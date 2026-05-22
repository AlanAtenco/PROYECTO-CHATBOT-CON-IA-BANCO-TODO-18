# Integración de PostgreSQL simulado con el asistente bancario Rasa

Este proyecto fue ajustado para que el asistente bancario deje de responder con datos fijos y consulte una **base de datos PostgreSQL simulada**. La simulación incluye clientes, cuentas, saldos, movimientos, servicios y pagos.

## Cambios principales

| Archivo | Cambio realizado |
|---|---|
| `database/init/01_banking_schema.sql` | Crea las tablas `clientes`, `cuentas`, `movimientos`, `servicios` y `pagos_servicios`, además de insertar datos de prueba. |
| `docker-compose.yml` | Monta el script de inicialización de PostgreSQL y agrega el servicio `action_server` para ejecutar acciones personalizadas de Rasa. |
| `rasa/actions/actions.py` | Implementa consultas reales a PostgreSQL para saldo, movimientos, transferencias, pagos y bloqueo simulado. |
| `rasa/endpoints.yml` | Activa el endpoint del servidor de acciones en `http://action_server:5055/webhook`. |
| `rasa/domain.yml`, `rasa/data/rules.yml`, `rasa/data/stories.yml` | Conectan los intents existentes con las nuevas acciones dinámicas. |
| `backend/main.py` | Usa variables de entorno (`DATABASE_URL`, `REDIS_URL`, `RASA_URL`) para funcionar correctamente dentro de Docker. |

## Datos simulados disponibles

La cuenta principal configurada para la simulación es `1234567890`. Si el usuario pregunta por saldo o movimientos sin indicar número de cuenta, el asistente usará esa cuenta por defecto.

| Cliente | Número de cuenta | Saldo inicial | Uso sugerido |
|---|---:|---:|---|
| Juan Pérez | `1234567890` | `$10,000.00 MXN` | Cuenta principal del usuario simulado. |
| María López | `9876543210` | `$5,200.50 MXN` | Cuenta destino para probar transferencias. |
| Carlos Ramírez | `5555666677` | `$2,500.75 MXN` | Cuenta adicional de prueba. |

## Cómo ejecutar el proyecto

Primero, entrena nuevamente Rasa porque se modificaron el dominio, reglas e historias. Después inicia todos los servicios con Docker Compose.

```bash
docker compose run --rm rasa train
docker compose up --build
```

Si ya tenías un volumen de PostgreSQL creado anteriormente, el script de inicialización no se ejecutará de nuevo automáticamente. Para reiniciar la base simulada desde cero puedes ejecutar:

```bash
docker compose down -v
docker compose run --rm rasa train
docker compose up --build
```

Si no deseas borrar el volumen, puedes cargar el script manualmente dentro del contenedor de PostgreSQL:

```bash
docker compose exec postgres psql -U admin -d asistente_bancario_db -f /docker-entrypoint-initdb.d/01_banking_schema.sql
```

## Ejemplos de mensajes para probar

| Función | Mensaje de ejemplo | Resultado esperado |
|---|---|---|
| Consultar saldo | `quiero consultar mi saldo` | Devuelve el saldo real de la cuenta `1234567890`. |
| Consultar movimientos | `muéstrame mis últimos movimientos` | Lista los últimos movimientos registrados en PostgreSQL. |
| Transferencia | `quiero transferir dinero` | Rasa solicitará destinatario, monto y cuenta destino; al confirmar, descuenta saldo e inserta movimientos. |
| Pago de servicio | `quiero pagar internet` | Rasa solicitará monto y cuenta; al confirmar, registra el pago y descuenta saldo. |
| Bloqueo | `bloquear mi tarjeta` | Cambia el estado de la cuenta por defecto a `bloqueada` dentro de la simulación. |

## Nota técnica importante

Esta integración es una simulación académica o de desarrollo. No incluye autenticación bancaria real, cifrado de datos sensibles ni controles antifraude. Para un entorno productivo sería obligatorio agregar autenticación robusta, autorización por usuario, auditoría, cifrado, manejo seguro de secretos y validaciones regulatorias.
