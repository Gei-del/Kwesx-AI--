"use client";

/**
 * contexts/AuthContext.tsx
 * ========================
 * Arquitectura de autenticación preparada para producción.
 *
 * ESTADO ACTUAL: Modo demostración — sin auth real.
 * Los valores aquí son stubs que representan un usuario demo.
 *
 * PARA ACTIVAR AUTH REAL:
 *   1. Implementar backend/app/routers/auth.py con /auth/login, /auth/register, etc.
 *   2. Reemplazar authService.login/register/logout con llamadas reales a la API
 *   3. Implementar almacenamiento seguro de tokens (httpOnly cookies en producción)
 *   4. Activar el middleware en src/middleware.ts
 */

import React, { createContext, useContext, useState, useCallback, useMemo } from "react";
import type { User, AuthState } from "@/types/auth";

// ── Interfaces del contexto ────────────────────────────────────────────────────

interface AuthContextValue extends AuthState {
  login:          (email: string, password: string) => Promise<void>;
  register:       (data: { email: string; password: string; nombre: string }) => Promise<void>;
  logout:         () => void;
  resetPassword:  (email: string) => Promise<void>;
  clearError:     () => void;
}

// ── Usuario demo (modo demostración) ──────────────────────────────────────────

const DEMO_USER: User = {
  id:          "demo-001",
  email:       "demo@kwesx.ai",
  nombre:      "Usuario Demo",
  rol:         "ciudadano",
  municipio:   "Bogotá D.C.",
  departamento: "Cundinamarca",
  createdAt:   new Date().toISOString(),
};

// ── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user,      setUser]      = useState<User | null>(DEMO_USER);   // demo: siempre logueado
  const [isLoading, setIsLoading] = useState(false);
  const [error,     setError]     = useState<string | null>(null);

  /**
   * login — Stub para implementación futura.
   * TODO: Reemplazar con llamada real a POST /auth/login
   */
  const login = useCallback(async (_email: string, _password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      // TODO: const response = await authService.login({ email, password });
      // TODO: setUser(response.user);
      // TODO: storeTokens(response.tokens);
      setUser(DEMO_USER);   // demo
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * register — Stub para implementación futura.
   * TODO: Reemplazar con llamada real a POST /auth/register
   */
  const register = useCallback(async (_data: { email: string; password: string; nombre: string }) => {
    setIsLoading(true);
    setError(null);
    try {
      // TODO: const response = await authService.register(data);
      // TODO: setUser(response.user);
      setUser(DEMO_USER);   // demo
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrarse");
    } finally {
      setIsLoading(false);
    }
  }, []);

  /** logout */
  const logout = useCallback(() => {
    // TODO: authService.logout();
    // TODO: clearTokens();
    setUser(null);
  }, []);

  /**
   * resetPassword — Stub para implementación futura.
   * TODO: Reemplazar con llamada real a POST /auth/reset-password
   */
  const resetPassword = useCallback(async (_email: string) => {
    setIsLoading(true);
    try {
      // TODO: await authService.resetPassword({ email });
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    register,
    logout,
    resetPassword,
    clearError,
  }), [user, isLoading, error, login, register, logout, resetPassword, clearError]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
