import React, { useState } from 'react';

interface LoginProps {
  onLogin: (user: { id: string; name: string; email: string }) => void;
}

export default function Login({ onLogin }: LoginProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validaciones
      if (!formData.email || !formData.password) {
        setError('Por favor completa todos los campos');
        setLoading(false);
        return;
      }

      if (!isLogin) {
        if (!formData.name) {
          setError('Por favor ingresa tu nombre');
          setLoading(false);
          return;
        }
        if (formData.password !== formData.confirmPassword) {
          setError('Las contraseñas no coinciden');
          setLoading(false);
          return;
        }
      }

      // Simular delay de servidor
      await new Promise(resolve => setTimeout(resolve, 800));

      // Crear usuario
      const user = {
        id: `user_${Date.now()}`,
        name: formData.name || formData.email.split('@')[0],
        email: formData.email
      };

      onLogin(user);
    } catch (err) {
      setError('Error al procesar la solicitud. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setFormData({ name: '', email: '', password: '', confirmPassword: '' });
    setError('');
  };

  return (
    <div className="login-container">
      {/* Fondo decorativo */}
      <div className="login-background">
        <div className="gradient-blob blob-1"></div>
        <div className="gradient-blob blob-2"></div>
      </div>

      {/* Contenido */}
      <div className="login-content">
        {/* Logo y título */}
        <div className="login-header">
          <div className="bank-logo">B</div>
          <h1>Banco Digital</h1>
          <p>Tu banco en tus manos</p>
        </div>

        {/* Formulario */}
        <form className="login-form" onSubmit={handleSubmit}>
          <h2>{isLogin ? 'Iniciar Sesión' : 'Crear Cuenta'}</h2>
          
          {error && <div className="error-message">{error}</div>}

          {!isLogin && (
            <div className="form-group">
              <label htmlFor="name">Nombre Completo</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Tu nombre completo"
                required={!isLogin}
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Correo Electrónico</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="tu@email.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              required
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label htmlFor="confirmPassword">Confirmar Contraseña</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="••••••••"
                required={!isLogin}
              />
            </div>
          )}

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Procesando...' : (isLogin ? 'Iniciar Sesión' : 'Crear Cuenta')}
          </button>
        </form>

        {/* Toggle entre login y registro */}
        <div className="login-toggle">
          <p>
            {isLogin ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?'}
            <button
              type="button"
              onClick={toggleMode}
              className="toggle-button"
            >
              {isLogin ? 'Regístrate aquí' : 'Inicia sesión aquí'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
