import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { supabase } from '../lib/supabase';

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const syncSession = useCallback(async () => {
    // Try Supabase first (if configured)
    let foundUser = null;
    try {
      if (supabase) {
        const { data: { session }, error } = await supabase.auth.getSession();
        if (error) throw error;
        const nextUser = session?.user ?? null;
        setUser(nextUser);
        if (session?.access_token) {
          localStorage.setItem('chitra_token', session.access_token);
          foundUser = nextUser;
        } else {
          localStorage.removeItem('chitra_token');
        }
      }
    } catch {
      setUser(null);
      localStorage.removeItem('chitra_token');
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    let active = true;
    syncSession();

    if (!supabase) {
      setLoading(false);
      return undefined;
    }

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!active) return;
      setUser(session?.user ?? null);
      if (session?.access_token) {
        localStorage.setItem('chitra_token', session.access_token);
      } else {
        localStorage.removeItem('chitra_token');
      }
      setLoading(false);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, [syncSession]);

  const loginWithPassword = async (email, password) => {
    if (!supabase) throw new Error('Supabase is not configured');
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    if (data.session?.access_token) localStorage.setItem('chitra_token', data.session.access_token);
    setUser(data.user ?? null);
    return data.user;
  };

  const registerWithPassword = async (name, email, password) => {
    if (!supabase) throw new Error('Supabase is not configured');
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: name },
        emailRedirectTo: window.location.origin + '/',
      },
    });
    if (error) throw error;
    if (data.session?.access_token) localStorage.setItem('chitra_token', data.session.access_token);
    setUser(data.user ?? null);
    return data.user;
  };

  const completeGoogleSession = async () => {
    if (!supabase) throw new Error('Supabase is not configured');
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) throw error;
    setUser(session?.user ?? null);
    if (session?.access_token) localStorage.setItem('chitra_token', session.access_token);
    else localStorage.removeItem('chitra_token');
    return session?.user ?? null;
  };

  const logout = async () => {
    if (supabase) await supabase.auth.signOut();
    localStorage.removeItem('chitra_token');
    setUser(null);
  };

  return (
    <AuthCtx.Provider value={{ user, loading, loginWithPassword, registerWithPassword, completeGoogleSession, logout, refresh: syncSession }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
