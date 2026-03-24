# Asistente Virtual Cognitivo Bancario con NLP

Proyecto de residencias profesionales para Ingeniería en Sistemas Computacionales desarrollado para PluriOne S.A. de C.V.

## Descripción del Proyecto

Este proyecto implementa un asistente virtual inteligente para el sector bancario que utiliza procesamiento de lenguaje natural (NLP) para comprender y responder consultas de clientes en español. El sistema está diseñado con una arquitectura de microservicios que garantiza escalabilidad, seguridad y disponibilidad 24/7.

## Características Principales

- **Comprensión de lenguaje natural** en español utilizando modelos de IA
- **Reconocimiento de intenciones** para identificar qué desea hacer el usuario
- **Extracción de entidades** para capturar información relevante (montos, fechas, beneficiarios)
- **Gestión de diálogos** multi-turno con contexto conversacional
- **Interfaz web moderna** y responsive
- **Almacenamiento persistente** de conversaciones
- **Caché de sesiones** para respuestas rápidas
- **Arquitectura segura** con autenticación JWT

## Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno para Python
- **PostgreSQL**: Base de datos relacional
- **Redis**: Sistema de caché en memoria

### NLP e Inteligencia Artificial
- **Rasa Open Source**: Framework conversacional
- **spaCy**: Procesamiento de lenguaje natural
- **Hugging Face Transformers**: Modelos pre-entrenados

### Frontend
- **React**: Librería de interfaces de usuario
- **TypeScript**: JavaScript con tipado estático
- **Vite**: Herramienta de construcción rápida

### Infraestructura
- **Docker**: Contenedorización de servicios
- **Docker Compose**: Orquestación de contenedores

## Estructura del Proyecto

```
asistente-bancario/
├── backend/              # API REST con FastAPI
│   ├── main.py          # Código principal del backend
│   └── requirements.txt # Dependencias de Python
├── nlp/                 # Servicio de NLP con Rasa
│   ├── config.yml       # Configuración del pipeline
│   ├── domain.yml       # Definición de intenciones y respuestas
│   ├── data/
│   │   ├── nlu.yml      # Datos de entrenamiento
│   │   └── stories.yml  # Flujos conversacionales
│   └── README.md        # Instrucciones de NLP
├── frontend/            # Interfaz de usuario con React
│   ├── src/
│   │   ├── App.tsx      # Componente principal
│   │   ├── App.css      # Estilos
│   │   └── main.tsx     # Punto de entrada
│   ├── package.json     # Dependencias de Node.js
│   └── vite.config.ts   # Configuración de Vite
├── docker-compose.yml   # Configuración de servicios
└── README.md           # Este archivo
```

## Instalación y Configuración

### Prerrequisitos

- Python 3.11+
- Node.js 18+
- Docker y Docker Compose
- Git

### Paso 1: Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd asistente-bancario
```

### Paso 2: Iniciar Bases de Datos

```bash
docker-compose up -d
```

Esto iniciará PostgreSQL en el puerto 5432 y Redis en el puerto 6379.

### Paso 3: Configurar Backend

```bash
cd backend

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
python main.py
```

El backend estará disponible en `http://localhost:8000`.

### Paso 4: Configurar Servicio NLP

```bash
cd ../nlp

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install rasa spacy
python -m spacy download es_core_news_md

# Entrenar modelo
rasa train

# Iniciar servidor (opcional, el backend tiene NLP integrado)
rasa run --enable-api --cors "*"
```

### Paso 5: Configurar Frontend

```bash
cd ../frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

El frontend estará disponible en `http://localhost:5173`.

## Uso del Sistema

1. Abre tu navegador en `http://localhost:5173`
2. Escribe un mensaje en el cuadro de texto
3. El asistente procesará tu consulta y responderá automáticamente

### Ejemplos de Consultas

- "Hola, ¿cuál es mi saldo?"
- "Muéstrame mis últimos movimientos"
- "Quiero transferir $500 a Juan"
- "Necesito pagar mi recibo de luz"
- "¿Cuánto pagaría por un crédito de $10,000?"
- "Perdí mi tarjeta, necesito bloquearla"

## Intenciones Soportadas

El asistente puede reconocer las siguientes intenciones:

| Intención | Descripción |
|-----------|-------------|
| `saludo` | Saludar al asistente |
| `despedida` | Despedirse |
| `consulta_saldo` | Consultar saldo de cuenta |
| `consulta_movimientos` | Ver movimientos recientes |
| `transferencia` | Realizar transferencia |
| `pago_servicios` | Pagar servicios |
| `simulacion_credito` | Simular crédito |
| `bloqueo_tarjeta` | Bloquear tarjeta |
| `informacion_producto` | Información sobre productos |
| `ayuda` | Solicitar ayuda |

## Arquitectura del Sistema

El sistema sigue una arquitectura de microservicios con tres componentes principales:

1. **Frontend (React)**: Interfaz de usuario que captura mensajes y muestra respuestas
2. **Backend (FastAPI)**: API REST que orquesta la lógica de negocio y procesa NLP
3. **Bases de Datos**: PostgreSQL para persistencia y Redis para caché

```
┌─────────────┐
│   Frontend  │ (React + TypeScript)
│  Port 5173  │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│   Backend   │ (FastAPI)
│  Port 8000  │
└──────┬──────┘
       │
   ┌───┴───┐
   ▼       ▼
┌──────┐ ┌──────┐
│ PG   │ │Redis │
│ 5432 │ │ 6379 │
└──────┘ └──────┘
```

## Desarrollo y Pruebas

### Probar el Backend

```bash
# Verificar estado
curl http://localhost:8000/health

# Enviar mensaje
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola, ¿cuál es mi saldo?", "user_id": "test"}'
```

### Probar el Modelo NLP

```bash
cd nlp
rasa shell
```

### Construir para Producción

```bash
# Frontend
cd frontend
npm run build

# Backend (ya está listo para producción)
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Seguridad

El sistema implementa múltiples capas de seguridad:

- **CORS configurado** para prevenir accesos no autorizados
- **Validación de datos** con Pydantic
- **Preparado para JWT** para autenticación de usuarios
- **Logs de auditoría** en base de datos
- **Cifrado en tránsito** con HTTPS (en producción)

## Mantenimiento

### Agregar Nuevas Intenciones

1. Editar `nlp/domain.yml` para agregar la nueva intención
2. Agregar ejemplos en `nlp/data/nlu.yml`
3. Crear historias en `nlp/data/stories.yml`
4. Reentrenar el modelo: `rasa train`
5. Actualizar la lógica en `backend/main.py`

### Monitoreo

- **Logs del backend**: Se imprimen en la consola
- **Logs de base de datos**: Tabla `messages` contiene todo el historial
- **Métricas de Redis**: Usar `redis-cli` para inspeccionar caché

## Solución de Problemas

### El backend no se conecta a PostgreSQL

Verifica que Docker esté corriendo:
```bash
docker-compose ps
```

### El frontend no puede comunicarse con el backend

Verifica que el backend esté corriendo en el puerto 8000 y que CORS esté configurado correctamente.

### Error al entrenar el modelo de Rasa

Asegúrate de haber descargado el modelo de spaCy:
```bash
python -m spacy download es_core_news_md
```

## Contribuciones

Este proyecto fue desarrollado como parte de las residencias profesionales. Para contribuir:

1. Crea un fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## Contacto

Desarrollado para PluriOne S.A. de C.V. (Develop Talent & Technology)

- **Empresa**: contacto@develop.com.mx
- **Teléfono**: 55 1900 3503
- **Dirección**: Puebla 46, Colonia Roma Norte, CDMX

## Agradecimientos

- **PluriOne S.A. de C.V.** por proporcionar el proyecto
- **Rasa** por su framework conversacional open source
- **spaCy** por sus herramientas de NLP
- **Hugging Face** por los modelos pre-entrenados
