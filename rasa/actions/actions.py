import os
from decimal import Decimal, InvalidOperation
import psycopg2
import psycopg2.extras
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from typing import Text, Any, Dict, List, Optional

DEFAULT_ACCOUNT_NUMBER = os.getenv("DEFAULT_ACCOUNT_NUMBER", "1234567890")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:admin@localhost:5432/asistente_bancario_db",
)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def money(value):
    amount = Decimal(value or 0).quantize(Decimal("0.01"))
    return f"${amount:,.2f} MXN"

def normalize_amount(value):
    if value is None:
        return None
    clean_val = str(value).replace('$', '').replace(',', '').strip()
    try:
        return Decimal(clean_val).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None

def normalize_text(value):
    return str(value).strip().lower() if value is not None else ""

def is_account_blocked(numero_cuenta):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT estado FROM cuentas WHERE numero_cuenta = %s", (numero_cuenta,))
                res = cursor.fetchone()
                return res and res["estado"] == "bloqueada"
    except Exception:
        return False

def get_current_account_number(tracker):
    metadata = (tracker.latest_message or {}).get("metadata") or {}
    account_number = metadata.get("account_number")
    return account_number or tracker.get_slot("numero_cuenta_sesion") or DEFAULT_ACCOUNT_NUMBER

def get_account(cursor, numero_cuenta):
    cursor.execute(
        """
        SELECT c.id AS cuenta_id, c.numero_cuenta, c.tipo, c.moneda, c.saldo, c.estado,
               cl.nombre AS cliente_nombre
        FROM cuentas c
        JOIN clientes cl ON cl.id = c.cliente_id
        WHERE c.numero_cuenta = %s
        """,
        (numero_cuenta,),
    )
    return cursor.fetchone()

class ActionSetTransferencia(Action):
    def name(self):
        return "action_set_transferencia"
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("tipo_operacion", "transferencia")]

class ActionSetPago(Action):
    def name(self):
        return "action_set_pago"
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("tipo_operacion", "pago")]

class ActionConsultarSaldo(Action):
    def name(self):
        return "action_consultar_saldo"
    def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        numero_cuenta = get_current_account_number(tracker)
        if is_account_blocked(numero_cuenta):
            dispatcher.utter_message(text="Lo siento, tu tarjeta y cuenta han sido bloqueadas por seguridad. No podrás realizar más operaciones hasta que acudas a una sucursal.")
            return [AllSlotsReset()]
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("SELECT c.nombre, a.saldo FROM clientes c JOIN cuentas a ON c.id = a.cliente_id WHERE a.numero_cuenta = %s", (numero_cuenta,))
                    cuenta = cursor.fetchone()
                    if not cuenta:
                        dispatcher.utter_message(text="No encontré tu cuenta vinculada.")
                        return []
                    nombre = cuenta["nombre"]
                    saldo = cuenta["saldo"]
            dispatcher.utter_message(text=f"{nombre}, el saldo disponible de tu cuenta es {money(saldo)}.")
            return [SlotSet("monto", None), SlotSet("numero_cuenta", None), SlotSet("nombre_destinatario", None), SlotSet("servicio", None)]
        except Exception as e:
            dispatcher.utter_message(text="Lo siento, tuve un problema al consultar tu saldo actual.")
            return []

class ActionConsultarMovimientos(Action):
    def name(self):
        return "action_consultar_movimientos"
    def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        numero_cuenta = get_current_account_number(tracker)
        if is_account_blocked(numero_cuenta):
            dispatcher.utter_message(text="Lo siento, tu tarjeta y cuenta han sido bloqueadas por seguridad. No podrás realizar más operaciones hasta que acudas a una sucursal.")
            return [AllSlotsReset()]
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cuenta = get_account(cursor, numero_cuenta)
                    if not cuenta:
                        dispatcher.utter_message(text=f"No encontré la cuenta {numero_cuenta}.")
                        return []
                    cursor.execute(
                        "SELECT tipo, descripcion, monto, fecha FROM movimientos WHERE cuenta_id = %s ORDER BY fecha DESC LIMIT 5",
                        (cuenta["cuenta_id"],),
                    )
                    movimientos = cursor.fetchall()
            if not movimientos:
                dispatcher.utter_message(text="No tienes movimientos registrados.")
                return []
            res = f"Últimos movimientos de la cuenta {numero_cuenta}:\n"
            for m in movimientos:
                res += f"- {m['fecha'].strftime('%d/%m/%Y')}: {m['descripcion']} ({money(m['monto'])})\n"
            dispatcher.utter_message(text=res)
            return []
        except Exception as exc:
            dispatcher.utter_message(text="Error al consultar movimientos.")
            return []

class ActionEjecutarTransferencia(Action):
    def name(self):
        return "action_ejecutar_transferencia"
    def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        cuenta_origen = get_current_account_number(tracker)
        if is_account_blocked(cuenta_origen):
            dispatcher.utter_message(text="Lo siento, tu tarjeta y cuenta han sido bloqueadas por seguridad. No podrás realizar más operaciones hasta que acudas a una sucursal.")
            return [AllSlotsReset()]
            
        cuenta_destino = tracker.get_slot("numero_cuenta")
        nombre_destinatario = tracker.get_slot("nombre_destinatario") or "destinatario"
        monto = normalize_amount(tracker.get_slot("monto"))

        if not cuenta_destino or not monto or monto <= 0:
            dispatcher.utter_message(text="Datos incompletos para la transferencia.")
            return []
        
        if len(str(cuenta_destino)) < 8:
            dispatcher.utter_message(text=f"El número de cuenta '{cuenta_destino}' parece inválido. Por favor proporciónalo de nuevo.")
            return [SlotSet("numero_cuenta", None)]

        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("SELECT * FROM cuentas WHERE numero_cuenta = %s FOR UPDATE", (cuenta_origen,))
                    origen = cursor.fetchone()
                    if not origen or Decimal(origen["saldo"]) < monto:
                        dispatcher.utter_message(text="Saldo insuficiente o cuenta no encontrada.")
                        return []
                    
                    nuevo_saldo = Decimal(origen["saldo"]) - monto
                    cursor.execute("UPDATE cuentas SET saldo = %s WHERE id = %s", (nuevo_saldo, origen["id"]))
                    cursor.execute(
                        "INSERT INTO movimientos (cuenta_id, tipo, descripcion, monto, saldo_resultante) VALUES (%s, 'transferencia', %s, %s, %s)",
                        (origen["id"], f"Transferencia a {nombre_destinatario} ({cuenta_destino})", -monto, nuevo_saldo),
                    )
                    conn.commit()
            dispatcher.utter_message(text=f"Transferencia de {money(monto)} a {nombre_destinatario} exitosa. Nuevo saldo: {money(nuevo_saldo)}.")
            return [SlotSet("monto", None), SlotSet("numero_cuenta", None), SlotSet("nombre_destinatario", None)]
        except Exception as exc:
            dispatcher.utter_message(text="Error al procesar la transferencia.")
            return []

class ActionEjecutarPago(Action):
    def name(self):
        return "action_ejecutar_pago"
    def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        cuenta_origen = get_current_account_number(tracker)
        if is_account_blocked(cuenta_origen):
            dispatcher.utter_message(text="Lo siento, tu tarjeta y cuenta han sido bloqueadas por seguridad. No podrás realizar más operaciones hasta que acudas a una sucursal.")
            return [AllSlotsReset()]
            
        servicio = normalize_text(tracker.get_slot("servicio"))
        monto = normalize_amount(tracker.get_slot("monto"))
        referencia = tracker.get_slot("numero_cuenta")

        if not servicio or not monto or monto <= 0:
            dispatcher.utter_message(text="Datos de pago incompletos.")
            return []

        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("SELECT * FROM cuentas WHERE numero_cuenta = %s FOR UPDATE", (cuenta_origen,))
                    origen = cursor.fetchone()
                    if not origen or Decimal(origen["saldo"]) < monto:
                        dispatcher.utter_message(text="Saldo insuficiente para el pago.")
                        return []
                    
                    nuevo_saldo = Decimal(origen["saldo"]) - monto
                    cursor.execute("UPDATE cuentas SET saldo = %s WHERE id = %s", (nuevo_saldo, origen["id"]))
                    cursor.execute(
                        "INSERT INTO movimientos (cuenta_id, tipo, descripcion, monto, saldo_resultante) VALUES (%s, 'pago', %s, %s, %s)",
                        (origen["id"], f"Pago de servicio: {servicio} (Ref: {referencia})", -monto, nuevo_saldo),
                    )
                    conn.commit()
            dispatcher.utter_message(text=f"Pago de {servicio} por {money(monto)} realizado. Nuevo saldo: {money(nuevo_saldo)}.")
            return [SlotSet("monto", None), SlotSet("numero_cuenta", None), SlotSet("servicio", None)]
        except Exception as exc:
            dispatcher.utter_message(text="Error al procesar el pago.")
            return []

class ActionBloquearTarjeta(Action):
    def name(self):
        return "action_bloquear_tarjeta"
    def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        numero_cuenta = get_current_account_number(tracker)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE cuentas SET estado = 'bloqueada' WHERE numero_cuenta = %s", (numero_cuenta,))
                    conn.commit()
            dispatcher.utter_message(text="Tu tarjeta y cuenta han sido bloqueadas por seguridad. No podrás realizar más operaciones hasta que acudas a una sucursal.")
            return [AllSlotsReset()]
        except Exception as e:
            dispatcher.utter_message(text="Hubo un error al intentar bloquear tu cuenta.")
            return []

class ValidateTransferenciaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_transferencia_form"

    def validate_monto(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        if is_account_blocked(get_current_account_number(tracker)) or tracker.latest_message.get("intent", {}).get("name") == "bloqueo_tarjeta":
            dispatcher.utter_message(text="Lo siento, tu tarjeta y cuenta han sido bloqueadas por seguridad. No podrás realizar más operaciones hasta que acudas a una sucursal.")
            return {"monto": None, "requested_slot": None}
        monto = normalize_amount(slot_value)
        if monto is None or monto <= 0:
            dispatcher.utter_message(text="Por favor ingresa un monto válido (ej. 500).")
            return {"monto": None}
        return {"monto": float(monto)}

    def validate_numero_cuenta(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        if is_account_blocked(get_current_account_number(tracker)) or tracker.latest_message.get("intent", {}).get("name") == "bloqueo_tarjeta":
            dispatcher.utter_message(text="Lo siento, tu tarjeta y cuenta han sido bloqueadas por seguridad. No podrás realizar más operaciones hasta que acudas a una sucursal.")
            return {"numero_cuenta": None, "requested_slot": None}
        cuenta = str(slot_value).strip()
        if len(cuenta) < 8:
            dispatcher.utter_message(text="El número de cuenta debe tener al menos 8 dígitos.")
            return {"numero_cuenta": None}
        return {"numero_cuenta": cuenta}

class ValidatePagoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_pago_form"

    def validate_servicio(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        if is_account_blocked(get_current_account_number(tracker)) or tracker.latest_message.get("intent", {}).get("name") == "bloqueo_tarjeta":
            dispatcher.utter_message(text="Lo siento, tu tarjeta y cuenta han sido bloqueadas por seguridad. No podrás realizar más operaciones hasta que acudas a una sucursal.")
            return {"servicio": None, "requested_slot": None}
        
        servicio_raw = str(slot_value).lower().strip()
        if any(kw in servicio_raw for kw in ["agua", "h2o", "sapal", "sacmex"]):
            return {"servicio": "agua"}
        if any(kw in servicio_raw for kw in ["luz", "electricidad", "cfe", "energia", "fuerza"]):
            return {"servicio": "luz"}
        if any(kw in servicio_raw for kw in ["internet", "wifi", "red", "net", "web", "telmex", "izzi", "totalplay"]):
            return {"servicio": "internet"}
            
        dispatcher.utter_message(text="Por ahora solo puedo procesar pagos de: luz, agua o internet. ¿Cuál deseas pagar?")
        return {"servicio": None}

    def validate_monto(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        if is_account_blocked(get_current_account_number(tracker)) or tracker.latest_message.get("intent", {}).get("name") == "bloqueo_tarjeta":
            dispatcher.utter_message(text="Lo siento, tu tarjeta y cuenta han sido bloqueadas por seguridad. No podrás realizar más operaciones hasta que acudas a una sucursal.")
            return {"monto": None, "requested_slot": None}
        monto = normalize_amount(slot_value)
        if monto is None or monto <= 0:
            dispatcher.utter_message(text="El monto ingresado no es válido.")
            return {"monto": None}
        return {"monto": float(monto)}

    def validate_numero_cuenta(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        if is_account_blocked(get_current_account_number(tracker)) or tracker.latest_message.get("intent", {}).get("name") == "bloqueo_tarjeta":
            dispatcher.utter_message(text="Lo siento, tu tarjeta y cuenta han sido bloqueadas por seguridad. No podrás realizar más operaciones hasta que acudas a una sucursal.")
            return {"numero_cuenta": None, "requested_slot": None}
        referencia = str(slot_value).strip()
        if len(referencia) < 5:
            dispatcher.utter_message(text="La referencia es demasiado corta.")
            return {"numero_cuenta": None}
        return {"numero_cuenta": referencia}
