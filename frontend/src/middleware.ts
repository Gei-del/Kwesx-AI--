/**
 * middleware.ts
 * =============
 * Middleware de Next.js para protección de rutas.
 *
 * ESTADO ACTUAL: Desactivado — el proyecto corre en Modo Demostración.
 *
 * PARA ACTIVAR:
 *   1. Implementar validación real de JWT en `isAuthenticated()`
 *   2. Descomentar la exportación del `config.matcher` con las rutas protegidas
 *   3. Conectar con el sistema de tokens de AuthContext
 *
 * REFERENCIA: https://nextjs.org/docs/app/building-your-application/routing/middleware
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// ── Rutas que requieren autenticación ─────────────────────────────────────────
// const PROTECTED_ROUTES = ["/perfil", "/admin", "/configuracion"];

// ── Rutas solo para no autenticados ───────────────────────────────────────────
// const AUTH_ROUTES = ["/auth/login", "/auth/registro"];

/**
 * Verifica si el request tiene un token válido.
 * TODO: Implementar verificación real de JWT.
 */
// function isAuthenticated(request: NextRequest): boolean {
//   const token = request.cookies.get("access_token")?.value;
//   if (!token) return false;
//   try {
//     // TODO: verificar firma del JWT
//     return true;
//   } catch {
//     return false;
//   }
// }

export function middleware(_request: NextRequest) {
  // En modo demostración, permitir todo el tráfico sin restricciones
  return NextResponse.next();

  // IMPLEMENTACIÓN FUTURA:
  // const authenticated = isAuthenticated(request);
  // const path = request.nextUrl.pathname;
  //
  // if (PROTECTED_ROUTES.some(r => path.startsWith(r)) && !authenticated) {
  //   return NextResponse.redirect(new URL("/auth/login", request.url));
  // }
  //
  // if (AUTH_ROUTES.some(r => path.startsWith(r)) && authenticated) {
  //   return NextResponse.redirect(new URL("/", request.url));
  // }
  //
  // return NextResponse.next();
}

export const config = {
  // Ejecutar el middleware en todas las rutas excepto assets estáticos
  matcher: ["/((?!_next/static|_next/image|favicon.ico|public/).*)"],
};
