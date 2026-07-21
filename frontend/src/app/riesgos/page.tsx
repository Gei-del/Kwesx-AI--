"use client";

/**
 * /riesgos — Alertas de Riesgo Territorial
 * Fuente: Isolation Forest + LOF (anomaly detection)
 */

import { useEffect, useState } from "react";
import {
  ShieldAlert, ShieldCheck, AlertTriangle, TrendingUp, TrendingDown,
  BarChart2, RefreshCw, Info
} from "lucide-react";
import { api } from "@/lib/api";
import clsx from "clsx";

// ── Tipos ─────────────────────────────────────────────────────────────────────

interface Anomalia {
  fecha:        string;
  score:        number;     // < 0 = más anómalo (Isolation Forest convention)
  tipo:         string;     // "upra" | "ideam_precip" | "ideam_temp" | "ani"
  descripcion?: string;
  valor?:       number;
  umbral?:      number;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function severidad(score: number): "ALTA" | "MEDIA" | "BAJA" {
  if (score < -0.2) return "ALTA";
  if (score < -0.1) return "MEDIA";
  return "BAJA";
}

const SEV_CONFIG = {
  ALTA:  { cls: "bg-red-50 border-red-200 text-red-700",  dot: "bg-red-500",  label: "Riesgo Alto"  },
  MEDIA: { cls: "bg-amber/10 border-amber/30 text-amber-dark", dot: "bg-amber", label: "Riesgo Medio" },
  BAJA:  { cls: "bg-warm-50 border-warm-200 text-warm-600",dot: "bg-warm-400",label: "Normal"       },
};

const TIPO_LABELS: Record<string, { emoji: string; label: string }> = {
  upra:        { emoji: "🌱", label: "Precios agrícolas (UPRA)" },
  ideam_precip:{ emoji: "🌧️", label: "Precipitación (IDEAM)" },
  ideam_temp:  { emoji: "🌡️", label: "Temperatura (IDEAM)" },
  ani:         { emoji: "🛣️", label: "Tráfico vehicular (ANI)" },
};

// ── Offline ───────────────────────────────────────────────────────────────────

function OfflinePage({ msg, onRetry }: { msg: string; onRetry: () => void }) {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="card border border-warm-200 bg-warm-50 text-center py-12 px-6">
        <div className="w-16 h-16 bg-warm-100 rounded-3xl flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">🛡️</span>
        </div>
        <h2 className="text-lg font-bold text-warm-900 mb-2">Sistema de alertas no disponible</h2>
        <p className="text-warm-500 text-sm mb-6 max-w-md mx-auto">
          No fue posible conectarse con el módulo de detección de anomalías.
          El modelo necesita estar entrenado con datos históricos del MTU.
        </p>
        <button onClick={onRetry} className="btn-primary mr-3">
          Reintentar
        </button>
        <p className="text-xs text-warm-300 mt-4">
          Tip: ejecuta <code className="bg-warm-100 px-1 rounded">python -m backend.ml.train_advanced</code> para entrenar el modelo.
        </p>
        <p className="text-xs text-warm-200 hidden">{msg}</p>
      </div>
    </div>
  );
}

// ── Sin alertas ───────────────────────────────────────────────────────────────

function SinAlertas() {
  return (
    <div className="card border border-terra/20 bg-terra-faint text-center py-12 px-6">
      <div className="w-16 h-16 bg-terra/10 rounded-3xl flex items-center justify-center mx-auto mb-4">
        <ShieldCheck size={32} className="text-terra" />
      </div>
      <h2 className="text-lg font-bold text-warm-900 mb-2">Todo bajo control</h2>
      <p className="text-warm-500 text-sm max-w-md mx-auto">
        No se detectaron anomalías significativas en los datos del MTU.
        El sistema monitorea continuamente las series temporales de UPRA, IDEAM y ANI.
      </p>
    </div>
  );
}

// ── Shimmer ───────────────────────────────────────────────────────────────────

function Shimmer() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="card p-4 flex gap-4 items-start">
          <div className="shimmer-line w-12 h-12 rounded-xl shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="shimmer-line h-4 w-2/3" />
            <div className="shimmer-line h-3 w-full" />
            <div className="shimmer-line h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Tarjeta anomalía ──────────────────────────────────────────────────────────

function AnomaliaCard({ a, idx }: { a: Anomalia; idx: number }) {
  const sev = severidad(a.score);
  const cfg = SEV_CONFIG[sev];
  const tipo = TIPO_LABELS[a.tipo] ?? { emoji: "⚠️", label: a.tipo };

  return (
    <div className={clsx("rounded-2xl border p-5 transition-shadow hover:shadow-md", cfg.cls)}>
      <div className="flex items-start gap-4">
        {/* Número */}
        <div className="w-9 h-9 rounded-xl bg-white/60 flex items-center justify-center shrink-0 text-sm font-bold text-warm-600">
          {idx + 1}
        </div>

        {/* Contenido */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-base">{tipo.emoji}</span>
            <span className="font-semibold text-sm">{tipo.label}</span>
            <span className={clsx(
              "text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1",
              sev === "ALTA"  ? "bg-red-100 text-red-700"  :
              sev === "MEDIA" ? "bg-amber/20 text-amber-dark" :
                               "bg-warm-100 text-warm-600"
            )}>
              <span className={clsx("w-1.5 h-1.5 rounded-full inline-block", cfg.dot)} />
              {cfg.label}
            </span>
          </div>

          <p className="text-xs text-warm-600 mb-2">
            {a.fecha && <span className="font-medium">{new Date(a.fecha).toLocaleDateString("es-CO", { year: "numeric", month: "long", day: "numeric" })} · </span>}
            {a.descripcion || `Score de anomalía: ${a.score.toFixed(4)}`}
          </p>

          {/* Barra de score */}
          <div className="flex items-center gap-2">
            <span className="text-2xs text-warm-400 shrink-0">Score IA</span>
            <div className="flex-1 h-1.5 bg-white/60 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.min(100, Math.abs(a.score) * 400)}%`,
                  background: sev === "ALTA" ? "#ef4444" : sev === "MEDIA" ? "var(--color-amber)" : "var(--color-terra)",
                }}
              />
            </div>
            <span className="text-2xs font-mono text-warm-500 shrink-0">
              {a.score.toFixed(3)}
            </span>
          </div>

          {/* Valor vs umbral */}
          {a.valor != null && a.umbral != null && (
            <div className="mt-2 flex items-center gap-3 text-xs text-warm-500">
              <span>Observado: <strong>{a.valor.toFixed(2)}</strong></span>
              <span>Umbral esperado: <strong>{a.umbral.toFixed(2)}</strong></span>
              <span className={a.valor > a.umbral ? "text-red-500" : "text-terra"}>
                {a.valor > a.umbral ? <TrendingUp size={12} className="inline" /> : <TrendingDown size={12} className="inline" />}
                {" "}{Math.abs(((a.valor - a.umbral) / a.umbral) * 100).toFixed(1)}% del umbral
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Panel de estadísticas ─────────────────────────────────────────────────────

function StatsPanel({ anomalias }: { anomalias: Anomalia[] }) {
  const altas  = anomalias.filter((a) => severidad(a.score) === "ALTA").length;
  const medias = anomalias.filter((a) => severidad(a.score) === "MEDIA").length;
  const bajas  = anomalias.filter((a) => severidad(a.score) === "BAJA").length;

  return (
    <div className="grid grid-cols-3 gap-4">
      {[
        { label: "Riesgo Alto",  value: altas,  color: "text-red-500",    bg: "bg-red-50   border-red-200"   },
        { label: "Riesgo Medio", value: medias, color: "text-amber-dark", bg: "bg-amber/10 border-amber/20"  },
        { label: "Normales",     value: bajas,  color: "text-terra",      bg: "bg-terra-faint border-terra/20" },
      ].map(({ label, value, color, bg }) => (
        <div key={label} className={clsx("card border rounded-2xl p-4 text-center", bg)}>
          <p className={clsx("text-3xl font-bold", color)}>{value}</p>
          <p className="text-xs text-warm-500 mt-0.5">{label}</p>
        </div>
      ))}
    </div>
  );
}

// ── Página principal ──────────────────────────────────────────────────────────

export default function RiesgosPage() {
  const [raw, setRaw] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filtroSev, setFiltroSev] = useState<"" | "ALTA" | "MEDIA" | "BAJA">("");

  const cargar = () => {
    setLoading(true);
    setError("");
    api.mlAnomalias(20)
      .then((r) => setRaw(r))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(cargar, []);

  if (loading) return <div className="p-6 max-w-5xl mx-auto"><Shimmer /></div>;
  if (error)   return <div className="p-6"><OfflinePage msg={error} onRetry={cargar} /></div>;

  // Normalizar respuesta del backend
  const anomaliasRaw = (raw as any)?.anomalias ?? (raw as any)?.datos ?? [];
  const anomalias: Anomalia[] = Array.isArray(anomaliasRaw)
    ? anomaliasRaw.map((a: any) => ({
        fecha:       a.fecha ?? a.date ?? "",
        score:       a.score ?? a.anomaly_score ?? 0,
        tipo:        a.tipo ?? a.type ?? "upra",
        descripcion: a.descripcion ?? a.description ?? "",
        valor:       a.valor ?? a.value,
        umbral:      a.umbral ?? a.threshold,
      }))
    : [];

  const filtradas = anomalias.filter((a) =>
    !filtroSev || severidad(a.score) === filtroSev
  );

  const hayAlertas = anomalias.some((a) => severidad(a.score) !== "BAJA");

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <div className={clsx(
        "card p-6",
        hayAlertas ? "bg-red-50 border border-red-200" : "gradient-terra text-white"
      )}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={clsx(
              "w-10 h-10 rounded-xl flex items-center justify-center",
              hayAlertas ? "bg-red-100" : "bg-white/15"
            )}>
              <ShieldAlert size={20} className={hayAlertas ? "text-red-600" : "text-white"} />
            </div>
            <div>
              <h1 className={clsx("text-lg font-bold", hayAlertas ? "text-red-900" : "text-white")}>
                {hayAlertas ? "Alertas activas detectadas" : "Sistema bajo monitoreo activo"}
              </h1>
              <p className={clsx("text-sm", hayAlertas ? "text-red-500" : "text-white/70")}>
                Isolation Forest + LOF · {anomalias.length} períodos analizados
              </p>
            </div>
          </div>
          <button
            onClick={cargar}
            className={clsx(
              "p-2 rounded-xl transition-colors",
              hayAlertas ? "hover:bg-red-100 text-red-400" : "hover:bg-white/10 text-white/60"
            )}
            title="Actualizar"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* ── Estadísticas ──────────────────────────────────────────────────── */}
      {anomalias.length > 0 && <StatsPanel anomalias={anomalias} />}

      {/* ── Nota metodológica ─────────────────────────────────────────────── */}
      <div className="flex items-start gap-2 bg-warm-50 rounded-xl p-3 text-xs text-warm-500 border border-warm-100">
        <Info size={13} className="mt-0.5 shrink-0 text-warm-400" />
        <p>
          Las anomalías se detectan mediante <strong>Isolation Forest</strong> (sensible a outliers globales)
          y <strong>LOF — Local Outlier Factor</strong> (sensible a cambios locales).
          Un score más negativo indica mayor probabilidad de ser un dato atípico.
          Umbral de alerta ALTA: score &lt; −0.20.
        </p>
      </div>

      {/* ── Filtros ───────────────────────────────────────────────────────── */}
      {anomalias.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {(["", "ALTA", "MEDIA", "BAJA"] as const).map((sev) => (
            <button
              key={sev}
              onClick={() => setFiltroSev(sev)}
              className={clsx(
                "px-3 py-1.5 text-xs rounded-xl border transition-colors font-medium",
                filtroSev === sev
                  ? "bg-terra text-white border-terra"
                  : "bg-white text-warm-600 border-warm-200 hover:border-terra hover:text-terra"
              )}
            >
              {sev || "Todas"}
            </button>
          ))}
        </div>
      )}

      {/* ── Lista anomalías ────────────────────────────────────────────────── */}
      {anomalias.length === 0 ? (
        <SinAlertas />
      ) : (
        <div className="space-y-3">
          {filtradas.length === 0 ? (
            <div className="card text-center py-8 text-warm-400 text-sm">
              No hay anomalías con el filtro seleccionado.
            </div>
          ) : (
            filtradas.map((a, i) => <AnomaliaCard key={`${a.fecha}-${i}`} a={a} idx={i} />)
          )}
        </div>
      )}

      {/* ── Fuente ────────────────────────────────────────────────────────── */}
      <p className="text-xs text-warm-300 text-center">
        Modelos entrenados con datos históricos del MTU (UPRA + IDEAM + ANI).
        Las alertas no son sustituto del criterio técnico especializado.
      </p>
    </div>
  );
}
