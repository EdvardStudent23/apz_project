import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { User } from '@/api/types';
import * as authApi from '@/api/auth';
import {
  clearToken,
  getStoredToken,
  getStoredUser,
  setUnauthorizedHandler,
  storeToken,
  storeUser,
} from '@/api/client';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signUp: (username: string, email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getStoredUser<User>());
  const [loading, setLoading] = useState<boolean>(() => Boolean(getStoredToken()));

  const reset = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      reset();
    });
  }, [reset]);

  useEffect(() => {
    let cancelled = false;
    const token = getStoredToken();
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then((fresh) => {
        if (cancelled) return;
        setUser(fresh);
        storeUser(fresh);
      })
      .catch(() => {
        if (cancelled) return;
        reset();
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reset]);

  const signIn = useCallback(async (username: string, password: string) => {
    const result = await authApi.login({ username, password });
    storeToken(result.tokens.access_token);
    storeUser(result.user);
    setUser(result.user);
  }, []);

  const signUp = useCallback(async (username: string, email: string, password: string) => {
    const result = await authApi.register({ username, email, password });
    storeToken(result.tokens.access_token);
    storeUser(result.user);
    setUser(result.user);
  }, []);

  const signOut = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      /* best-effort */
    }
    reset();
  }, [reset]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      loading,
      signIn,
      signUp,
      signOut,
    }),
    [user, loading, signIn, signUp, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
