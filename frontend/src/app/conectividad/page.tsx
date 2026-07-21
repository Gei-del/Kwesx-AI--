"use client";

/**
 * /conectividad — Brecha Digital por Municipio
 * Fuente: DANE ECV + MinTIC
 */

import { useEffect, useState } from "react";
import { Wifi, WifiOff, TrendingUp, TrendingDown, Users, Zap } from "lucide-react";
import { api } from "@/lib/api";
import type { ConectividadRegistro } from "@/lib/api";
import clsx from "clsx";

// ── Helpers ──────────────────────────────────────────────────────────────────

function colorBrecha(pct: number): string {
  if (pct >= 65) return "text-terra";
  if (pct >= 40) return "text-amber";
  return "text-red-500";
}

function badgeBrecha(pct: number): { label: string; cls: string } {
  if (pct >= 65) return { label: "Alta cobertura", cls: "bg-terra-faint text-terra" };
  if (pct >= 40) return { label: "Cobertura media", cls: "bg-amber/10 text-amber-dark" };
  return { label: "Brecha crítica", cls: "bg-red-50 text-red-600" };
}

// ── Offline ───────────────────────────────────────────────────────────────────

function OfflinePage({ msg }: { msg: string }) {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="card border border-warm-200 bg-warm-50 text-center py-12 px-6">
        <div className="w-16 h-16 bg-warm-100 rounded-3xl flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">📡</span>
        </div>
        <h2 className="text-lg font-bold text-warm-900 mb-2">Datos no disponibles por ahora</h2>
        <p className="text-warm-500 text-sm mb-6 max-w-md mx-auto">
          No fue posible conectarse con el servidor de datos de conectividad.
          Verifica que el backend esté activo.
        </p>
        <button onClick={() => window.location.reload()} className="btn-primary mr-3">
          Reintentar
        </button>
        <a
          href="https://www.datos.gov.co"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-ghost text-sm"
        >
          Ver fuente oficial
        </a>
        <p className="text-xs text-warm-300 mt-4 hidden">{msg}</p>
      </div>
    </div>
  );
}

// ── Shimmer ───────────────────────────────────────────────────────────────────

function Shimmer() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="card p-5 space-y-3">
          <div className="shimmer-line h-4 w-3/4" />
          <div className="shimmer-line h-8 w-1/2" />
          <div className="shimmer-line h-3 w-full" />
          <div className="shimmer-line h-3 w-5/6" />
        </div>
      ))}
    </div>
  );
}

// ── Tarjeta municipio ─────────────────────────────────────────────────────────

function MunicipioCard({ r }: { r: ConectividadRegistro }) {
  const badge = badgeBrecha(r.pct_hogares_internet);
  return (
    <div className="card p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-warm-900 text-sm">{r.municipio}</h3>
          <p className="text-xs text-warm-400">{r.departamento} · {r.anio}</p>
        </div>
        <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full", badge.cls)}>
          {badge.label}
        </span>
      </div>

      {/* Barra principal: internet */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-warm-500 flex items-center gap-1">
            <Wifi size={11} /> Internet
          </span>
          <span className={clsx("text-xl font-bold", colorBrecha(r.pct_hogares_internet))}>
            {r.pct_hogares_internet?.toFixed(1)}%
          </span>
        </div>
        <div className="h-2 bg-warm-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${r.pct_hogares_internet || 0}%`,
              background: r.pct_hogares_internet >= 65
                ? "var(--color-terra)"
                : r.pct_hogares_internet >= 40
                  ? "var(--color-amber)"
                  : "#ef4444",
            }}
          />
        </div>
      </div>

      {/* Métricas secundarias */}
      <div className="grid grid-cols-2 gap-2 text-xs text-warm-600">
        {r.pct_hogares_celular != null && (
          <div className="flex items-center gap-1">
            <span className="text-warm-400">📱</span>
            <span>Celular {r.pct_hogares_celular.toFixed(0)}%</span>
          </div>
        )}
        {r.pct_hogares_pc != null && (
          <div className="flex items-center gap-1">
            <span className="text-warm-400">💻</span>
            <span>PC/tablet {r.pct_hogares_pc.toFixed(0)}%</span>
          </div>
        )}
        {r.tipo_conexion && (
          <div className="flex items-center gap-1">
            <span className="text-warm-400">🔌</span>
            <span className="capitalize">{r.tipo_conexion}</span>
          </div>
        )}
        {r.zona && (
          <div className="flex items-center gap-1">
            <span className="text-warm-400">📍</span>
            <span className="capitalize">{r.zona}</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Página principal ──────────────────────────────────────────────────────────

export default function ConectividadPage() {
  const [datos, setDatos] = useState<ConectividadRegistro[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filtroZona, setFiltroZona] = useState<"" | "urbana" | "rural">("");
  const [busqueda, setBusqueda] = useState("");

  useEffect(() => {
    api.conectividad({ anio: 2023 })
      .then((r) => setDatos(r.datos))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 max-w-7xl mx-auto"><Shimmer /></div>;
  if (error)   return <div className="p-6"><OfflinePage msg={error} /></div>;

  // Filtros locales
  const filtrados = datos.filter((r) => {
    const matchZona = !filtroZona || r.zona === filtroZona;
    const matchBusq = !busqueda || r.municipio.toLowerCase().includes(busqueda.toLowerCase())
      || r.departamento.toLowerCase().includes(busqueda.toLowerCase());
    return matchZona && matchBusq;
  });

  // Estadísticas resumen
  const conInternet = filtrados.filter((r) => r.zona === "urbana" || !r.zona);
  const promInternet = conInternet.length
    ? conInternet.reduce((s, r) => s + (r.pct_hogares_internet || 0), 0) / conInternet.length
    : 0;

  const urbanos = datos.filter((r) => r.zona === "urbana");
  const rurales = datos.filter((r) => r.zona === "rural");
  const promUrbano = urbanos.length ? urbanos.reduce((s, r) => s + (r.pct_hogares_internet || 0), 0) / urbanos.length : 0;
  const promRural  = rurales.length ? rurales.reduce((s, r) => s + (r.pct_hogares_internet || 0), 0) / rurales.length : 0;
  const brecha = promUrbano - promRural;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <div className="card gradient-terra text-white p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-white/15 rounded-xl flex items-center justify-center">
            <Wifi size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold">Brecha Digital en Colombia</h1>
            <p className="text-sm text-white/70">Hogares con acceso a internet por municipio · DANE ECV + MinTIC</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatHero label="Prom. Nacional" value={`${promInternet.toFixed(1)}%`} sub="con internet" />
          <StatHero label="Zona Urbana" value={`${promUrbano.toFixed(1)}%`} sub="hogares" />
          <StatHero label="Zona Rural" value={`${promRural.toFixed(1)}%`} sub="hogares" />
          <StatHero label="Brecha U-R" value={`${brecha.toFixed(1)} pp`} sub="puntos porcentuales" warn={brecha > 25} />
        </div>
      </div>

      {/* ── Filtros ───────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          placeholder="Buscar municipio o departamento..."
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          className="flex-1 px-4 py-2.5 text-sm rounded-xl border border-warm-200 bg-white focus:outline-none focus:border-terra focus:ring-2 focus:ring-terra/20 text-warm-800"
        />
        <div className="flex gap-2">
          {(["", "urbana", "rural"] as const).map((z) => (
            <button
              key={z}
              onClick={() => setFiltroZona(z)}
              className={clsx(
                "px-4 py-2.5 text-sm rounded-xl border transition-colors font-medium",
                filtroZona === z
                  ? "bg-terra text-white border-terra"
                  : "bg-white text-warm-600 border-warm-200 hover:border-terra hover:text-terra"
              )}
            >
              {z === "" ? "Todas" : z.charAt(0).toUpperCase() + z.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* ── Grid municipios ───────────────────────────────────────────────── */}
      <div>
        <p className="text-xs text-warm-400 mb-3">
          Mostrando {filtrados.length} de {datos.length} registros
        </p>
        {filtrados.length === 0 ? (
          <div className="card text-center py-10 text-warm-400">
            <WifiOff size={32} className="mx-auto mb-2 opacity-40" />
            <p>No hay resultados para tu búsqueda.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtrados.map((r) => <MunicipioCard key={`${r.codigo_dane}-${r.zona}`} r={r} />)}
          </div>
        )}
      </div>

      {/* ── Fuente ────────────────────────────────────────────────────────── */}
      <p className="text-xs text-warm-300 text-center">
        Fuente: DANE Encuesta de Calidad de Vida 2023 + MinTIC Índice de Penetración.
        Los municipios marcados como "SIMULADO" usan promedios departamentales de referencia.
      </p>
    </div>
  );
}

function StatHero({ label, value, sub, warn }: { label: string; value: string; sub: string; warn?: boolean }) {
  return (
    <div className="bg-white/10 rounded-xl px-4 py-3">
      <p className="text-xs text-white/60 mb-0.5">{label}</p>
      <p className={clsx("text-2xl font-bold", warn ? "text-red-300" : "text-white")}>{value}</p>
      <p className="text-xs text-white/50">{sub}</p>
    </div>
  );
}
