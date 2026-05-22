# 🏦 Asistente Bancario Virtual con Rasa NLU

Un asistente virtual bancario inteligente construido con **Rasa NLU**, **FastAPI** y **React**, que proporciona respuestas naturales y amigables para consultas bancarias.

## 📋 Características

✅ **Inteligencia Artificial Real** - Powered by Rasa NLU
✅ **Respuestas Amigables** - Conversaciones naturales y empáticas
✅ **Operaciones Bancarias** - Consultas de saldo, transferencias, pagos
✅ **Historial Persistente** - Base de datos PostgreSQL
✅ **Caché Rápido** - Redis para sesiones y contexto
✅ **API RESTful** - FastAPI con documentación automática
✅ **Frontend Moderno** - React con diseño bancario profesional
✅ **Containerizado** - Docker Compose para fácil despliegue

## 🚀 Inicio Rápido

### Requisitos Previos

- Docker y Docker Compose instalados
- Python 3.11+ (para desarrollo local)
- Node.js 18+ (para desarrollo del frontend)

### Opción 1: Con Docker (Recomendado)

```bash
# 1. Clonar o descargar el proyecto
cd asistente-bancario

# 2. Iniciar todos los servicios
docker compose -f docker-compose-complete.yml up -d

# 3. Entrenar el modelo de Rasa (primera vez)
docker compose -f docker-compose-complete.yml run --rm rasa train

# 4. Acceder a la aplicación
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Rasa: http://localhost:5005
```

### Opción 2: Desarrollo Local

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Rasa (en otra terminal)
cd rasa
rasa train
rasa run --enable-api --cors "*"

# Frontend (en otra terminal)
cd frontend
npm install
npm run dev
```

## 📁 Estructura del Proyecto

```
asistente-bancario/
├── backend/                    # API FastAPI
│   ├── main.py                # Aplicación principal
│   ├── requirements.txt        # Dependencias Python
│   └── Dockerfile             # Imagen Docker
├── rasa/                       # Configuración de Rasa NLU
│   ├── config.yml             # Configuración del modelo
│   ├── domain.yml             # Intenciones y respuestas
│   ├── data/
│   │   ├── nlu.yml           # Ejemplos de entrenamiento
│   │   └── stories.yml       # Historias de conversación
│   ├── credentials.yml        # Credenciales de conectores
│   └── endpoints.yml          # Endpoints de servicios
├── frontend/                   # Aplicación React
│   ├── src/
│   │   ├── pages/            # Páginas (Login, Dashboard)
│   │   ├── components/       # Componentes (ChatWidget)
│   │   └── App.tsx           # Componente principal
│   └── package.json          # Dependencias Node
├── docker-compose.yml         # Orquestación de servicios
└── README.md                  # Este archivo
```

## 🤖 Intenciones Soportadas

El asistente puede entender y responder a:

- **Saludos** - "Hola", "¿Qué tal?"
- **Despedidas** - "Adiós", "Hasta luego"
- **Consultar Saldo** - "¿Cuál es mi saldo?"
- **Transferencias** - "Transferir $100 a Juan"
- **Pago de Servicios** - "Pagar la luz"
- **Historial** - "Mostrar mis transacciones"
- **Solicitar Tarjeta** - "Quiero una tarjeta de crédito"
- **Inversiones** - "Quiero invertir dinero"
- **Ayuda** - "¿Cómo funciona?"
- **Soporte** - "Hablar con un agente"
- **Seguridad** - "¿Es seguro?"

## 🔧 Configuración

### Variables de Entorno

Crear archivo `.env` en la raíz:

```env
DATABASE_URL=postgresql://admin:admin@localhost:5432/asistente_bancario_db
REDIS_URL=redis://localhost:6379
RASA_URL=http://localhost:5005
```

### Entrenar Modelo de Rasa

```bash
# Entrenar modelo
docker compose -f docker-compose-complete.yml run --rm rasa train

# O localmente
cd rasa
rasa train
```

## 📊 API Endpoints

### Chat
```bash
POST /chat
Content-Type: application/json

{
  "text": "¿Cuál es mi saldo?",
  "user_id": "usuario123"
}

Response:
{
  "reply": "Tu saldo disponible es de $15,234.50",
  "intent": "consultar_saldo",
  "confidence": 0.95,
  "entities": {}
}
```

### Historial
```bash
GET /history/{session_id}

Response:
{
  "session_id": "abc123",
  "messages": [
    {
      "sender": "user",
      "text": "¿Cuál es mi saldo?",
      "intent": "consultar_saldo",
      "timestamp": "2024-04-15T10:30:00"
    },
    {
      "sender": "assistant",
      "text": "Tu saldo disponible es de $15,234.50",
      "intent": null,
      "timestamp": "2024-04-15T10:30:01"
    }
  ]
}
```

### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "redis": "connected",
  "database": "connected"
}
```

## 🎨 Personalización

### Agregar Nuevas Intenciones

1. **Actualizar `rasa/data/nlu.yml`**:
```yaml
- intent: mi_nueva_intencion
  examples: |
    - ejemplo 1
    - ejemplo 2
    - ejemplo 3
```

2. **Actualizar `rasa/domain.yml`**:
```yaml
intents:
  - mi_nueva_intencion

responses:
  utter_mi_nueva_intencion:
  - text: "Respuesta amigable aquí"
```

3. **Entrenar modelo**:
```bash
docker compose -f docker-compose-complete.yml run --rm rasa train
```

### Cambiar Respuestas

Editar `rasa/domain.yml` en la sección `responses`:

```yaml
responses:
  utter_saludo:
  - text: "Tu respuesta personalizada aquí"
```

## 🐳 Comandos Docker Útiles

```bash
# Ver logs
docker-compose logs -f backend
docker-compose logs -f rasa

# Entrenar modelo
docker compose -f docker-compose-complete.yml run --rm rasa train

# Acceder a la BD
docker exec -it postgres_db psql -U admin -d asistente_bancario_db

# Detener servicios
docker-compose down

# Limpiar todo
docker-compose down -v
```

## 📈 Monitoreo

- **Rasa Swagger**: http://localhost:5005/
- **FastAPI Docs**: http://localhost:8000/docs
- **FastAPI ReDoc**: http://localhost:8000/redoc

## 🔐 Seguridad

- ✅ Encriptación de datos en tránsito
- ✅ Validación de entrada con Pydantic
- ✅ CORS configurado
- ✅ Sesiones con Redis
- ✅ Base de datos segura

## 🚀 Deployment

### A Producción

1. **Configurar variables de entorno**
2. **Usar HTTPS**
3. **Configurar CORS específico**
4. **Usar contraseñas seguras**
5. **Habilitar autenticación**

```bash
# Build para producción
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📞 Soporte

Para reportar problemas o sugerencias, contacta al equipo de desarrollo.

## 📄 Licencia

Proyecto privado - Todos los derechos reservados

---

**Última actualización**: Abril 2024
**Versión**: 2.0.0
**Estado**: ✅ Producción
