from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import redis
import psycopg2
from datetime import datetime
import json
import uuid

# =====================================
# CONFIGURACIÓN DE LA API
# =====================================

app = FastAPI(
    title="API del Asistente Virtual Bancario",
    description="Backend para el chatbot bancario",
    version="1.0.0"
)

# =====================================
# CONFIGURACIÓN CORS (FRONTEND)
# =====================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================
# CONEXIÓN A REDIS (CACHE)
# =====================================

try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("Conexión exitosa a Redis")
except:
    print("No se pudo conectar a Redis")
    redis_client = None


# =====================================
# CONEXIÓN A POSTGRESQL
# =====================================

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="asistente_bancario_db",
            user="admin",
            password="admin"
        )
        return conn
    except Exception as e:
        print("Error PostgreSQL:", e)
        return None


# =====================================
# MODELOS DE DATOS
# =====================================

class Message(BaseModel):
    text: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    entities: Optional[dict] = None


class ConversationHistory(BaseModel):
    session_id: str
    messages: List[dict]


# =====================================
# CREACIÓN DE TABLAS AL INICIAR
# =====================================

@app.on_event("startup")
async def startup_event():

    conn = get_db_connection()

    if conn:

        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255),
            sender VARCHAR(50),
            text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        cursor.close()
        conn.close()

        print("Base de datos lista")


# =====================================
# ENDPOINT DE PRUEBA
# =====================================

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "API funcionando"
    }


# =====================================
# ENDPOINT PRINCIPAL DEL CHATBOT
# =====================================

@app.post("/chat", response_model=ChatResponse)
async def chat(message: Message):

    # Crear sesión
    session_id = message.user_id if message.user_id else str(uuid.uuid4())

    # ===============================
    # PROCESAMIENTO NLP
    # ===============================

    nlp_result = process_nlp(message.text)

    # ===============================
    # GENERAR RESPUESTA
    # ===============================

    reply = generate_response(nlp_result)

    # ===============================
    # GUARDAR MENSAJE EN BD
    # ===============================

    save_message(session_id, "user", message.text)
    save_message(session_id, "assistant", reply)

    return ChatResponse(
        reply=reply,
        intent=nlp_result["intent"],
        confidence=nlp_result["confidence"],
        entities={}
    )


# =====================================
# HISTORIAL DE CONVERSACIÓN
# =====================================

@app.get("/history/{session_id}", response_model=ConversationHistory)
async def get_history(session_id: str):

    conn = get_db_connection()

    if not conn:
        raise HTTPException(status_code=500, detail="Error base de datos")

    cursor = conn.cursor()

    cursor.execute("""
    SELECT sender, text, timestamp
    FROM messages
    WHERE session_id = %s
    ORDER BY timestamp
    """, (session_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    messages = []

    for row in rows:
        messages.append({
            "sender": row[0],
            "text": row[1],
            "timestamp": row[2].isoformat()
        })

    return ConversationHistory(session_id=session_id, messages=messages)


# =====================================
# NLP DEL CHATBOT
# =====================================

def process_nlp(text: str) -> dict:

    text_lower = text.lower()

    saludos = [
        "hola",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "hey"
    ]

    for palabra in saludos:
        if palabra in text_lower:
            return {
                "intent": "saludo",
                "confidence": 0.95
            }

    return {
        "intent": "unknown",
        "confidence": 0.5
    }


# =====================================
# GENERADOR DE RESPUESTA
# =====================================

def generate_response(nlp_result: dict):

    intent = nlp_result["intent"]

    if intent == "saludo":
        return "¡Hola! Soy tu asistente virtual bancario."

    return "Error: Esta versión del chatbot solo responde saludos."


# =====================================
# GUARDAR MENSAJES
# =====================================

def save_message(session_id: str, sender: str, text: str):

    conn = get_db_connection()

    if not conn:
        return

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO conversations (session_id)
    VALUES (%s)
    ON CONFLICT (session_id) DO NOTHING
    """, (session_id,))

    cursor.execute("""
    INSERT INTO messages (session_id, sender, text)
    VALUES (%s, %s, %s)
    """, (session_id, sender, text))

    conn.commit()

    cursor.close()
    conn.close()


# =====================================
# EJECUTAR SERVIDOR
# =====================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )