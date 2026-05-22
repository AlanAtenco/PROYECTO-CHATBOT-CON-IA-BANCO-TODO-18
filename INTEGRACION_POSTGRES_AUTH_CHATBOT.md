# Integración de PostgreSQL con autenticación y chatbot

Este documento resume los cambios aplicados al proyecto para que el **login**, el **registro** y el **chatbot bancario** trabajen con una base de datos PostgreSQL real. La integración evita el registro simulado en el navegador y vincula cada conversación del asistente con el usuario autenticado y su cuenta bancaria.

## Cambios principales

| Área | Cambio realizado | Archivo principal |
|---|---|---|
| Base de datos | Se añadieron tablas de `usuarios`, `auth_sessions`, `conversations` y `messages`, vinculadas con `clientes` y `cuentas`. | `database/init/01_banking_schema.sql` |
| Backend | Se implementaron endpoints reales de registro, login, sesión actual, logout, chat e historial protegido. | `backend/main.py` |
| Frontend | Se sustituyó la autenticación simulada por llamadas reales a FastAPI y almacenamiento local del token. | `frontend/src/App.tsx`, `frontend/src/pages/Login.tsx` |
| Chatbot | El widget envía token, usuario y `sender_id`; FastAPI transmite `metadata` a Rasa con la cuenta activa. | `frontend/src/components/ChatWidget.tsx`, `backend/main.py` |
| Rasa Actions | Las acciones consultan la cuenta enviada por la sesión autenticada en vez de usar siempre una cuenta fija. | `rasa/actions/actions.py` |
| Optimización | Se centralizó la configuración de API, tipos de usuario y helpers de autenticación. | `frontend/src/api.ts` |

## Endpoints nuevos o actualizados

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/auth/register` | Crea cliente, usuario, cuenta bancaria inicial, sesión y saldo inicial. |
| `POST` | `/auth/login` | Valida credenciales con hash PBKDF2 y crea una sesión en PostgreSQL. |
| `GET` | `/auth/me` | Devuelve el usuario autenticado usando `Authorization: Bearer <token>`. |
| `POST` | `/auth/logout` | Revoca la sesión actual. |
| `POST` | `/chat` | Procesa mensajes solo con sesión válida y vincula conversación a usuario/cuenta. |
| `GET` | `/history/{session_id}` | Devuelve historial únicamente del usuario autenticado. |

## Flujo de autenticación

El registro crea un cliente y una cuenta de ahorro con saldo inicial de prueba. La contraseña se almacena como hash `pbkdf2_sha256` con salt aleatorio; el frontend nunca guarda la contraseña, solo conserva el token de sesión devuelto por el backend.

> La sesión se guarda en PostgreSQL dentro de `auth_sessions`, tiene fecha de expiración y puede revocarse mediante `/auth/logout`.

## Flujo del chatbot

El frontend envía cada mensaje con el token de sesión. FastAPI valida el token, obtiene el usuario, identifica la cuenta bancaria activa y llama a Rasa con esta metadata:

```json
{
  "sender": "web:<user_id>",
  "message": "¿Cuál es mi saldo?",
  "metadata": {
    "user_id": "<uuid>",
    "account_number": "<numero_cuenta>"
  }
}
```

Las acciones personalizadas de Rasa leen `account_number` desde `tracker.latest_message.metadata`, por lo que consultas de saldo, movimientos, transferencias, pagos y bloqueo operan sobre la cuenta del usuario autenticado.

## Ejecución paso a paso (Comandos finales)

Sigue este orden exacto para asegurar que el sistema inicie correctamente:

### Paso 1: Limpieza total (Recomendado)
```bash
docker compose -f docker-compose-complete.yml down -v
```
> **¿Por qué?**: Borra volúmenes antiguos para que PostgreSQL cree las nuevas tablas de usuarios y chatbot correctamente.

### Paso 2: Construir las imágenes
```bash
docker compose -f docker-compose-complete.yml build
```
> **¿Por qué?**: Empaqueta el código actualizado del backend y las acciones de Rasa.

### Paso 3: Entrenar el cerebro del asistente (Rasa)
```bash
docker compose -f docker-compose-complete.yml run --rm rasa train
```
> **¿Por qué?**: Genera el modelo de IA. He extendido masivamente el entrenamiento para que responda a casi cualquier variación de saldo, pagos, transferencias y bloqueos.

### Paso 4: Levantar todo el sistema
```bash
docker compose -f docker-compose-complete.yml up -d
```
> **¿Por qué?**: Inicia los contenedores en segundo plano. Ahora el backend no se bloqueará si Rasa tarda en cargar.

### Paso 5: Verificar que todo esté arriba
```bash
docker compose -f docker-compose-complete.yml ps
```
> **¿Por qué?**: Confirma que los 6 servicios estén en estado `running`.

### Paso 6: Ver logs del backend (Opcional)
```bash
docker compose -f docker-compose-complete.yml logs -f backend
```
> **¿Por qué?**: Útil para ver errores de conexión o depurar el flujo de login/chat.

## Validación realizada

Se validó la sintaxis del backend y de las acciones de Rasa con `python3.11 -m py_compile`. También se compiló el frontend con `npm run build` y el build terminó correctamente.

```bash
python3.11 -m py_compile backend/main.py rasa/actions/actions.py
cd frontend && npm run build
```

## Nota de base de datos existente

Si ya existe un volumen de PostgreSQL creado antes de estos cambios, los scripts de `database/init` no se ejecutarán automáticamente de nuevo porque Docker solo los aplica al inicializar el volumen. En ese caso hay dos opciones:

| Opción | Uso recomendado |
|---|---|
| Reiniciar volumen | Desarrollo local sin datos importantes: `docker compose down -v && docker compose -f docker-compose-complete.yml up -d`. |
| Migrar manualmente | Mantener datos existentes: ejecutar las sentencias nuevas de `database/init/01_banking_schema.sql` en la base actual. |
