export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface User {
  id: string;
  name: string;
  email: string;
  accountNumber?: string;
  balance?: number;
}

export interface AuthPayload {
  token: string;
  user: User;
}

export const getStoredAuth = (): AuthPayload | null => {
  const raw = localStorage.getItem('bankAuth');
  if (!raw) return null;

  try {
    return JSON.parse(raw) as AuthPayload;
  } catch (error) {
    console.error('No se pudo leer la sesión local:', error);
    localStorage.removeItem('bankAuth');
    return null;
  }
};

export const saveStoredAuth = (auth: AuthPayload) => {
  localStorage.setItem('bankAuth', JSON.stringify(auth));
};

export const clearStoredAuth = () => {
  localStorage.removeItem('bankAuth');
};

export const authHeaders = (token?: string): HeadersInit => ({
  'Content-Type': 'application/json',
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
});
