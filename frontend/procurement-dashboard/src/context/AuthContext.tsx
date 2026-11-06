import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile } from '../types/auth';
import { authApi } from '../services/api';

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const profile = await authApi.getCurrentUser();
          setUser(profile);
        } catch (err) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setError(null);
    try {
      const tokens = await authApi.login(email, password);
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      const profile = await authApi.getCurrentUser();
      setUser(profile);
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.message || 'Login failed';
      setError(msg);
      throw new Error(msg);
    }
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token') || '';
    try {
      await authApi.logout(refreshToken);
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

