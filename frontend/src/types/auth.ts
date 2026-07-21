/**
 * types/auth.ts
 * =============
 * Interfaces de autenticación — arquitectura preparada para producción.
 *
 * NOTA: Este módulo está preparado para implementación futura.
 * El proyecto actualmente corre en Modo Demostración.
 * Para activar auth real: implementar los endpoints en backend/app/routers/auth.py
 * y conectar AuthContext con el servicio real.
 */

// ── Usuario ────────────────────────────────────────────────────────────────────

export interface User {
  id:          string;
  email:       string;
  nombre:      string;
  rol:         UserRole;
  municipio?:  string;
  departamento?: string;
  createdAt:   string;
  avatarUrl?:  string;
}

export type UserRole = "ciudadano" | "funcionario" | "investigador" | "admin";

// ── Tokens ─────────────────────────────────────────────────────────────────────

export interface AuthTokens {
  accessToken:  string;
  refreshToken: string;
  expiresIn:    number;   // segundos
  tokenType:    "Bearer";
}

// ── Requests / Responses ──────────────────────────────────────────────────────

export interface LoginRequest {
  email:    string;
  password: string;
}

export interface RegisterRequest {
  email:       string;
  password:    string;
  nombre:      string;
  rol?:        UserRole;
  municipio?:  string;
  departamento?: string;
}

export interface ResetPasswordRequest {
  email: string;
}

export interface ChangePasswordRequest {
  token:       string;
  newPassword: string;
}

export interface AuthResponse {
  user:   User;
  tokens: AuthTokens;
}

// ── Estado de autenticación ────────────────────────────────────────────────────

export interface AuthState {
  user:          User | null;
  isAuthenticated: boolean;
  isLoading:     boolean;
  error:         string | null;
}
