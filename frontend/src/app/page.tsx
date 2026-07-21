"use client";

/**
 * Dashboard Principal — "Hoy en tu territorio"
 *
 * Diseñado para cualquier persona, desde campesinos hasta investigadores.
 * El usuario nunca debe sentir que está consultando bases de datos.
 * Debe sentir que está hablando con un experto que conoce su territorio.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  CloudRain, Sprout, Route, MapPin, ArrowRight, TrendingUp, TrendingDown,
  Minus, AlertCircle, CheckCircle, MessageCircle
} from "lucide-react";

import { api, ResumenMTU, IVTResultado, UPRARegistro, IDEAMRegistro } from "@/lib/api";
import { useApp } from "@/contexts/AppContext";

// Mapa con SSR desactivado
const ColombiaMap = dynamic(() => import("@/components/map/ColombiaMap"), {
  ssr: false,
  loading: () => <div className="skeleton h-full rounded-2xl" />,
});

// ─── Preguntas frecuentes ─────────────────────────────────────────────────────

const PREGUNTAS = [
  { emoji: "🌧️", texto: "¿Va a llover hoy?",                href: "/asistente", color: "sky" },
  { emoji: "🚜", texto: "¿Cómo están los cultivos?",         href: "/asistente", color: "terra" },
  { emoji: "🛣️", texto: "¿Hay cierres viales?",             href: "/datos/ani",  color: "amber" },
  { emoji: "🌱", texto: "¿Qué insumos subieron de precio?",  href: "/datos/upra", color: "terra" },
  { emoji: "⚠️", texto: "¿Hay alertas en mi zona?",          href: "/asistente", color: "danger" },
  { emoji: "🏘️", texto: "¿Cómo está mi municipio?",         href: "/prediccion", color: "terra" },
];

// ─── Página ───────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { speak } = useApp();

  const [resumen, setResumen] = useState<ResumenMTU | null>(null);
  const [ivt,     setIVT]     = useState<IVTResultado | null>(null);
  const [upra,    setUPRA]    = useState<UPRARegistro[]>([]);
  const [ideam,   setIDEAM]   = useState<IDEAMRegistro[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.resumen(),
      api.ivtActual(),
      api.upraTendencia(),
      api.ideam({ limit: 500, dias: 7 }),
    ]).then(([resR, ivtR, upraR, ideamR]) => {
      if (resR.status  === "fulfilled") setResumen(resR.value);
      if (ivtR.status  === "fulfilled") setIVT(ivtR.value);
      if (upraR.status === "fulfilled") setUPRA(upraR.value.datos);
      if (ideamR.status=== "fulfilled") setIDEAM(ideamR.value.datos);
      setLoading(false);
    });
  }, []);

  // Datos derivados
  const ultimo      = upra[upra.length - 1];
  const penultimo   = upra[upra.length - 2];
  const varMensual  = ultimo?.variacion_mensual_pct ?? 0;
  const ivtEtiqueta = ivt?.ivt?.etiqueta ?? null;

  const totalRegistros = resumen
    ? resumen.mtu.ani.registros + resumen.mtu.upra.registros + resumen.mtu.ideam.registros
    : 0;

  // Texto de insight proactivo para voz
  useEffect(() => {
    if (!loading && ivtEtiqueta) {
      speak(
        `Hola. El índice de calidad de vida territorial está en nivel ${ivtEtiqueta}. ` +
        (varMensual > 0
          ? `Los precios del campo subieron ${Math.abs(varMensual).toFixed(1)}% este mes.`
          : varMensual < 0
          ? `Los precios del campo bajaron ${Math.abs(varMensual).toFixed(1)}% este mes.`
          : "Los precios del campo están estables este mes.")
      );
    }
  }, [loading, ivtEtiqueta, varMensual, speak]);

  return (
    <div className="space-y-8">

      {/* ── Hero de bienvenida ────────────────────────────────────────────── */}
      <div className="gradient-terra rounded-3xl p-6 md:p-8 text-white relative overflow-hidden animate-fade-in">
        {/* Decoración de fondo */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-32 translate-x-32" aria-hidden />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-24 -translate-x-24" aria-hidden />

        <div className="relative">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <p className="text-white/70 text-sm font-medium mb-1">
                🌎 Hoy en tu territorio
              </p>
              <h2 className="text-2xl md:text-3xl font-bold text-white leading-tight">
                {loading ? "Analizando el territorio..." : "¿Qué está pasando cerca de ti?"}
              </h2>
              <p className="text-white/65 mt-2 text-sm max-w-lg">
                Kwesx AI cruza información oficial de clima, carreteras y precios del campo
                para darte una visión clara de tu territorio.
              </p>
            </div>

            {/* IVT badge en el hero */}
            {!loading && ivt?.modelo_disponible && ivtEtiqueta && (
              <div className="animate-pop">
                <IVTHeroBadge etiqueta={ivtEtiqueta} />
              </div>
            )}
          </div>

          {/* Link a asistente */}
          <Link
            href="/asistente"
            className="mt-5 inline-flex items-center gap-2 bg-white text-terra font-bold px-5 py-3 rounded-xl hover:bg-amber-pale transition-all shadow-card-md"
          >
            <MessageCircle size={18} aria-hidden />
            Hazle una pregunta a Kwesx
            <ArrowRight size={16} aria-hidden />
          </Link>
        </div>
      </div>

      {/* ── Preguntas frecuentes ──────────────────────────────────────────── */}
      <section aria-labelledby="preguntas-heading">
        <h2 id="preguntas-heading" className="text-base font-bold text-warm-800 mb-4">
          Preguntas frecuentes
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {PREGUNTAS.map((p, i) => (
            <Link
              key={p.texto}
              href={p.href}
              className={`question-chip animate-fade-in`}
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <span className="text-xl shrink-0" aria-hidden>{p.emoji}</span>
              <span className="leading-tight">{p.texto}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* ── Insights proactivos ───────────────────────────────────────────── */}
      <section aria-labelledby="insights-heading">
        <h2 id="insights-heading" className="text-base font-bold text-warm-800 mb-4">
          Resumen de hoy
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

          {/* Clima */}
          <InsightCard
            loading={loading}
            emoji="🌦️"
            titulo="El Tiempo"
            href="/datos/ideam"
            delay={0}
          >
            {ideam.length > 0 ? (
              <>
                <p className="text-sm text-warm-700">
                  Se registraron mediciones en{" "}
                  <strong>{new Set(ideam.map((d) => d.departamento).filter(Boolean)).size} departamentos</strong>{" "}
                  esta semana.
                </p>
                <p className="text-xs text-warm-500 mt-1">
                  {ideam.length} mediciones · Precipitación y temperatura
                </p>
              </>
            ) : (
              <p className="text-sm text-warm-500">Sin datos recientes. Ejecuta el ETL para activar.</p>
            )}
          </InsightCard>

          {/* Precios del campo */}
          <InsightCard
            loading={loading}
            emoji="🌱"
            titulo="Precios del Campo"
            href="/datos/upra"
            delay={100}
          >
            {ultimo ? (
              <>
                <p className="text-sm text-warm-700">
                  El índice de insumos agrícolas es{" "}
                  <strong>{ultimo.indice_total?.toFixed(1)}</strong>.
                </p>
                <div className="flex items-center gap-1.5 mt-1">
                  {varMensual > 0.5 ? (
                    <><TrendingUp size={13} className="text-red-500" aria-hidden />
                      <span className="text-xs text-red-600 font-medium">Subió {varMensual.toFixed(1)}% este mes</span></>
                  ) : varMensual < -0.5 ? (
                    <><TrendingDown size={13} className="text-emerald-600" aria-hidden />
                      <span className="text-xs text-emerald-600 font-medium">Bajó {Math.abs(varMensual).toFixed(1)}% este mes</span></>
                  ) : (
                    <><Minus size={13} className="text-warm-400" aria-hidden />
                      <span className="text-xs text-warm-500">Estable este mes</span></>
                  )}
                </div>
              </>
            ) : (
              <p className="text-sm text-warm-500">Sin datos. Ejecuta el ETL para activar.</p>
            )}
          </InsightCard>

          {/* Estado de las vías */}
          <InsightCard
            loading={loading}
            emoji="🛣️"
            titulo="Estado de las Vías"
            href="/datos/ani"
            delay={200}
          >
            {resumen?.mtu.ani.registros ? (
              <>
                <p className="text-sm text-warm-700">
                  Hay <strong>{resumen.mtu.ani.registros.toLocaleString("es-CO")}</strong> registros
                  de tráfico en peajes disponibles.
                </p>
                <p className="text-xs text-warm-500 mt-1">
                  Red vial concesionada nacional
                </p>
              </>
            ) : (
              <p className="text-sm text-warm-500">Sin datos de vías. Ejecuta el ETL para activar.</p>
            )}
          </InsightCard>
        </div>
      </section>

      {/* ── Mapa territorial ─────────────────────────────────────────────── */}
      {ideam.some((d) => d.latitud && d.longitud) && (
        <section aria-labelledby="mapa-heading" className="animate-fade-in">
          <div className="card p-0 overflow-hidden">
            <div className="px-6 py-4 border-b border-warm-100 flex items-center justify-between">
              <h2 id="mapa-heading" className="font-bold text-warm-900 flex items-center gap-2">
                <MapPin size={18} className="text-terra" aria-hidden />
                Tu territorio en el mapa
              </h2>
              <Link href="/datos/ideam" className="text-xs text-terra font-medium hover:underline flex items-center gap-1">
                Ver más <ArrowRight size={12} aria-hidden />
              </Link>
            </div>
            <div style={{ height: "380px" }}>
              <ColombiaMap puntos={ideam.filter((d) => d.latitud && d.longitud)} />
            </div>
            <div className="px-6 py-3 bg-warm-50 border-t border-warm-100 flex items-center justify-between">
              <div className="flex items-center gap-4 text-xs text-warm-500">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-terra inline-block" aria-hidden />
                  Precipitación
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-amber inline-block" aria-hidden />
                  Temperatura
                </span>
              </div>
              <p className="text-xs text-warm-400">
                {ideam.filter((d) => d.latitud && d.longitud).length} estaciones activas
              </p>
            </div>
          </div>
        </section>
      )}

      {/* ── Estado del sistema ────────────────────────────────────────────── */}
      {!loading && (
        <section aria-labelledby="sistema-heading" className="advanced-feature animate-fade-in">
          <h2 id="sistema-heading" className="text-sm font-bold text-warm-600 uppercase tracking-wide mb-3">
            Estado del sistema
          </h2>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Precios del Campo",  ok: (resumen?.mtu.upra.registros ?? 0) > 0,  count: resumen?.mtu.upra.registros,  icon: Sprout },
              { label: "Estado de las Vías", ok: (resumen?.mtu.ani.registros  ?? 0) > 0,  count: resumen?.mtu.ani.registros,   icon: Route  },
              { label: "El Tiempo",          ok: (resumen?.mtu.ideam.registros ?? 0) > 0, count: resumen?.mtu.ideam.registros,  icon: CloudRain },
            ].map(({ label, ok, count, icon: Icon }) => (
              <div
                key={label}
                className={`flex items-center gap-3 p-3 rounded-2xl border transition-all ${
                  ok ? "bg-terra-faint border-terra-pale" : "bg-warm-50 border-warm-200"
                }`}
              >
                {ok
                  ? <CheckCircle size={16} className="text-terra shrink-0" aria-hidden />
                  : <AlertCircle size={16} className="text-amber-dark shrink-0" aria-hidden />
                }
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-warm-800 truncate">{label}</p>
                  <p className="text-2xs text-warm-500">
                    {ok ? `${count?.toLocaleString("es-CO")} registros` : "Ejecutar ETL"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// ─── Sub-componentes ──────────────────────────────────────────────────────────

function InsightCard({
  loading, emoji, titulo, href, delay, children
}: {
  loading: boolean;
  emoji:   string;
  titulo:  string;
  href:    string;
  delay:   number;
  children?: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="insight-card flex flex-col group animate-fade-in"
      style={{ animationDelay: `${delay}ms` }}
      aria-label={`Ver más sobre ${titulo}`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl" aria-hidden>{emoji}</span>
          <p className="text-sm font-bold text-warm-800">{titulo}</p>
        </div>
        <ArrowRight
          size={14}
          className="text-warm-300 group-hover:text-terra transition-colors group-hover:translate-x-0.5"
          aria-hidden
        />
      </div>

      {loading ? (
        <div className="space-y-2">
          <div className="skeleton h-4 w-3/4" />
          <div className="skeleton h-3 w-1/2" />
        </div>
      ) : (
        <div className="flex-1">{children}</div>
      )}
    </Link>
  );
}

function IVTHeroBadge({ etiqueta }: { etiqueta: string }) {
  const config: Record<string, { label: string; color: string; emoji: string }> = {
    BAJA:  { label: "Buenas condiciones",  color: "bg-emerald-100 text-emerald-800 border-emerald-200", emoji: "✅" },
    MEDIA: { label: "Atención moderada",   color: "bg-amber-pale text-amber-dark border-amber-pale",    emoji: "⚠️" },
    ALTA:  { label: "Alerta territorial",  color: "bg-red-100 text-red-800 border-red-200",             emoji: "🚨" },
  };
  const c = config[etiqueta] ?? config.MEDIA;

  return (
    <div
      className={`flex flex-col items-center px-5 py-3 rounded-2xl border-2 ${c.color}`}
      role="status"
      aria-label={`Calidad de vida en tu zona: ${c.label}`}
    >
      <span className="text-3xl mb-1" aria-hidden>{c.emoji}</span>
      <p className="text-xs font-bold uppercase tracking-wide">{c.label}</p>
      <p className="text-2xs opacity-70 mt-0.5">Calidad de vida territorial</p>
    </div>
  );
}
