import { useEffect, useState } from 'react';
import './App.css';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import { API_URL, AuthPayload, User, authHeaders, clearStoredAuth, getStoredAuth, saveStoredAuth } from './api';

function App() {
  const [auth, setAuth] = useState<AuthPayload | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const storedAuth = getStoredAuth();
      if (!storedAuth?.token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/auth/me`, {
          headers: authHeaders(storedAuth.token),
        });

        if (!response.ok) {
          throw new Error('Sesión expirada o inválida');
        }

        const user = (await response.json()) as User;
        const refreshedAuth = { token: storedAuth.token, user };
        setAuth(refreshedAuth);
        saveStoredAuth(refreshedAuth);
      } catch (error) {
        console.error('Error al validar la sesión:', error);
        clearStoredAuth();
        setAuth(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogin = (authData: AuthPayload) => {
    setAuth(authData);
    saveStoredAuth(authData);
  };

  const handleLogout = async () => {
    if (auth?.token) {
      try {
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: authHeaders(auth.token),
        });
      } catch (error) {
        console.warn('No se pudo cerrar la sesión en el servidor:', error);
      }
    }

    setAuth(null);
    clearStoredAuth();
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="app">
      {auth ? (
        <Dashboard user={auth.user} token={auth.token} onLogout={handleLogout} />
      ) : (
        <Login onLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;
