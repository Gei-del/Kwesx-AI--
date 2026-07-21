"use client";

/**
 * TopBar — Barra superior de Kwesx AI
 *
 * Incluye:
 *   - Título de la página en lenguaje humano
 *   - Controles de accesibilidad (fuente, contraste, voz)
 *   - Panel de accesibilidad expandible
 *   - Estado de conexión
 */

import { useState } from "react";
import { usePathname } from "next/navigation";
import {
  RefreshCw, Accessibility, Type, Sun, Volume2, VolumeX, ChevronDown,
  CheckCircle, User, LogOut, Settings, HelpCircle, Menu
} from "lucide-react";
import clsx from "clsx";
import { useApp } from "@/contexts/AppContext";

// ─── Títulos en lenguaje humano ───────────────────────────────────────────────

const PAGE_TITLES: Record<string, { title: string; sub: string; emoji: string }> = {
  "/":            { title: "Tu Territorio Hoy",         sub: "Lo más importante en un vistazo", emoji: "🏠" },
  "/asistente":   { title: "Pregúntale a Kwesx",        sub: "Escribe o habla tu pregunta",     emoji: "💬" },
  "/datos/upra":  { title: "Precios del Campo",         sub: "Fertilizantes, semillas e insumos", emoji: "🌱" },
  "/datos/ani":   { title: "Estado de las Vías",        sub: "Tráfico y condición de carreteras", emoji: "🛣️" },
  "/datos/ideam": { title: "El Tiempo en Colombia",     sub: "Lluvia, temperatura y clima",      emoji: "🌦️" },
  "/prediccion":   { title: "Calidad de Vida en tu Zona", sub: "Análisis territorial inteligente", emoji: "🏘️" },
  "/conectividad": { title: "Brecha Digital",             sub: "Acceso a internet por municipio",           emoji: "📶" },
  "/educacion":    { title: "Cobertura Educativa",        sub: "Matrícula y tasas por nivel",               emoji: "🎓" },
  "/riesgos":      { title: "Alertas de Riesgo",          sub: "Anomalías detectadas por IA",               emoji: "⚠️" },
  "/insights":     { title: "Insights de IA",             sub: "Ensemble · Clustering · Forecasting · XAI", emoji: "🤖" },
};

// ─── Componente ───────────────────────────────────────────────────────────────

export default function TopBar() {
  const pathname = usePathname();
  const page     = PAGE_TITLES[pathname] ?? { title: "Kwesx AI", sub: "Inteligencia Territorial", emoji: "🌎" };
  const { fontSize, contrast, voiceEnabled, setFontSize, toggleContrast, toggleVoice, toggleMobileNav } = useApp();

  const [showAccPanel,    setShowAccPanel]    = useState(false);
  const [showUserMenu,    setShowUserMenu]    = useState(false);
  const [refreshing,      setRefreshing]      = useState(false);
  const [demoMsg,         setDemoMsg]         = useState(false);

  const now = new Date().toLocaleDateString("es-CO", {
    weekday: "long", month: "long", day: "numeric"
  });

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => { window.location.reload(); }, 300);
  };

  return (
    <header
      className="glass border-b border-warm-100 px-5 md:px-8 flex items-center justify-between shrink-0"
      style={{ minHeight: "64px" }}
      role="banner"
    >
      {/* ── Hamburger (móvil) ───────────────────────────────────────────── */}
      <button
        onClick={toggleMobileNav}
        className="btn-ghost p-2.5 lg:hidden mr-1"
        aria-label="Abrir menú de navegación"
      >
        <Menu size={20} />
      </button>

      {/* ── Título ──────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <span className="text-2xl hidden sm:block" aria-hidden>{page.emoji}</span>
        <div>
          <h1 className="text-base font-bold text-warm-900 leading-tight">
            {page.title}
          </h1>
          <p className="text-xs text-warm-500 capitalize hidden sm:block">{now} · {page.sub}</p>
        </div>
      </div>

      {/* ── Controles ───────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2">

        {/* Indicador online */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-terra-faint text-xs font-medium text-terra-dark">
          <span className="status-dot" aria-hidden />
          Actualizado
        </div>

        {/* Actualizar */}
        <button
          onClick={handleRefresh}
          className="btn-ghost p-2.5"
          title="Actualizar datos"
          aria-label="Actualizar información del territorio"
        >
          <RefreshCw size={16} className={clsx(refreshing && "animate-spin")} />
        </button>

        {/* Accesibilidad */}
        <div className="relative">
          <button
            onClick={() => { setShowAccPanel((v) => !v); setShowUserMenu(false); }}
            className={clsx(
              "btn-ghost p-2.5 flex items-center gap-1.5",
              showAccPanel ? "bg-terra-faint text-terra" : "text-warm-500 hover:text-terra"
            )}
            aria-expanded={showAccPanel}
            aria-haspopup="true"
            aria-label="Opciones de accesibilidad"
            title="Accesibilidad: fuente, contraste y voz"
          >
            <Accessibility size={17} />
            <ChevronDown
              size={12}
              className={clsx("transition-transform duration-200", showAccPanel && "rotate-180")}
              aria-hidden
            />
          </button>

        </div>

        {/* Panel de accesibilidad — drawer lateral fijo (no obstruye el contenido) */}
        {showAccPanel && (
          <div
            className="acc-drawer-panel"
            role="dialog"
            aria-label="Panel de accesibilidad"
          >
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-bold text-warm-900 flex items-center gap-2">
                <Accessibility size={15} className="text-terra" aria-hidden />
                Accesibilidad
              </p>
              <button
                onClick={() => setShowAccPanel(false)}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-warm-400 hover:bg-warm-100 hover:text-warm-700 transition-colors"
                aria-label="Cerrar panel"
              >
                ✕
              </button>
            </div>

            {/* Tamaño de fuente */}
            <div className="mb-5">
              <p className="text-xs text-warm-500 font-semibold mb-2 flex items-center gap-1.5 uppercase tracking-wide">
                <Type size={12} aria-hidden />
                Tamaño del texto
              </p>
              <div className="grid grid-cols-3 gap-2">
                {([
                  { key: "normal", label: "Aa", sub: "Normal" },
                  { key: "large",  label: "Aa", sub: "Grande", textSize: "text-lg" },
                  { key: "xlarge", label: "Aa", sub: "Máximo", textSize: "text-xl" },
                ] as const).map(({ key, label, sub, textSize }) => (
                  <button
                    key={key}
                    onClick={() => setFontSize(key as "normal" | "large" | "xlarge")}
                    className={clsx(
                      "flex flex-col items-center py-2.5 rounded-xl border transition-all",
                      fontSize === key
                        ? "bg-terra text-white border-terra shadow-sm"
                        : "bg-warm-50 text-warm-600 border-warm-200 hover:border-terra hover:text-terra"
                    )}
                    aria-pressed={fontSize === key}
                  >
                    <span className={clsx("font-bold leading-none", textSize ?? "text-base")}>{label}</span>
                    <span className="text-2xs mt-1 opacity-80">{sub}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Alto contraste */}
            <div className="flex items-center justify-between py-3 border-t border-warm-100">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-warm-100 flex items-center justify-center shrink-0">
                  <Sun size={15} className="text-warm-600" aria-hidden />
                </div>
                <div>
                  <p className="text-sm font-medium text-warm-900">Alto contraste</p>
                  <p className="text-xs text-warm-400">Mayor legibilidad</p>
                </div>
              </div>
              <button
                onClick={toggleContrast}
                className={clsx("toggle-track", contrast === "high" && "on")}
                aria-pressed={contrast === "high"}
                aria-label="Activar alto contraste"
              >
                <div className="toggle-thumb" />
              </button>
            </div>

            {/* Voz */}
            <div className="flex items-center justify-between py-3 border-t border-warm-100">
              <div className="flex items-center gap-2.5">
                <div className={clsx(
                  "w-8 h-8 rounded-lg flex items-center justify-center shrink-0",
                  voiceEnabled ? "bg-terra-faint" : "bg-warm-100"
                )}>
                  {voiceEnabled
                    ? <Volume2 size={15} className="text-terra" aria-hidden />
                    : <VolumeX size={15} className="text-warm-400" aria-hidden />
                  }
                </div>
                <div>
                  <p className="text-sm font-medium text-warm-900">Leer en voz alta</p>
                  <p className="text-xs text-warm-400">Respuestas por audio</p>
                </div>
              </div>
              <button
                onClick={toggleVoice}
                className={clsx("toggle-track", voiceEnabled && "on")}
                aria-pressed={voiceEnabled}
                aria-label={voiceEnabled ? "Desactivar voz" : "Activar voz"}
              >
                <div className="toggle-thumb" />
              </button>
            </div>

            {/* WCAG badge */}
            <div className="mt-4 flex items-center gap-2 text-xs text-terra bg-terra-faint rounded-xl px-3 py-2.5">
              <CheckCircle size={13} aria-hidden />
              <span className="font-medium">Cumple WCAG 2.2 Nivel AA</span>
            </div>
          </div>
        )}

        {/* Avatar usuario */}
        <div className="relative">
          <button
            onClick={() => { setShowUserMenu((v) => !v); setShowAccPanel(false); }}
            className="w-9 h-9 rounded-full gradient-terra flex items-center justify-center text-white text-sm font-bold hover:opacity-90 transition-opacity"
            aria-expanded={showUserMenu}
            aria-haspopup="true"
            aria-label="Menú de usuario"
            title="Mi cuenta"
          >
            G
          </button>

          {/* Menú de usuario */}
          {showUserMenu && (
            <div
              className="absolute right-0 top-12 w-56 bg-white rounded-2xl border border-warm-100 py-2 z-50 animate-pop"
              style={{ boxShadow: "0 16px 48px rgb(0 0 0 / 0.12)" }}
              role="menu"
              aria-label="Opciones de cuenta"
            >
              {/* Info */}
              <div className="px-4 py-3 border-b border-warm-100">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-full gradient-terra flex items-center justify-center text-white text-sm font-bold shrink-0">
                    G
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-warm-900">Kwesx AI</p>
                    <p className="text-xs text-warm-400">Modo demostración</p>
                  </div>
                </div>
              </div>

              {/* Opciones */}
              {[
                {
                  icon: User,
                  label: "Mi perfil",
                  action: () => setDemoMsg(true),
                },
                {
                  icon: Settings,
                  label: "Accesibilidad",
                  action: () => { setShowAccPanel(true); },
                },
                {
                  icon: HelpCircle,
                  label: "Ayuda",
                  action: () => window.open("https://www.datos.gov.co", "_blank"),
                },
              ].map(({ icon: Icon, label, action }) => (
                <button
                  key={label}
                  onClick={() => { action(); setShowUserMenu(false); }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-warm-700 hover:bg-terra-faint hover:text-terra transition-colors"
                  role="menuitem"
                >
                  <Icon size={15} aria-hidden />
                  {label}
                </button>
              ))}

              {/* Banner modo demo */}
              {demoMsg && (
                <div className="mx-3 mb-2 mt-1 px-3 py-2 bg-terra-faint rounded-xl text-xs text-terra-dark border border-terra-pale">
                  <p className="font-semibold mb-0.5">Modo demostración</p>
                  <p className="text-warm-500">El perfil de usuario estará disponible en la versión final.</p>
                  <button
                    onClick={() => setDemoMsg(false)}
                    className="mt-1 text-2xs underline text-warm-400"
                  >
                    Cerrar
                  </button>
                </div>
              )}

              <div className="border-t border-warm-100 mt-1 pt-1">
                <button
                  onClick={() => setShowUserMenu(false)}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-warm-400 hover:bg-red-50 hover:text-red-500 transition-colors"
                  role="menuitem"
                >
                  <LogOut size={15} aria-hidden />
                  Cerrar sesión
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Overlay para cerrar paneles */}
      {(showAccPanel || showUserMenu) && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => { setShowAccPanel(false); setShowUserMenu(false); }}
          aria-hidden
        />
      )}
    </header>
  );
}
