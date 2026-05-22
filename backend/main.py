from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import hmac
import json
import os
import random
import re
import secrets
import uuid
from typing import List, Optional

import httpx
import psycopg2
import psycopg2.extras
import redis
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:admin@localhost:5432/asistente_bancario_db",
)
SESSION_TTL_DAYS = int(os.getenv("SESSION_TTL_DAYS", "7"))
PASSWORD_ITERATIONS = int(os.getenv("PASSWORD_ITERATIONS", "120000"))
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = FastAPI(
    title="API del Asistente Virtual Bancario",
    description="Backend para autenticación, persistencia bancaria y procesamiento de consultas con Rasa NLU",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    print("✅ Conexión exitosa a Redis")
except Exception as exc:
    print(f"⚠️ No se pudo conectar a Redis: {exc}")
    redis_client = None


class Message(BaseModel):
    text: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    sender_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    entities: Optional[dict] = None
    session_id: Optional[str] = None


class ConversationHistory(BaseModel):
    session_id: str
    messages: List[dict]


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    accountNumber: Optional[str] = None


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    accountNumber: Optional[str] = None
    balance: Optional[float] = None


class AuthResponse(BaseModel):
    token: str
    user: UserOut


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email(email: str) -> None:
    if not EMAIL_REGEX.match(email):
        raise HTTPException(status_code=422, detail="El correo electrónico no tiene un formato válido")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate, digest)
    except Exception:
        return False


def create_session(cursor, user_id: str) -> str:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(days=SESSION_TTL_DAYS)
    cursor.execute(
        """
        INSERT INTO auth_sessions (token, user_id, expires_at)
        VALUES (%s, %s, %s)
        """,
        (token, user_id, expires_at),
    )
    return token


def auth_token_from_header(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def fetch_user_by_token(token: str) -> Optional[dict]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT u.id, u.nombre, u.email, u.estado,
                       c.numero_cuenta, c.saldo
                FROM auth_sessions s
                JOIN usuarios u ON u.id = s.user_id
                LEFT JOIN cuentas c ON c.cliente_id = u.cliente_id AND c.estado IN ('activa', 'bloqueada')
                WHERE s.token = %s
                  AND s.revoked_at IS NULL
                  AND s.expires_at > CURRENT_TIMESTAMP
                ORDER BY c.created_at ASC
                LIMIT 1
                """,
                (token,),
            )
            return cursor.fetchone()


def fetch_user_by_id(user_id: str) -> Optional[dict]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT u.id, u.nombre, u.email, u.estado,
                       c.numero_cuenta, c.saldo
                FROM usuarios u
                LEFT JOIN cuentas c ON c.cliente_id = u.cliente_id AND c.estado IN ('activa', 'bloqueada')
                WHERE u.id = %s
                ORDER BY c.created_at ASC
                LIMIT 1
                """,
                (user_id,),
            )
            return cursor.fetchone()


def to_user_out(row: dict) -> UserOut:
    return UserOut(
        id=row["id"],
        name=row["nombre"],
        email=row["email"],
        accountNumber=row.get("numero_cuenta"),
        balance=float(row["saldo"]) if row.get("saldo") is not None else None,
    )


def generate_account_number(cursor) -> str:
    for _ in range(10):
        number = str(random.randint(10**9, 10**10 - 1))
        cursor.execute("SELECT 1 FROM cuentas WHERE numero_cuenta = %s", (number,))
        if cursor.fetchone() is None:
            return number
    raise HTTPException(status_code=500, detail="No se pudo generar una cuenta única")


def initialize_database():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(150) NOT NULL,
                    documento VARCHAR(50) UNIQUE NOT NULL,
                    telefono VARCHAR(30),
                    email VARCHAR(150),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cuentas (
                    id SERIAL PRIMARY KEY,
                    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
                    numero_cuenta VARCHAR(20) UNIQUE NOT NULL,
                    tipo VARCHAR(50) NOT NULL DEFAULT 'ahorro',
                    moneda VARCHAR(10) NOT NULL DEFAULT 'MXN',
                    saldo NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
                    estado VARCHAR(30) NOT NULL DEFAULT 'activa',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id VARCHAR(36) PRIMARY KEY,
                    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
                    nombre VARCHAR(150) NOT NULL,
                    email VARCHAR(150) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    estado VARCHAR(30) NOT NULL DEFAULT 'activo',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios (LOWER(email))")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_cliente_id ON usuarios (cliente_id)")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS movimientos (
                    id SERIAL PRIMARY KEY,
                    cuenta_id INTEGER NOT NULL REFERENCES cuentas(id),
                    tipo VARCHAR(40) NOT NULL,
                    descripcion TEXT NOT NULL,
                    monto NUMERIC(14, 2) NOT NULL,
                    saldo_resultante NUMERIC(14, 2) NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_movimientos_cuenta_id ON movimientos (cuenta_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos (fecha DESC)")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tarjetas (
                    id SERIAL PRIMARY KEY,
                    cuenta_id INTEGER NOT NULL REFERENCES cuentas(id),
                    numero_tarjeta VARCHAR(20) UNIQUE NOT NULL,
                    tipo VARCHAR(30) NOT NULL DEFAULT 'debito',
                    estado VARCHAR(30) NOT NULL DEFAULT 'activa',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tarjetas_cuenta_id ON tarjetas (cuenta_id)")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS servicios (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(80) UNIQUE NOT NULL,
                    referencia VARCHAR(80),
                    estado VARCHAR(30) NOT NULL DEFAULT 'activo'
                )
                """
            )
            cursor.execute(
                "INSERT INTO servicios (nombre, referencia) VALUES ('luz', 'CFE-001'), ('agua', 'AGUA-001'), ('internet', 'TELCO-001') ON CONFLICT DO NOTHING"
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    token VARCHAR(128) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    revoked_at TIMESTAMP
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at ON auth_sessions (expires_at)")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id VARCHAR(36) REFERENCES usuarios(id) ON DELETE SET NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(36) REFERENCES usuarios(id) ON DELETE SET NULL,
                    sender VARCHAR(50) NOT NULL,
                    text TEXT NOT NULL,
                    intent VARCHAR(100),
                    confidence FLOAT,
                    entities JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)")
            cursor.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages (user_id)")
            conn.commit()


@app.on_event("startup")
async def startup_event():
    try:
        initialize_database()
        print("✅ Base de datos inicializada")
    except Exception as exc:
        print(f"⚠️ No se pudo inicializar la base de datos: {exc}")


@app.get("/")
def read_root():
    return {
        "status": "online",
        "version": "3.0.0",
        "description": "Asistente Bancario Virtual con autenticación PostgreSQL y Rasa NLU",
    }


@app.get("/health")
def health_check():
    database_status = "disconnected"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                database_status = "connected"
    except Exception:
        database_status = "disconnected"

    return {
        "status": "healthy" if database_status == "connected" else "degraded",
        "redis": "connected" if redis_client else "disconnected",
        "database": database_status,
    }


@app.post("/auth/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    name = payload.name.strip()
    email = normalize_email(payload.email)
    validate_email(email)
    user_id = str(uuid.uuid4())
    documento = secrets.token_hex(4).upper()

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # 1. Verificar si el email ya existe
            cursor.execute("SELECT id FROM usuarios WHERE LOWER(email) = %s", (email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Este correo electrónico ya está registrado")

            # 2. Manejar el número de cuenta
            if payload.accountNumber and payload.accountNumber.strip():
                account_number = payload.accountNumber.strip()
                cursor.execute("SELECT id FROM cuentas WHERE numero_cuenta = %s", (account_number,))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Este número de cuenta ya está en uso")
            else:
                account_number = generate_account_number(cursor)

            cursor.execute(
                """
                INSERT INTO clientes (nombre, documento, email)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (name, documento, email),
            )
            cliente_id = cursor.fetchone()["id"]
            initial_balance = Decimal("15000.00")
            cursor.execute(
                """
                INSERT INTO cuentas (cliente_id, numero_cuenta, tipo, moneda, saldo, estado)
                VALUES (%s, %s, 'ahorro', 'MXN', %s, 'activa')
                RETURNING id
                """,
                (cliente_id, account_number, initial_balance),
            )
            cuenta_id = cursor.fetchone()["id"]
            cursor.execute(
                """
                INSERT INTO movimientos (cuenta_id, tipo, descripcion, monto, saldo_resultante)
                VALUES (%s, 'deposito', 'Depósito inicial por apertura de cuenta', %s, %s)
                """,
                (cuenta_id, initial_balance, initial_balance),
            )
            cursor.execute(
                """
                INSERT INTO usuarios (id, cliente_id, nombre, email, password_hash)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, cliente_id, name, email, hash_password(payload.password)),
            )
            token = create_session(cursor, user_id)
            conn.commit()

    return AuthResponse(
        token=token,
        user=UserOut(
            id=user_id,
            name=name,
            email=email,
            accountNumber=account_number,
            balance=float(initial_balance),
        ),
    )


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    email = normalize_email(payload.email)
    validate_email(email)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT u.id, u.nombre, u.email, u.password_hash, u.estado,
                       c.numero_cuenta, c.saldo
                FROM usuarios u
                LEFT JOIN cuentas c ON c.cliente_id = u.cliente_id AND c.estado IN ('activa', 'bloqueada')
                WHERE LOWER(u.email) = %s
                ORDER BY c.created_at ASC
                LIMIT 1
                """,
                (email,),
            )
            user = cursor.fetchone()
            if not user or not verify_password(payload.password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
            if user["estado"] != "activo":
                raise HTTPException(status_code=403, detail="El usuario no está activo")
            token = create_session(cursor, user["id"])
            conn.commit()

    return AuthResponse(token=token, user=to_user_out(user))


@app.get("/auth/me", response_model=UserOut)
def me(authorization: Optional[str] = Header(default=None)):
    token = auth_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    user = fetch_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    return to_user_out(user)


@app.post("/auth/logout")
def logout(authorization: Optional[str] = Header(default=None)):
    token = auth_token_from_header(authorization)
    if token:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE auth_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE token = %s",
                    (token,),
                )
                conn.commit()
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(message: Message, authorization: Optional[str] = Header(default=None)):
    token = auth_token_from_header(authorization)
    user = fetch_user_by_token(token) if token else None
    if not user and message.user_id:
        user = fetch_user_by_id(message.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión para usar el asistente")

    session_id = message.sender_id or f"user:{user['id']}"
    account_number = user.get("numero_cuenta")

    try:
        rasa_response = await get_rasa_response(
            message.text,
            session_id,
            user_id=user["id"],
            account_number=account_number,
        )

        if rasa_response:
            reply = rasa_response.get("text") or "Disculpa, no entendí tu mensaje. ¿Puedes reformular?"
            intent = rasa_response.get("intent", "unknown")
            confidence = rasa_response.get("confidence", 0.0)
            entities = rasa_response.get("entities", {})
        else:
            reply = "Lo siento, estoy teniendo dificultades para procesar tu solicitud. Intenta de nuevo."
            intent = "error"
            confidence = 0.0
            entities = {}

        save_message(session_id, user["id"], "user", message.text, {"intent": intent, "confidence": confidence, "entities": entities})
        save_message(session_id, user["id"], "assistant", reply, None)
        cache_session(session_id, user["id"], intent, message.text, account_number)

        return ChatResponse(
            reply=reply,
            intent=intent,
            confidence=confidence,
            entities=entities,
            session_id=session_id,
        )

    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ Error en chat: {exc}")
        return ChatResponse(
            reply="Lo siento, ocurrió un error. Por favor intenta de nuevo.",
            intent="error",
            confidence=0.0,
            entities={},
            session_id=session_id,
        )


async def get_rasa_response(user_message: str, sender_id: str, user_id: str, account_number: Optional[str]) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            rasa_base_url = os.getenv("RASA_URL", "http://localhost:5005")
            rasa_url = f"{rasa_base_url}/webhooks/rest/webhook"
            payload = {
                "sender": sender_id,
                "message": user_message,
                "metadata": {
                    "user_id": user_id,
                    "account_number": account_number
                }
            }
            response = await client.post(rasa_url, json=payload)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return data[0]
            return None
    except Exception as exc:
        print(f"⚠️ Error al conectar con Rasa: {exc}")
        return None


def save_message(session_id: str, user_id: str, sender: str, text: str, nlu_data: Optional[dict]):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO conversations (session_id, user_id) VALUES (%s, %s) ON CONFLICT (session_id) DO UPDATE SET user_id = EXCLUDED.user_id",
                    (session_id, user_id),
                )
                cursor.execute(
                    """
                    INSERT INTO messages (session_id, user_id, sender, text, intent, confidence, entities)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        session_id,
                        user_id,
                        sender,
                        text,
                        nlu_data.get("intent") if nlu_data else None,
                        nlu_data.get("confidence") if nlu_data else None,
                        json.dumps(nlu_data.get("entities")) if nlu_data and nlu_data.get("entities") else None,
                    ),
                )
                conn.commit()
    except Exception as exc:
        print(f"⚠️ Error al guardar mensaje: {exc}")


def cache_session(session_id: str, user_id: str, last_intent: str, last_message: str, account_number: str):
    if not redis_client:
        return
    try:
        cache_data = {
            "user_id": user_id,
            "last_intent": last_intent,
            "last_message": last_message,
            "account_number": account_number,
            "updated_at": datetime.utcnow().isoformat(),
        }
        redis_client.setex(f"session:{session_id}", 3600, json.dumps(cache_data))
    except Exception as exc:
        print(f"⚠️ Error en caché Redis: {exc}")


@app.get("/history/{session_id}", response_model=ConversationHistory)
def get_history(session_id: str):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                "SELECT sender, text, timestamp FROM messages WHERE session_id = %s ORDER BY timestamp ASC",
                (session_id,),
            )
            messages = cursor.fetchall()
            return ConversationHistory(session_id=session_id, messages=messages)
