/**
 * Kwesx AI — Service Worker
 * ==========================
 * Cache básico offline-first para mejorar la experiencia en zonas con
 * conectividad intermitente (contexto: comunidades rurales de Colombia).
 *
 * ESTADO ACTUAL: Cache básico + estructura preparada para Push Notifications.
 *
 * PARA ACTIVAR PUSH NOTIFICATIONS:
 *   1. Configurar VAPID keys en el backend
 *   2. Implementar el evento 'push' con notificaciones reales
 *   3. Conectar con useServiceWorker.ts → subscribe()
 */

const CACHE_VERSION = "kwesx-v1";
const STATIC_ASSETS = [
  "/",
  "/asistente",
  "/datos/upra",
  "/datos/ani",
  "/datos/ideam",
];

// ── Instalación ───────────────────────────────────────────────────────────────

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_VERSION)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// ── Activación ────────────────────────────────────────────────────────────────

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_VERSION)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

// ── Fetch — Network first con fallback a cache ────────────────────────────────

self.addEventListener("fetch", (event) => {
  // Solo cachear peticiones GET de navegación (no la API)
  const url = new URL(event.request.url);
  const isAPI = url.pathname.startsWith("/api/") || url.port === "8000";
  const isNavigation = event.request.mode === "navigate";

  if (isAPI || !isNavigation) return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Actualizar cache con respuesta fresca
        const clone = response.clone();
        caches.open(CACHE_VERSION).then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() =>
        // Sin conexión: servir desde cache
        caches.match(event.request).then((cached) => cached || caches.match("/"))
      )
  );
});

// ── Push Notifications (stub — listo para activar) ────────────────────────────

self.addEventListener("push", (event) => {
  if (!event.data) return;

  let data;
  try {
    data = event.data.json();
  } catch {
    data = { titulo: "Kwesx AI", cuerpo: event.data.text() };
  }

  event.waitUntil(
    self.registration.showNotification(data.titulo || "Kwesx AI", {
      body:  data.cuerpo || "Nueva alerta territorial",
      icon:  "/icon-192.png",
      badge: "/badge-72.png",
      tag:   data.tipo || "kwesx-alert",
      data:  { url: data.urlAccion || "/" },
    })
  );
});

// ── Clic en notificación ──────────────────────────────────────────────────────

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === url && "focus" in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
