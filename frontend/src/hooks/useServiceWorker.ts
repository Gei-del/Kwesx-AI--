"use client";

/**
 * hooks/useServiceWorker.ts
 * =========================
 * Hook para registrar el Service Worker y gestionar notificaciones push.
 *
 * ESTADO ACTUAL: Service Worker registrado pero sin push real.
 * El SW actualmente solo gestiona cache offline básico.
 *
 * PARA ACTIVAR NOTIFICACIONES PUSH:
 *   1. Obtener VAPID keys: npx web-push generate-vapid-keys
 *   2. Configurar NEXT_PUBLIC_VAPID_PUBLIC_KEY en .env
 *   3. Implementar el endpoint POST /notificaciones/suscribir en backend
 *   4. Reemplazar los stubs de subscribe/unsubscribe
 *
 * REFERENCIA:
 *   https://developer.mozilla.org/en-US/docs/Web/API/Push_API
 */

import { useState, useEffect, useCallback } from "react";
import type { ServiceWorkerStatus, PreferenciasNotificacion, PREFERENCIAS_DEFAULT } from "@/types/notifications";

// Silencia el error de tipo circular
type _Prefs = typeof PREFERENCIAS_DEFAULT;

interface UseServiceWorkerReturn {
  status:          ServiceWorkerStatus;
  isSupported:     boolean;
  isSubscribed:    boolean;
  subscribe:       () => Promise<void>;
  unsubscribe:     () => Promise<void>;
  preferencias:    PreferenciasNotificacion | null;
  setPreferencias: (p: PreferenciasNotificacion) => void;
}

const PREFS_KEY = "kwesx-notif-prefs";

export function useServiceWorker(): UseServiceWorkerReturn {
  const [status,       setStatus]       = useState<ServiceWorkerStatus>("idle");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [preferencias, setPrefsState]  = useState<PreferenciasNotificacion | null>(null);

  const isSupported = typeof window !== "undefined" && "serviceWorker" in navigator && "PushManager" in window;

  // Registrar el Service Worker al montar
  useEffect(() => {
    if (!isSupported) {
      setStatus("not-supported");
      return;
    }

    const register = async () => {
      setStatus("registering");
      try {
        const registration = await navigator.serviceWorker.register("/sw.js", {
          scope: "/",
        });
        console.info("[SW] Registrado:", registration.scope);
        setStatus("ready");

        // Verificar si ya hay suscripción activa
        const sub = await registration.pushManager.getSubscription();
        setIsSubscribed(!!sub);
      } catch (err) {
        console.error("[SW] Error al registrar:", err);
        setStatus("error");
      }
    };

    register();
  }, [isSupported]);

  // Cargar preferencias guardadas
  useEffect(() => {
    try {
      const saved = localStorage.getItem(PREFS_KEY);
      if (saved) setPrefsState(JSON.parse(saved));
    } catch { /* ignore */ }
  }, []);

  /**
   * subscribe — Solicitar permiso y suscribir al push.
   * TODO: Implementar con VAPID keys y endpoint real.
   */
  const subscribe = useCallback(async () => {
    if (!isSupported || status !== "ready") return;

    const permission = await Notification.requestPermission();
    if (permission !== "granted") return;

    try {
      // TODO: const reg = await navigator.serviceWorker.ready;
      // TODO: const sub = await reg.pushManager.subscribe({
      // TODO:   userVisibleOnly: true,
      // TODO:   applicationServerKey: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY,
      // TODO: });
      // TODO: await fetch("/api/notificaciones/suscribir", { method: "POST", body: JSON.stringify(sub) });
      setIsSubscribed(true);
      console.info("[SW] Suscripción push activada (stub)");
    } catch (err) {
      console.error("[SW] Error al suscribir:", err);
    }
  }, [isSupported, status]);

  /**
   * unsubscribe — Cancelar la suscripción push.
   * TODO: Implementar con endpoint real.
   */
  const unsubscribe = useCallback(async () => {
    try {
      // TODO: const reg = await navigator.serviceWorker.ready;
      // TODO: const sub = await reg.pushManager.getSubscription();
      // TODO: await sub?.unsubscribe();
      // TODO: await fetch("/api/notificaciones/cancelar", { method: "POST" });
      setIsSubscribed(false);
    } catch (err) {
      console.error("[SW] Error al cancelar suscripción:", err);
    }
  }, []);

  const setPreferencias = useCallback((p: PreferenciasNotificacion) => {
    setPrefsState(p);
    try { localStorage.setItem(PREFS_KEY, JSON.stringify(p)); } catch { /* ignore */ }
  }, []);

  return { status, isSupported, isSubscribed, subscribe, unsubscribe, preferencias, setPreferencias };
}
