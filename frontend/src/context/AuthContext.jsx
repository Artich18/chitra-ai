import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import api from '../lib/api';

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    try {
      const { data } = await api.get('/auth/me');
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Skip /me check if we're processing OAuth callback
    if (window.location.hash?.includes('session_id=')) {
      setLoading(false);
      return;
    }
    fetchMe();
  }, [fetchMe]);

  const loginWithPassword = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password });
    localStorage.setItem('chitra_token', data.token);
    setUser(data.user);
    return data.user;
  };

  const registerWithPassword = async (name, email, password) => {
    const { data } = await api.post('/auth/register', { name, email, password });
    localStorage.setItem('chitra_token', data.token);
    setUser(data.user);
    return data.user;
  };

  const completeGoogleSession = async (sessionId) => {
    const { data } = await api.post('/auth/google/session', { session_id: sessionId });
    if (data?.session_token) localStorage.setItem('chitra_token', data.session_token);
    setUser(data.user);
    return data.user;
  };

  const logout = async () => {
    try { await api.post('/auth/logout'); } catch {}
    localStorage.removeItem('chitra_token');
    setUser(null);
  };

  return (
    <AuthCtx.Provider value={{ user, loading, loginWithPassword, registerWithPassword, completeGoogleSession, logout, refresh: fetchMe }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
