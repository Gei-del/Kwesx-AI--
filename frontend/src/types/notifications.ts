/**
 * types/notifications.ts
 * =======================
 * Interfaces para el sistema de notificaciones push.
 *
 * ESTADO ACTUAL: Arquitectura preparada — sin integración real.
 *
 * PARA ACTIVAR con Firebase Cloud Messaging:
 *   1. Crear proyecto en Firebase Console
 *   2. Instalar: npm install firebase
 *   3. Inicializar Firebase en src/lib/firebase.ts
 *   4. Reemplazar los stubs en useServiceWorker.ts
 *
 * PARA ACTIVAR con OneSignal:
 *   1. Crear cuenta en OneSignal
 *   2. Instalar: npm install @onesignal/node-onesignal
 *   3. Reemplazar los stubs en useServiceWorker.ts
 */

// ── Tipos de alerta territorial ───────────────────────────────────────────────

export type AlertaTipo =
  | "precio_insumos"      // UPRA — variación de precios significativa
  | "anomalia_climatica"  // IDEAM — evento climático extremo
  | "cierre_vial"         // ANI — bloqueo de carretera
  | "riesgo_territorial"  // ML — IVT pasa a categoría ALTA
  | "brecha_conectividad" // MinTIC — municipio sin internet
  | "sistema";            // Sistema — mantenimiento, actualizaciones

export type AlertaPrioridad = "CRITICA" | "ALTA" | "MEDIA" | "BAJA";

// ── Notificación push ─────────────────────────────────────────────────────────

export interface NotificacionPush {
  id:          string;
  tipo:        AlertaTipo;
  prioridad:   AlertaPrioridad;
  titulo:      string;
  cuerpo:      string;
  icono?:      string;
  urlAccion?:  string;      // Ruta a la que navegar al tocar
  timestamp:   string;
  leida:       boolean;
  datos?:      Record<string, unknown>;
}

// ── Preferencias de suscripción ───────────────────────────────────────────────

export interface PreferenciasNotificacion {
  habilitadas:  boolean;
  tipos:        Record<AlertaTipo, boolean>;
  municipio?:   string;
  departamento?: string;
}

export const PREFERENCIAS_DEFAULT: PreferenciasNotificacion = {
  habilitadas: false,
  tipos: {
    precio_insumos:      true,
    anomalia_climatica:  true,
    cierre_vial:         true,
    riesgo_territorial:  true,
    brecha_conectividad: false,
    sistema:             false,
  },
};

// ── Estado del Service Worker ─────────────────────────────────────────────────

export type ServiceWorkerStatus =
  | "idle"          // No inicializado
  | "registering"   // Registrándose
  | "ready"         // Listo y activo
  | "not-supported" // Navegador no soporta SW
  | "error";        // Error durante registro
