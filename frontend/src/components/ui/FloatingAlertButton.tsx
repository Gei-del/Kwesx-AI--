"use client";

/**
 * FloatingAlertButton — Botón flotante de alertas territoriales
 *
 * Siempre visible en la esquina inferior derecha.
 * Al hacer clic muestra un panel con tipos de alerta disponibles.
 * Accesible con teclado (Escape para cerrar).
 */

import { useState, useEffect, useRef } from "react";
import { Bell, X, CloudLightning, Truck, Sprout, Wifi, AlertTriangle } from "lucide-react";
import clsx from "clsx";
import { useApp } from "@/contexts/AppContext";

const TIPOS_ALERTA = [
  { id: "clima",      icon: CloudLightning, label: "Alertas de clima",       sub: "Lluvias fuertes, sequías",        color: "text-sky-dark" },
  { id: "vias",       icon: Truck,          label: "Cierres viales",          sub: "Bloqueos y accidentes",           color: "text-amber-dark" },
  { id: "precios",    icon: Sprout,         label: "Cambios en precios",      sub: "Fertilizantes y cultivos",        color: "text-terra" },
  { id: "conectividad",icon: Wifi,          label: "Conectividad",            sub: "Red vial e internet",             color: "text-warm-600" },
  { id: "emergencia", icon: AlertTriangle,  label: "Emergencias territoriales",sub: "Alertas críticas de la zona",   color: "text-danger" },
];

export default function FloatingAlertButton() {
  const { alertsEnabled, toggleAlerts } = useApp();
  const [open,       setOpen]      = useState(false);
  const [subscribed, setSubscribed] = useState<Record<string, boolean>>({});
  const [saved,      setSaved]     = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  // Cerrar con Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  // Restaurar suscripciones
  useEffect(() => {
    try {
      const s = localStorage.getItem("kwesx-alertas");
      if (s) setSubscribed(JSON.parse(s));
    } catch { /* ignore */ }
  }, []);

  const toggleSub = (id: string) => {
    setSubscribed((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const guardar = () => {
    try {
      localStorage.setItem("kwesx-alertas", JSON.stringify(subscribed));
    } catch { /* ignore */ }
    if (!alertsEnabled) toggleAlerts();
    setSaved(true);
    setTimeout(() => { setSaved(false); setOpen(false); }, 1500);
  };

  const contActivas = Object.values(subscribed).filter(Boolean).length;

  return (
    <>
      {/* ── FAB ──────────────────────────────────────────────────────────── */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="fab"
        aria-label={open ? "Cerrar alertas" : "Activar alertas inteligentes"}
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        <div className="relative">
          <Bell size={20} aria-hidden />
          {contActivas > 0 && (
            <span
              className="absolute -top-1 -right-1 w-4 h-4 bg-amber rounded-full text-white text-2xs font-bold flex items-center justify-center"
              aria-label={`${contActivas} alertas activas`}
            >
              {contActivas}
            </span>
          )}
        </div>
        <span className="hidden sm:inline">
          {contActivas > 0 ? `${contActivas} alertas` : "Alertas inteligentes"}
        </span>
      </button>

      {/* ── Panel de alertas ─────────────────────────────────────────────── */}
      {open && (
        <>
          {/* Overlay */}
          <div
            className="fixed inset-0 z-40 bg-black/20"
            onClick={() => setOpen(false)}
            aria-hidden
          />

          {/* Panel */}
          <div
            ref={panelRef}
            role="dialog"
            aria-label="Configurar alertas territoriales"
            aria-modal="true"
            className="fixed bottom-24 right-6 z-50 w-80 bg-white rounded-3xl animate-pop"
            style={{ boxShadow: "0 20px 60px rgb(0 0 0 / 0.15)" }}
          >
            {/* Header */}
            <div className="flex items-start justify-between p-5 border-b border-warm-100">
              <div>
                <p className="font-bold text-warm-900 text-base">🔔 Alertas Inteligentes</p>
                <p className="text-xs text-warm-500 mt-0.5">
                  Recibe avisos cuando algo cambia en tu territorio
                </p>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="btn-ghost p-1.5 ml-2"
                aria-label="Cerrar panel de alertas"
              >
                <X size={16} />
              </button>
            </div>

            {/* Tipos de alerta */}
            <div className="p-4 space-y-2">
              {TIPOS_ALERTA.map((tipo) => {
                const Icon    = tipo.icon;
                const checked = !!subscribed[tipo.id];
                return (
                  <label
                    key={tipo.id}
                    className={clsx(
                      "flex items-center gap-3 p-3 rounded-2xl cursor-pointer transition-all border",
                      checked
                        ? "bg-terra-faint border-terra-pale"
                        : "bg-warm-50 border-transparent hover:border-warm-200"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleSub(tipo.id)}
                      className="sr-only"
                      aria-label={tipo.label}
                    />
                    {/* Checkbox visual */}
                    <div
                      className={clsx(
                        "w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all",
                        checked
                          ? "bg-terra border-terra"
                          : "border-warm-300 bg-white"
                      )}
                      aria-hidden
                    >
                      {checked && (
                        <svg width="10" height="8" fill="none" viewBox="0 0 10 8">
                          <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      )}
                    </div>

                    <Icon size={16} className={clsx("shrink-0", tipo.color)} aria-hidden />

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-warm-900">{tipo.label}</p>
                      <p className="text-xs text-warm-400">{tipo.sub}</p>
                    </div>
                  </label>
                );
              })}
            </div>

            {/* Botón guardar */}
            <div className="px-4 pb-4">
              <button
                onClick={guardar}
                className={clsx(
                  "btn-primary w-full justify-center",
                  saved && "bg-emerald-500"
                )}
                disabled={saved}
              >
                {saved ? "✓ ¡Alertas activadas!" : "Guardar mis alertas"}
              </button>
              <p className="text-xs text-warm-400 text-center mt-2">
                Las alertas se guardan en este dispositivo
              </p>
            </div>
          </div>
        </>
      )}
    </>
  );
}
