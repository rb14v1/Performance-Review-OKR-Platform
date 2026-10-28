import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { fetchMe, login as loginRequest } from "../api/endpoints/auth";
import { getAccessToken, getRefreshToken, setAccessToken, setRefreshToken } from "../api/client";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function bootstrap() {
      const refresh = getRefreshToken();
      if (!refresh) {
        setLoading(false);
        return;
      }
      try {
        // Access token isn't persisted; if we only have a refresh token
        // (e.g. page reload), force a fresh login instead of guessing.
        if (!getAccessToken()) {
          setLoading(false);
          return;
        }
        const me = await fetchMe();
        setUser(me);
      } catch {
        setAccessToken(null);
        setRefreshToken(null);
      } finally {
        setLoading(false);
      }
    }
    bootstrap();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { access, refresh } = await loginRequest(email, password);
    setAccessToken(access);
    setRefreshToken(refresh);
    const me = await fetchMe();
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
