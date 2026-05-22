-- Esquema bancario simulado para el asistente virtual
-- Este archivo se ejecuta automáticamente cuando PostgreSQL inicializa un volumen nuevo.

CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    documento VARCHAR(50) UNIQUE NOT NULL,
    telefono VARCHAR(30),
    email VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cuentas (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    numero_cuenta VARCHAR(20) UNIQUE NOT NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'ahorro',
    moneda VARCHAR(10) NOT NULL DEFAULT 'MXN',
    saldo NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    estado VARCHAR(30) NOT NULL DEFAULT 'activa', -- 'activa' o 'bloqueada'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usuarios (
    id VARCHAR(36) PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'activo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios (LOWER(email));
CREATE INDEX IF NOT EXISTS idx_usuarios_cliente_id ON usuarios (cliente_id);

CREATE TABLE IF NOT EXISTS auth_sessions (
    token VARCHAR(128) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at ON auth_sessions (expires_at);

CREATE TABLE IF NOT EXISTS movimientos (
    id SERIAL PRIMARY KEY,
    cuenta_id INTEGER NOT NULL REFERENCES cuentas(id),
    tipo VARCHAR(40) NOT NULL,
    descripcion TEXT NOT NULL,
    monto NUMERIC(14, 2) NOT NULL,
    saldo_resultante NUMERIC(14, 2) NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servicios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(80) UNIQUE NOT NULL,
    referencia VARCHAR(80),
    estado VARCHAR(30) NOT NULL DEFAULT 'activo'
);

CREATE TABLE IF NOT EXISTS pagos_servicios (
    id SERIAL PRIMARY KEY,
    cuenta_id INTEGER NOT NULL REFERENCES cuentas(id),
    servicio_id INTEGER NOT NULL REFERENCES servicios(id),
    monto NUMERIC(14, 2) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'aprobado',
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(36) REFERENCES usuarios(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id);

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
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages (user_id);

INSERT INTO clientes (nombre, documento, telefono, email)
VALUES
    ('Juan Pérez', 'CLI-001', '+52 55 1000 1000', 'juan.perez@example.com'),
    ('María López', 'CLI-002', '+52 55 2000 2000', 'maria.lopez@example.com'),
    ('Carlos Ramírez', 'CLI-003', '+52 55 3000 3000', 'carlos.ramirez@example.com')
ON CONFLICT (documento) DO NOTHING;

INSERT INTO cuentas (cliente_id, numero_cuenta, tipo, moneda, saldo, estado)
SELECT id, '1234567890', 'ahorro', 'MXN', 10000.00, 'activa'
FROM clientes WHERE documento = 'CLI-001'
ON CONFLICT (numero_cuenta) DO NOTHING;

INSERT INTO cuentas (cliente_id, numero_cuenta, tipo, moneda, saldo, estado)
SELECT id, '9876543210', 'ahorro', 'MXN', 5200.50, 'activa'
FROM clientes WHERE documento = 'CLI-002'
ON CONFLICT (numero_cuenta) DO NOTHING;

INSERT INTO cuentas (cliente_id, numero_cuenta, tipo, moneda, saldo, estado)
SELECT id, '5555666677', 'corriente', 'MXN', 2500.75, 'activa'
FROM clientes WHERE documento = 'CLI-003'
ON CONFLICT (numero_cuenta) DO NOTHING;

INSERT INTO servicios (nombre, referencia, estado)
VALUES
    ('luz', 'CFE-001', 'activo'),
    ('agua', 'AGUA-001', 'activo'),
    ('internet', 'TELCO-001', 'activo'),
    ('telefono', 'TEL-001', 'activo')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO movimientos (cuenta_id, tipo, descripcion, monto, saldo_resultante, fecha)
SELECT c.id, 'deposito', 'Depósito inicial de nómina', 10000.00, c.saldo, CURRENT_TIMESTAMP - INTERVAL '5 days'
FROM cuentas c WHERE c.numero_cuenta = '1234567890'
AND NOT EXISTS (SELECT 1 FROM movimientos m WHERE m.cuenta_id = c.id);

INSERT INTO movimientos (cuenta_id, tipo, descripcion, monto, saldo_resultante, fecha)
SELECT c.id, 'retiro', 'Retiro en cajero automático', -500.00, c.saldo - 500.00, CURRENT_TIMESTAMP - INTERVAL '3 days'
FROM cuentas c WHERE c.numero_cuenta = '1234567890'
AND (SELECT COUNT(*) FROM movimientos m WHERE m.cuenta_id = c.id) < 2;

INSERT INTO movimientos (cuenta_id, tipo, descripcion, monto, saldo_resultante, fecha)
SELECT c.id, 'pago', 'Pago de servicio de internet', -650.00, c.saldo - 1150.00, CURRENT_TIMESTAMP - INTERVAL '1 day'
FROM cuentas c WHERE c.numero_cuenta = '1234567890'
AND (SELECT COUNT(*) FROM movimientos m WHERE m.cuenta_id = c.id) < 3;
