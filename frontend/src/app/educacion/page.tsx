"use client";

/**
 * /educacion — Cobertura Educativa por Municipio
 * Fuente: MEN — SIMAT
 */

import { useEffect, useState } from "react";
import { GraduationCap, BookOpen, Users, TrendingDown, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import type { EducacionRegistro } from "@/lib/api";
import clsx from "clsx";

// ── Constantes ────────────────────────────────────────────────────────────────

const NIVELES = ["preescolar", "primaria", "secundaria", "media"] as const;
type Nivel = typeof NIVELES[number];

const NIVEL_CONFIG: Record<Nivel, { emoji: string; color: string }> = {
  preescolar:  { emoji: "🧸", color: "bg-sky-100 text-sky-700" },
  primaria:    { emoji: "📚", color: "bg-terra-faint text-terra" },
  secundaria:  { emoji: "✏️",  color: "bg-amber/10 text-amber-dark" },
  media:       { emoji: "🎓", color: "bg-purple-50 text-purple-700" },
};

// ── Offline ───────────────────────────────────────────────────────────────────

function OfflinePage({ msg }: { msg: string }) {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="card border border-warm-200 bg-warm-50 text-center py-12 px-6">
        <div className="w-16 h-16 bg-warm-100 rounded-3xl flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">📚</span>
        </div>
        <h2 className="text-lg font-bold text-warm-900 mb-2">Datos educativos no disponibles</h2>
        <p className="text-warm-500 text-sm mb-6 max-w-md mx-auto">
          No fue posible conectarse con el servidor. Verifica que el backend esté activo.
        </p>
        <button onClick={() => window.location.reload()} className="btn-primary mr-3">
          Reintentar
        </button>
        <a
          href="https://www.mineducacion.gov.co"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-ghost text-sm"
        >
          Ver MEN oficial
        </a>
        <p className="text-xs text-warm-300 mt-4 hidden">{msg}</p>
      </div>
    </div>
  );
}

// ── Shimmer ───────────────────────────────────────────────────────────────────

function Shimmer() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="card p-5 space-y-3">
          <div className="shimmer-line h-4 w-1/3" />
          <div className="grid grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, j) => (
              <div key={j} className="shimmer-line h-16 rounded-xl" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Barra de cobertura ────────────────────────────────────────────────────────

function CoberturaBar({ value, max = 100, nivel }: { value: number; max?: number; nivel: Nivel }) {
  const pct = Math.min(100, (value / max) * 100);
  const colors: Record<Nivel, string> = {
    preescolar:  "#0ea5e9",
    primaria:    "var(--color-terra)",
    secundaria:  "var(--color-amber)",
    media:       "#a855f7",
  };
  return (
    <div className="h-1.5 bg-warm-100 rounded-full overflow-hidden mt-1">
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{ width: `${pct}%`, background: colors[nivel] }}
      />
    </div>
  );
}

// ── Grupo por municipio ───────────────────────────────────────────────────────

interface MunicipioGroup {
  codigo_dane: string;
  municipio:   string;
  departamento: string;
  anio:        number;
  niveles:     Record<string, EducacionRegistro>;
}

function agruparPorMunicipio(datos: EducacionRegistro[]): MunicipioGroup[] {
  const map = new Map<string, MunicipioGroup>();
  for (const r of datos) {
    const key = `${r.codigo_dane}-${r.anio}`;
    if (!map.has(key)) {
      map.set(key, {
        codigo_dane:  r.codigo_dane,
        municipio:    r.municipio,
        departamento: r.departamento,
        anio:         r.anio,
        niveles:      {},
      });
    }
    map.get(key)!.niveles[r.nivel_educativo] = r;
  }
  return Array.from(map.values());
}

// ── Tarjeta municipio ─────────────────────────────────────────────────────────

function MunicipioCard({ grupo }: { grupo: MunicipioGroup }) {
  const primaria = grupo.niveles["primaria"];
  const alertaDesercion = Object.values(grupo.niveles).some(
    (r) => r.tasa_desercion != null && r.tasa_desercion > 6
  );

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-semibold text-warm-900">{grupo.municipio}</h3>
          <p className="text-xs text-warm-400">{grupo.departamento} · {grupo.anio}</p>
        </div>
        {alertaDesercion && (
          <div className="flex items-center gap-1 text-xs text-red-500 bg-red-50 px-2 py-0.5 rounded-full">
            <AlertCircle size={11} />
            Alta deserción
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {NIVELES.map((nivel) => {
          const r = grupo.niveles[nivel];
          const cfg = NIVEL_CONFIG[nivel];
          if (!r) return (
            <div key={nivel} className="rounded-xl bg-warm-50 p-3 opacity-40">
              <span className="text-lg">{cfg.emoji}</span>
              <p className="text-xs text-warm-400 capitalize mt-1">{nivel}</p>
              <p className="text-xs text-warm-300">Sin datos</p>
            </div>
          );
          return (
            <div key={nivel} className="rounded-xl bg-warm-50 p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-base">{cfg.emoji}</span>
                <span className={clsx("text-2xs font-semibold px-1.5 py-0.5 rounded-full", cfg.color)}>
                  {nivel}
                </span>
              </div>
              <p className="text-lg font-bold text-warm-900">
                {r.tasa_cobertura_neta?.toFixed(0) ?? "—"}%
              </p>
              <p className="text-2xs text-warm-400">cobertura neta</p>
              {r.tasa_cobertura_neta != null && (
                <CoberturaBar value={r.tasa_cobertura_neta} nivel={nivel} />
              )}
              {r.tasa_desercion != null && (
                <p className={clsx(
                  "text-2xs mt-1.5",
                  r.tasa_desercion > 6 ? "text-red-500 font-medium" : "text-warm-400"
                )}>
                  ↓ {r.tasa_desercion.toFixed(1)}% deserción
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Totales */}
      {primaria && (
        <div className="mt-3 pt-3 border-t border-warm-100 flex items-center gap-4 text-xs text-warm-500">
          <div className="flex items-center gap-1">
            <Users size={11} />
            <span>{primaria.matriculados?.toLocaleString("es-CO")} matriculados (primaria)</span>
          </div>
          {primaria.tasa_aprobacion != null && (
            <div className="flex items-center gap-1">
              <BookOpen size={11} />
              <span>{primaria.tasa_aprobacion.toFixed(0)}% aprobación</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Página principal ──────────────────────────────────────────────────────────

export default function EducacionPage() {
  const [datos, setDatos] = useState<EducacionRegistro[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [filtroNivel, setFiltroNivel] = useState<"" | Nivel>("");

  useEffect(() => {
    api.educacion()
      .then((r) => setDatos(r.datos))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 max-w-7xl mx-auto"><Shimmer /></div>;
  if (error)   return <div className="p-6"><OfflinePage msg={error} /></div>;

  // Estadísticas nacionales
  const promPorNivel = (nivel: string) => {
    const fil = datos.filter((r) => r.nivel_educativo === nivel && r.tasa_cobertura_neta != null);
    return fil.length ? fil.reduce((s, r) => s + r.tasa_cobertura_neta!, 0) / fil.length : 0;
  };

  // Filtros
  const datosFiltrados = datos.filter((r) => {
    const matchNivel = !filtroNivel || r.nivel_educativo === filtroNivel;
    const matchBusq  = !busqueda
      || r.municipio?.toLowerCase().includes(busqueda.toLowerCase())
      || r.departamento?.toLowerCase().includes(busqueda.toLowerCase());
    return matchNivel && matchBusq;
  });

  const grupos = agruparPorMunicipio(datosFiltrados);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <div className="card gradient-terra text-white p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-white/15 rounded-xl flex items-center justify-center">
            <GraduationCap size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold">Cobertura Educativa Colombia</h1>
            <p className="text-sm text-white/70">Tasas de matrícula por nivel y municipio · MEN — SIMAT {new Date().getFullYear() - 1}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {NIVELES.map((n) => (
            <div key={n} className="bg-white/10 rounded-xl px-4 py-3">
              <p className="text-xs text-white/60 mb-0.5 capitalize">{n}</p>
              <p className="text-2xl font-bold">{promPorNivel(n).toFixed(0)}%</p>
              <p className="text-xs text-white/50">cobertura neta prom.</p>
            </div>
          ))}
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
        <div className="flex gap-2 flex-wrap">
          {(["", ...NIVELES] as const).map((n) => (
            <button
              key={n}
              onClick={() => setFiltroNivel(n as "" | Nivel)}
              className={clsx(
                "px-3 py-2 text-xs rounded-xl border transition-colors font-medium capitalize",
                filtroNivel === n
                  ? "bg-terra text-white border-terra"
                  : "bg-white text-warm-600 border-warm-200 hover:border-terra hover:text-terra"
              )}
            >
              {n || "Todos"}
            </button>
          ))}
        </div>
      </div>

      {/* ── Lista municipios ──────────────────────────────────────────────── */}
      <div>
        <p className="text-xs text-warm-400 mb-3">{grupos.length} municipios</p>
        <div className="space-y-4">
          {grupos.map((g) => (
            <MunicipioCard key={`${g.codigo_dane}-${g.anio}`} grupo={g} />
          ))}
          {grupos.length === 0 && (
            <div className="card text-center py-10 text-warm-400">
              <GraduationCap size={32} className="mx-auto mb-2 opacity-40" />
              <p>No hay resultados para tu búsqueda.</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Fuente ────────────────────────────────────────────────────────── */}
      <p className="text-xs text-warm-300 text-center">
        Fuente: Ministerio de Educación Nacional — SIMAT. Los datos marcados "SIMULADO" usan
        promedios departamentales MEN 2022.
      </p>
    </div>
  );
}
