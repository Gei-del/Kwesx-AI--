"use client";

/**
 * Sidebar — Navegación principal de Kwesx AI
 *
 * Lenguaje humano, sin jerga técnica.
 * Modo Fácil oculta secciones avanzadas.
 * Accesible con teclado y lector de pantalla.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home, MessageCircle, Sprout, Route, CloudSun, MapPin, Zap, Sparkles,
  Wifi, GraduationCap, ShieldAlert, Map
} from "lucide-react";
import clsx from "clsx";
import { useApp } from "@/contexts/AppContext";

// ─── Navegación ───────────────────────────────────────────────────────────────

const NAV_MAIN = [
  {
    href:  "/",
    icon:  Home,
    label: "Inicio",
    sub:   "Resumen de tu territorio",
    emoji: "🏠",
  },
  {
    href:  "/asistente",
    icon:  MessageCircle,
    label: "Pregúntale a Kwesx",
    sub:   "Habla o escribe tu pregunta",
    emoji: "💬",
    highlight: true,
  },
];

const NAV_DATOS = [
  {
    href:   "/datos/upra",
    icon:   Sprout,
    label:  "Precios del Campo",
    sub:    "Fertilizantes, cultivos, insumos",
    emoji:  "🌱",
  },
  {
    href:   "/datos/ani",
    icon:   Route,
    label:  "Estado de las Vías",
    sub:    "Tráfico y peajes nacionales",
    emoji:  "🛣️",
  },
  {
    href:   "/datos/ideam",
    icon:   CloudSun,
    label:  "El Tiempo",
    sub:    "Lluvia y temperatura",
    emoji:  "🌦️",
  },
];

const NAV_SOCIAL = [
  {
    href:  "/conectividad",
    icon:  Wifi,
    label: "Brecha Digital",
    sub:   "Internet por municipio · MinTIC",
    emoji: "📶",
  },
  {
    href:  "/educacion",
    icon:  GraduationCap,
    label: "Educación",
    sub:   "Cobertura escolar · MEN",
    emoji: "🎓",
  },
];

const NAV_AVANZADO = [
  {
    href:  "/prediccion",
    icon:  MapPin,
    label: "Calidad de Vida",
    sub:   "Vulnerabilidad territorial (IVT)",
    emoji: "🏘️",
  },
  {
    href:  "/riesgos",
    icon:  ShieldAlert,
    label: "Alertas de Riesgo",
    sub:   "Anomalías detectadas por IA",
    emoji: "⚠️",
  },
  {
    href:  "/insights",
    icon:  Sparkles,
    label: "Insights de IA",
    sub:   "Ensemble · Clustering · Forecasting · XAI",
    emoji: "🤖",
  },
];

// ─── Componente ───────────────────────────────────────────────────────────────

export default function Sidebar() {
  const pathname = usePathname();
  const { mode, toggleMode, mobileNavOpen, closeMobileNav } = useApp();
  const isEasy = mode === "easy";

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  // Cerrar sidebar móvil al navegar
  const handleNavClick = () => {
    if (mobileNavOpen) closeMobileNav();
  };

  return (
    <>
      {/* Overlay oscuro en móvil */}
      {mobileNavOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 lg:hidden"
          onClick={closeMobileNav}
          aria-hidden
        />
      )}

    <aside
      className={[
        "flex flex-col shrink-0 gradient-terra",
        // Desktop: siempre visible
        "lg:relative lg:translate-x-0 lg:w-64",
        // Móvil: drawer fixed que entra desde la izquierda
        "fixed inset-y-0 left-0 w-72 z-50 transition-transform duration-300 ease-spring",
        mobileNavOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
      ].join(" ")}
      aria-label="Navegación principal"
      role="navigation"
    >
      {/* ── Logo ───────────────────────────────────────────────────────── */}
      <div className="px-5 py-6 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center">
            <Zap size={18} className="text-amber" fill="currentColor" />
          </div>
          <div>
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-bold text-white tracking-tight">Kwesx</span>
              <span className="text-xl font-bold text-amber-light tracking-tight">AI</span>
            </div>
            <p className="text-2xs text-white/50 leading-none">Tu Territorio Inteligente</p>
          </div>
        </div>
      </div>

      {/* ── Navegación ─────────────────────────────────────────────────── */}
      <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">

        {/* Principal */}
        {NAV_MAIN.map((item) => (
          <NavItem key={item.href} item={item} active={isActive(item.href)} isEasy={isEasy} onClick={handleNavClick} />
        ))}

        {/* Separador datos */}
        <div className="pt-3 pb-1 px-2">
          <p className="text-2xs font-semibold uppercase tracking-widest text-white/35">
            Información
          </p>
        </div>

        {NAV_DATOS.map((item) => (
          <NavItem key={item.href} item={item} active={isActive(item.href)} isEasy={isEasy} onClick={handleNavClick} />
        ))}

        {/* Social / Brecha digital */}
        <div className="advanced-feature">
          <div className="pt-3 pb-1 px-2">
            <p className="text-2xs font-semibold uppercase tracking-widest text-white/35">
              Social
            </p>
          </div>
          {NAV_SOCIAL.map((item) => (
            <NavItem key={item.href} item={item} active={isActive(item.href)} isEasy={isEasy} onClick={handleNavClick} />
          ))}
        </div>

        {/* Avanzado — oculto en Modo Fácil */}
        <div className="advanced-feature">
          <div className="pt-3 pb-1 px-2">
            <p className="text-2xs font-semibold uppercase tracking-widest text-white/35">
              Análisis IA
            </p>
          </div>
          {NAV_AVANZADO.map((item) => (
            <NavItem key={item.href} item={item} active={isActive(item.href)} isEasy={isEasy} onClick={handleNavClick} />
          ))}
        </div>
      </div>

      {/* ── Modo Fácil ─────────────────────────────────────────────────── */}
      <div className="px-4 py-4 border-t border-white/10">
        <button
          onClick={toggleMode}
          className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-white/10 transition-colors group"
          aria-pressed={isEasy}
          aria-label={isEasy ? "Desactivar Modo Fácil" : "Activar Modo Fácil"}
        >
          <div className="flex items-center gap-2.5">
            <span className="text-lg" aria-hidden>🌟</span>
            <div className="text-left">
              <p className="text-sm font-semibold text-white">Modo Fácil</p>
              <p className="text-2xs text-white/50">
                {isEasy ? "Activo" : "Simplifica la interfaz"}
              </p>
            </div>
          </div>
          {/* Toggle */}
          <div
            className={clsx(
              "toggle-track",
              isEasy && "on"
            )}
            aria-hidden
          >
            <div className="toggle-thumb" />
          </div>
        </button>

        {/* Info del concurso */}
        <p className="text-2xs text-white/30 text-center mt-3 leading-relaxed">
          Concurso Datos al Ecosistema 2026
        </p>
      </div>
    </aside>
    </>
  );
}

// ─── NavItem ──────────────────────────────────────────────────────────────────

interface NavItemProps {
  item: {
    href:      string;
    icon:      React.ElementType;
    label:     string;
    sub:       string;
    emoji:     string;
    highlight?: boolean;
  };
  active:  boolean;
  isEasy:  boolean;
  onClick: () => void;
}

function NavItem({ item, active, isEasy, onClick }: NavItemProps) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      onClick={onClick}
      className={clsx(
        "sidebar-item group",
        active && "active",
        item.highlight && !active && "bg-white/8"
      )}
      aria-current={active ? "page" : undefined}
    >
      {/* Emoji grande en Modo Fácil, ícono normal en modo estándar */}
      {isEasy ? (
        <span className="text-2xl w-8 text-center shrink-0" aria-hidden>{item.emoji}</span>
      ) : (
        <Icon
          size={18}
          className={clsx(
            "shrink-0 transition-colors",
            active ? "text-amber-light" : "text-white/60 group-hover:text-white"
          )}
          aria-hidden
        />
      )}

      <div className="flex-1 min-w-0">
        <p className={clsx(
          "font-semibold leading-tight truncate",
          active ? "text-white" : "text-white/80"
        )}>
          {item.label}
        </p>
        {!isEasy && (
          <p className="text-2xs text-white/40 truncate leading-tight mt-0.5">
            {item.sub}
          </p>
        )}
      </div>

      {active && (
        <div className="w-1.5 h-1.5 rounded-full bg-amber-light shrink-0" aria-hidden />
      )}
    </Link>
  );
}
