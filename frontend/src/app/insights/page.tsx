"use client";

/**
 * /insights — Panel de IA Avanzada
 *
 * Integra todos los modelos ML en una sola vista:
 * 1. IVT actual con nivel de confianza (Ensemble RF+XGBoost)
 * 2. Forecasting de precios UPRA (Holt-Winters + SARIMA)
 * 3. Perfiles de clustering territorial (KMeans + DBSCAN)
 * 4. Anomalías detectadas (Isolation Forest + LOF)
 * 5. Explicación XAI (SHAP) de la predicción actual
 * 6. Recomendaciones automáticas
 */

import { useState, useEffect, useCallback } from "react";
import {
  Brain, TrendingUp, TrendingDown, AlertTriangle, CheckCircle2,
  Zap, BarChart3, Layers, Search, RefreshCw, Info, ChevronRight,
  Target, Activity, Sparkles,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, ReferenceLine, Area, AreaChart, CartesianGrid,
  Legend,
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Tipos ──────────────────────────────────────────────────────────────────────

interface Recomendacion {
  tipo: string;
  icono: string;
  titulo: string;
  accion: string;
  prioridad: "ALTA" | "MEDIA" | "BAJA";
}

interface Prediccion {
  mes: string;
  valor: number;
  ic_inf_95: number;
  ic_sup_95: number;
  tendencia: string;
}

interface Anomalia {
  periodo: string;
  tipo: string;
  severidad: string;
  descripcion: string;
  score_combinado: number;
}

interface FactorXAI {
  feature: string;
  nombre: string;
  contribucion: number;
}

interface InsightsData {
  generado_en: string;
  ivt_actual?: {
    modelo_disponible: boolean;
    ivt?: {
      etiqueta: string;
      confianza: number;
      nivel_confianza: string;
      probabilidades: Record<string, number>;
    };
    interpretacion?: string;
  };
  forecast_precios?: {
    cambio_esperado_3m_pct?: number;
    interpretacion?: string;
    predicciones?: Prediccion[];
    modelo_disponible?: boolean;
  };
  perfiles_territoriales?: {
    n_perfiles: number;
    perfiles: Record<string, string>;
    metadata?: { silhouette?: number };
    modelo_disponible?: boolean;
  };
  anomalias?: {
    n_anomalias: number;
    tasa_pct: number;
    mas_recientes: Anomalia[];
    interpretacion: string;
    modelo_disponible?: boolean;
  };
  xai?: {
    importancias_globales?: Array<{
      feature: string;
      nombre: string;
      importancia_pct: number;
    }>;
    modelo_disponible?: boolean;
  };
  recomendaciones?: Recomendacion[];
}

interface ForecastData {
  modelo_disponible: boolean;
  nombre?: string;
  predicciones?: Prediccion[];
  historico_reciente?: Array<{ mes: string; valor: number }>;
  cambio_esperado_pct?: number;
  interpretacion?: string;
}

interface ClusteringData {
  modelo_disponible: boolean;
  metadata?: {
    kmeans?: { n_clusters: number; silhouette?: number };
    dbscan?: { n_clusters: number; n_outliers: number; pct_outliers: number };
  };
  perfiles?: Record<string, {
    nombre: string;
    riesgo: string;
    n_periodos: number;
  }>;
}

interface AnomaliaData {
  modelo_disponible: boolean;
  n_anomalias?: number;
  tasa_anomalia_pct?: number;
  anomalias?: Anomalia[];
  serie_scores?: Array<{ periodo: string; score: number; es_anomalia: boolean }>;
  interpretacion?: string;
}

// ── Colores de riesgo ──────────────────────────────────────────────────────────

const RIESGO_CONFIG: Record<string, { bg: string; text: string; border: string; label: string }> = {
  ALTA:  { bg: "bg-red-50",     text: "text-red-700",    border: "border-red-200",    label: "Riesgo Alto" },
  MEDIA: { bg: "bg-amber-pale", text: "text-amber-dark", border: "border-amber-pale", label: "Riesgo Moderado" },
  BAJA:  { bg: "bg-terra-faint",text: "text-terra",      border: "border-terra-pale", label: "Riesgo Bajo" },
};

const PRIO_COLOR: Record<string, string> = {
  ALTA:  "text-red-600",
  MEDIA: "text-amber-dark",
  BAJA:  "text-terra",
};

// ── Componentes auxiliares ─────────────────────────────────────────────────────

function SectionTitle({
  icon: Icon,
  title,
  badge,
}: {
  icon: React.ElementType;
  title: string;
  badge?: string;
}) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <div className="w-8 h-8 rounded-xl bg-terra/10 flex items-center justify-center">
        <Icon size={16} className="text-terra" />
      </div>
      <h2 className="text-base font-bold text-warm-900">{title}</h2>
      {badge && (
        <span className="ml-auto text-xs bg-terra/10 text-terra px-2 py-0.5 rounded-full font-medium">
          {badge}
        </span>
      )}
    </div>
  );
}

function ModelBadge({ disponible, nombre }: { disponible: boolean; nombre: string }) {
  if (disponible) return null;
  return (
    <div className="p-4 bg-warm-50 border border-warm-200 rounded-2xl text-center">
      <Brain size={20} className="mx-auto text-warm-400 mb-2" />
      <p className="text-sm text-warm-600 font-medium">{nombre} no entrenado</p>
      <code className="text-xs bg-warm-100 px-2 py-1 rounded mt-2 inline-block text-warm-700">
        make train-advanced
      </code>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-8 bg-warm-100 rounded-xl" />
      ))}
    </div>
  );
}

// ── Componente de IVT Hero ─────────────────────────────────────────────────────

function IVTHero({ ivt }: { ivt: InsightsData["ivt_actual"] }) {
  if (!ivt?.modelo_disponible) return <ModelBadge disponible={false} nombre="Ensemble IVT" />;
  if (!ivt.ivt) return <ModelBadge disponible={false} nombre="Ensemble IVT" />;

  const etiqueta = ivt.ivt.etiqueta || "?";
  const conf = ivt.ivt;
  const cfg = RIESGO_CONFIG[etiqueta] || RIESGO_CONFIG.MEDIA;

  const probData = Object.entries(conf.probabilidades || {}).map(([k, v]) => ({
    clase: k,
    probabilidad: Math.round(v * 100),
  }));

  return (
    <div className={`p-5 rounded-2xl border ${cfg.bg} ${cfg.border}`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-xs font-medium text-warm-500 uppercase tracking-wide">IVT — Ensemble RF + XGBoost</p>
          <p className={`text-3xl font-black mt-1 ${cfg.text}`}>{etiqueta}</p>
          <p className="text-sm text-warm-600 mt-0.5">{cfg.label}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-warm-400">Confianza</p>
          <p className={`text-2xl font-bold ${cfg.text}`}>
            {Math.round((conf.confianza || 0) * 100)}%
          </p>
          <p className="text-xs text-warm-500">{conf.nivel_confianza}</p>
        </div>
      </div>

      {/* Barras de probabilidad por clase */}
      <div className="space-y-1.5 mt-3">
        {probData.map(({ clase, probabilidad }) => (
          <div key={clase} className="flex items-center gap-2">
            <span className="text-xs w-14 text-warm-600 font-medium">{clase}</span>
            <div className="flex-1 h-2 bg-white/60 rounded-full overflow-hidden">
              <div
                className={`h-2 rounded-full transition-all duration-700 ${
                  clase === "ALTA" ? "bg-red-400" :
                  clase === "MEDIA" ? "bg-amber" : "bg-terra-light"
                }`}
                style={{ width: `${probabilidad}%` }}
              />
            </div>
            <span className="text-xs text-warm-600 w-9 text-right">{probabilidad}%</span>
          </div>
        ))}
      </div>

      {ivt.interpretacion && (
        <p className="text-xs text-warm-600 mt-3 leading-relaxed border-t border-white/40 pt-3">
          {ivt.interpretacion}
        </p>
      )}
    </div>
  );
}

// ── Componente de Forecasting ──────────────────────────────────────────────────

function ForecastCard({
  data,
  titulo,
  color,
}: {
  data: ForecastData;
  titulo: string;
  color: string;
}) {
  if (!data.modelo_disponible) return <ModelBadge disponible={false} nombre={titulo} />;

  const historico = (data.historico_reciente || []).slice(-6);
  const predicciones = data.predicciones || [];

  const chartData = [
    ...historico.map((h) => ({ mes: h.mes, historico: h.valor, prediccion: null, ic_inf: null, ic_sup: null })),
    ...predicciones.map((p) => ({
      mes: p.mes,
      historico: null,
      prediccion: p.valor,
      ic_inf: p.ic_inf_95,
      ic_sup: p.ic_sup_95,
    })),
  ];

  const cambio = data.cambio_esperado_pct || 0;
  const TrendIcon = cambio > 0 ? TrendingUp : TrendingDown;
  const trendColor = cambio > 0 ? "text-red-500" : "text-terra";

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-xs text-warm-400">{titulo}</p>
          <div className="flex items-center gap-1.5 mt-0.5">
            <TrendIcon size={16} className={trendColor} />
            <span className={`text-lg font-bold ${trendColor}`}>
              {cambio > 0 ? "+" : ""}{cambio?.toFixed(1)}%
            </span>
            <span className="text-xs text-warm-400">en {predicciones.length} meses</span>
          </div>
        </div>
        <span className="text-xs bg-terra/10 text-terra px-2 py-0.5 rounded-full">HW + SARIMA</span>
      </div>

      <ResponsiveContainer width="100%" height={130}>
        <AreaChart data={chartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${color}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.2} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="mes" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
          <YAxis hide />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "none", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }}
          />
          <Area
            type="monotone"
            dataKey="historico"
            stroke={color}
            strokeWidth={2}
            fill={`url(#grad-${color})`}
            connectNulls
            dot={false}
            name="Histórico"
          />
          <Area
            type="monotone"
            dataKey="prediccion"
            stroke={color}
            strokeWidth={2}
            strokeDasharray="4 2"
            fill={`url(#grad-${color})`}
            connectNulls
            dot={{ fill: color, r: 3 }}
            name="Pronóstico"
          />
        </AreaChart>
      </ResponsiveContainer>

      {data.interpretacion && (
        <p className="text-xs text-warm-500 mt-3 leading-relaxed">{data.interpretacion}</p>
      )}
    </div>
  );
}

// ── Componente de Clustering ───────────────────────────────────────────────────

function ClusteringCard({ data }: { data: ClusteringData }) {
  if (!data.modelo_disponible) return <ModelBadge disponible={false} nombre="Clustering territorial" />;

  const perfiles = Object.entries(data.perfiles || {});
  const kmeta = data.metadata?.kmeans;
  const dbmeta = data.metadata?.dbscan;

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs text-warm-400">KMeans + DBSCAN</p>
          <p className="font-bold text-warm-900">
            {kmeta?.n_clusters || perfiles.length} perfiles detectados
          </p>
        </div>
        {kmeta?.silhouette && (
          <div className="text-right">
            <p className="text-xs text-warm-400">Silhouette</p>
            <p className="font-bold text-terra">{kmeta.silhouette.toFixed(3)}</p>
          </div>
        )}
      </div>

      <div className="space-y-2">
        {perfiles.map(([id, perfil]) => (
          <div
            key={id}
            className="flex items-center gap-3 p-2.5 bg-warm-50 rounded-xl"
          >
            <div className="w-7 h-7 rounded-lg bg-terra/10 flex items-center justify-center shrink-0">
              <span className="text-xs font-bold text-terra">{id}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-warm-800 truncate">{perfil.nombre}</p>
              <p className="text-xs text-warm-400">{perfil.n_periodos} períodos</p>
            </div>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              perfil.riesgo?.includes("ALTA") ? "bg-red-100 text-red-600" :
              perfil.riesgo?.includes("MEDIA") ? "bg-amber-pale text-amber-dark" :
              "bg-terra-faint text-terra"
            }`}>
              {perfil.riesgo}
            </span>
          </div>
        ))}
      </div>

      {dbmeta && (
        <div className="mt-3 pt-3 border-t border-warm-100 flex items-center justify-between text-xs text-warm-500">
          <span>DBSCAN: {dbmeta.n_clusters} grupos</span>
          <span>{dbmeta.n_outliers} outliers ({dbmeta.pct_outliers}%)</span>
        </div>
      )}
    </div>
  );
}

// ── Componente de Anomalías ────────────────────────────────────────────────────

function AnomalíasCard({ data }: { data: AnomaliaData }) {
  if (!data.modelo_disponible) return <ModelBadge disponible={false} nombre="Detector de Anomalías" />;

  const SEVERIDAD_COLOR: Record<string, string> = {
    "CRÍTICA":  "bg-red-100 text-red-700",
    "ALTA":     "bg-orange-100 text-orange-700",
    "MODERADA": "bg-amber-pale text-amber-dark",
  };

  return (
    <div className="card p-5">
      <div className="flex items-center gap-4 mb-4">
        <div className="text-center">
          <p className="text-2xl font-black text-warm-900">{data.n_anomalias}</p>
          <p className="text-xs text-warm-400">anomalías</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-black text-amber-dark">{data.tasa_anomalia_pct}%</p>
          <p className="text-xs text-warm-400">de la serie</p>
        </div>
        <div className="flex-1">
          <p className="text-xs text-warm-500 leading-relaxed">{data.interpretacion}</p>
        </div>
      </div>

      {/* Série de scores */}
      {data.serie_scores && data.serie_scores.length > 0 && (
        <ResponsiveContainer width="100%" height={60}>
          <AreaChart data={data.serie_scores.slice(-24)}>
            <Area
              type="monotone"
              dataKey="score"
              stroke="#F59E0B"
              fill="#FEF9EC"
              strokeWidth={1.5}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}

      <div className="space-y-2 mt-3">
        {(data.anomalias || []).slice(0, 4).map((a, i) => (
          <div key={i} className="flex items-start gap-2 p-2 bg-warm-50 rounded-xl">
            <AlertTriangle size={14} className="text-amber-dark shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-warm-600">{a.periodo}</span>
                <span className={`text-2xs px-1.5 py-0.5 rounded-full font-medium ${SEVERIDAD_COLOR[a.severidad] || "bg-warm-100 text-warm-600"}`}>
                  {a.severidad}
                </span>
              </div>
              <p className="text-xs text-warm-500 mt-0.5 leading-tight">{a.descripcion}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Componente de XAI ──────────────────────────────────────────────────────────

function XAICard({ data }: { data: InsightsData["xai"] }) {
  if (!data?.modelo_disponible && !data?.importancias_globales?.length) {
    return <ModelBadge disponible={false} nombre="XAI Explainer (SHAP)" />;
  }

  const items = data?.importancias_globales || [];

  return (
    <div className="card p-5">
      <p className="text-xs text-warm-400 mb-3">Importancias globales (SHAP TreeExplainer)</p>
      <div className="space-y-2">
        {items.slice(0, 6).map((item) => (
          <div key={item.feature} className="group">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-warm-700 truncate max-w-[70%]">{item.nombre}</span>
              <span className="text-xs font-bold text-terra">{item.importancia_pct.toFixed(1)}%</span>
            </div>
            <div className="h-1.5 bg-warm-100 rounded-full overflow-hidden">
              <div
                className="h-1.5 bg-terra rounded-full transition-all duration-700"
                style={{ width: `${Math.min(100, item.importancia_pct)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Componente de Recomendaciones ──────────────────────────────────────────────

function RecomendacionesCard({ items }: { items: Recomendacion[] }) {
  return (
    <div className="card p-5">
      <div className="space-y-3">
        {items.map((r, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 p-3 rounded-2xl border ${
              r.prioridad === "ALTA"  ? "bg-red-50 border-red-200" :
              r.prioridad === "MEDIA" ? "bg-amber-pale border-amber-pale" :
              "bg-terra-faint border-terra-pale"
            }`}
          >
            <span className="text-xl shrink-0">{r.icono}</span>
            <div className="flex-1">
              <p className={`text-sm font-semibold ${PRIO_COLOR[r.prioridad]}`}>{r.titulo}</p>
              <p className="text-xs text-warm-600 mt-0.5 leading-relaxed">{r.accion}</p>
            </div>
            <span className={`text-2xs font-bold uppercase px-1.5 py-0.5 rounded-md ${
              r.prioridad === "ALTA" ? "bg-red-100 text-red-600" :
              r.prioridad === "MEDIA" ? "bg-amber-pale text-amber-dark" :
              "bg-terra-faint text-terra"
            }`}>
              {r.prioridad}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Página principal ───────────────────────────────────────────────────────────

export default function InsightsPage() {
  const [insights, setInsights]     = useState<InsightsData | null>(null);
  const [forecast, setForecast]     = useState<ForecastData | null>(null);
  const [clustering, setClustering] = useState<ClusteringData | null>(null);
  const [anomalias, setAnomalias]   = useState<AnomaliaData | null>(null);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>("");

  const cargarDatos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [insRes, fcRes, clRes, anRes] = await Promise.allSettled([
        fetch(`${API_BASE}/ml/insights`),
        fetch(`${API_BASE}/ml/forecast/upra_indice_total?horizonte=6`),
        fetch(`${API_BASE}/ml/clustering`),
        fetch(`${API_BASE}/ml/anomalias?top=8`),
      ]);

      if (insRes.status === "fulfilled" && insRes.value.ok) {
        setInsights(await insRes.value.json());
      }
      if (fcRes.status === "fulfilled" && fcRes.value.ok) {
        setForecast(await fcRes.value.json());
      }
      if (clRes.status === "fulfilled" && clRes.value.ok) {
        setClustering(await clRes.value.json());
      }
      if (anRes.status === "fulfilled" && anRes.value.ok) {
        setAnomalias(await anRes.value.json());
      }

      setLastUpdate(new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" }));
    } catch (e) {
      setError("No se pudo conectar con la API. ¿Está corriendo el backend?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  return (
    <div className="min-h-screen bg-warm-50 p-4 md:p-6 lg:p-8">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="max-w-7xl mx-auto">
        <div className="flex items-start justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-9 h-9 rounded-2xl bg-terra flex items-center justify-center">
                <Sparkles size={18} className="text-white" />
              </div>
              <h1 className="text-2xl font-black text-warm-900">Insights de IA</h1>
            </div>
            <p className="text-warm-500 text-sm">
              Ensemble RF+XGBoost · Clustering KMeans+DBSCAN · SARIMA · Isolation Forest · SHAP
            </p>
            {lastUpdate && (
              <p className="text-xs text-warm-400 mt-1">Actualizado a las {lastUpdate}</p>
            )}
          </div>
          <button
            onClick={cargarDatos}
            disabled={loading}
            className="btn-secondary flex items-center gap-2 text-sm"
            aria-label="Recargar datos"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            <span className="hidden sm:inline">{loading ? "Cargando..." : "Actualizar"}</span>
          </button>
        </div>

        {/* ── Error ────────────────────────────────────────────────────── */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl flex items-start gap-3">
            <AlertTriangle size={16} className="text-red-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-red-700">Error de conexión</p>
              <p className="text-xs text-red-600 mt-0.5">{error}</p>
              <code className="text-xs bg-red-100 px-2 py-0.5 rounded mt-1.5 inline-block text-red-700">
                make up && make train-advanced
              </code>
            </div>
          </div>
        )}

        {/* ── Grid principal ────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Columna izquierda: IVT + Recomendaciones */}
          <div className="space-y-6">
            <div className="card p-5">
              <SectionTitle icon={Brain} title="IVT Ensemble" badge="RF + XGBoost" />
              {loading ? <LoadingSkeleton /> : <IVTHero ivt={insights?.ivt_actual} />}
            </div>

            <div className="card p-5">
              <SectionTitle icon={Target} title="Recomendaciones IA" />
              {loading ? <LoadingSkeleton /> : (
                insights?.recomendaciones?.length
                  ? <RecomendacionesCard items={insights.recomendaciones} />
                  : <p className="text-sm text-warm-400">Sin recomendaciones activas.</p>
              )}
            </div>

            <div className="card p-5">
              <SectionTitle icon={BarChart3} title="Explainability SHAP" badge="Global" />
              {loading ? <LoadingSkeleton /> : <XAICard data={insights?.xai} />}
            </div>
          </div>

          {/* Columna central: Forecasting + Anomalías */}
          <div className="space-y-6">
            <div className="card p-5">
              <SectionTitle icon={TrendingUp} title="Forecasting de Precios" badge="6 meses" />
              {loading ? <LoadingSkeleton /> : (
                <ForecastCard
                  data={forecast || { modelo_disponible: false }}
                  titulo="Índice UPRA de insumos agrícolas"
                  color="#1A6B42"
                />
              )}
            </div>

            <div className="card p-5">
              <SectionTitle icon={AlertTriangle} title="Anomalías Detectadas" badge="IsoForest + LOF" />
              {loading ? <LoadingSkeleton /> : (
                <AnomalíasCard data={anomalias || { modelo_disponible: false }} />
              )}
            </div>
          </div>

          {/* Columna derecha: Clustering + Info técnica */}
          <div className="space-y-6">
            <div className="card p-5">
              <SectionTitle icon={Layers} title="Perfiles Territoriales" badge="KMeans + DBSCAN" />
              {loading ? <LoadingSkeleton /> : (
                <ClusteringCard data={clustering || { modelo_disponible: false }} />
              )}
            </div>

            {/* Info técnica */}
            <div className="card p-5 bg-warm-900 text-white">
              <div className="flex items-center gap-2 mb-3">
                <Activity size={16} className="text-terra-light" />
                <p className="text-sm font-bold">Stack ML Avanzado</p>
              </div>
              <div className="space-y-2 text-xs text-warm-300">
                {[
                  ["Clasificación IVT", "RF + XGBoost (Voting Ensemble)"],
                  ["Calibración", "CalibratedClassifierCV (isotonic + sigmoid)"],
                  ["Segmentación", "KMeans (silhouette auto-K) + DBSCAN"],
                  ["Forecasting", "Holt-Winters + SARIMA ensemble"],
                  ["Anomalías", "Isolation Forest + LOF (contamination=10%)"],
                  ["Explicabilidad", "SHAP TreeExplainer (valores Shapley)"],
                ].map(([modelo, detalle]) => (
                  <div key={modelo} className="flex justify-between gap-2">
                    <span className="text-warm-400">{modelo}</span>
                    <span className="text-right text-warm-200">{detalle}</span>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-3 border-t border-white/10">
                <p className="text-xs text-warm-400">Entrenar todos los modelos:</p>
                <code className="text-xs text-terra-light mt-1 block">
                  make train-advanced
                </code>
              </div>
            </div>

          </div>
        </div>

        {/* ── Validacion ML ──────────────────────────────────────────── */}
        <ValidacionMLCard />

      </div>
    </div>
  );
}


// -- Tarjeta de Validacion ML ------------------------------------------------

function ValidacionMLCard() {
  const [val, setVal]   = useState<Record<string, any> | null>(null);
  const [load, setLoad] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/ml/validacion`)
      .then((r) => r.json())
      .then(setVal)
      .catch(() => setVal(null))
      .finally(() => setLoad(false));
  }, []);

  const m = val?.metricas;

  function MetricaPill({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
    return (
      <div className={`rounded-xl p-3 text-center ${ok === undefined ? "bg-warm-50" : ok ? "bg-terra-faint" : "bg-amber/10"}`}>
        <p className="text-lg font-bold text-warm-900">{value}</p>
        <p className="text-xs text-warm-500 mt-0.5">{label}</p>
      </div>
    );
  }

  function BarraImportancia({ feature, value }: { feature: string; value: number }) {
    const labels: Record<string, string> = {
      upra_indice_total: "UPRA Índice",
      upra_var_mensual_pct: "UPRA Variación",
      upra_fertilizantes: "Fertilizantes",
      upra_plaguicidas: "Plaguicidas",
      ideam_precipitacion_mm: "Precipitación",
      ideam_precipitacion_anomalia: "Anom. Precip.",
      ideam_temperatura_c: "Temperatura",
      ideam_temperatura_anomalia: "Anom. Temp.",
      mes: "Mes",
      anio: "Año",
    };
    return (
      <div className="flex items-center gap-2 text-xs">
        <span className="w-32 text-warm-600 truncate">{labels[feature] ?? feature}</span>
        <div className="flex-1 h-2 bg-warm-100 rounded-full overflow-hidden">
          <div className="h-full rounded-full bg-terra" style={{ width: `${value * 100}%` }} />
        </div>
        <span className="w-10 text-right font-mono text-warm-500">{(value * 100).toFixed(1)}%</span>
      </div>
    );
  }

  return (
    <div className="mt-6 card p-6">
      <SectionTitle icon={Target} title="Validación del Modelo" badge="Métricas ML" />

      {load ? (
        <LoadingSkeleton />
      ) : !val || !m ? (
        <ModelBadge disponible={false} nombre="Validación ML" />
      ) : !val.modelo_disponible ? (
        <div className="p-4 bg-warm-50 rounded-2xl text-center text-sm text-warm-500">
          <Brain size={20} className="mx-auto mb-2 text-warm-400" />
          {val.mensaje ?? "Modelo no entrenado"}
          <br />
          <code className="text-xs bg-warm-100 px-2 py-1 rounded mt-2 inline-block">make train-advanced</code>
        </div>
      ) : (
        <div className="space-y-5">
          {/* Metricas globales */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricaPill label="Accuracy"   value={`${((m.accuracy ?? 0) * 100).toFixed(1)}%`}  ok={(m.accuracy ?? 0) > 0.75} />
            <MetricaPill label="F1 Macro"   value={`${((m.f1_macro ?? 0) * 100).toFixed(1)}%`}  ok={(m.f1_macro ?? 0) > 0.65} />
            <MetricaPill label="Precision"  value={`${((m.precision_macro ?? 0) * 100).toFixed(1)}%`} />
            <MetricaPill label="AUC-ROC"    value={m.auc_roc_macro ? m.auc_roc_macro.toFixed(3) : "—"} ok={m.auc_roc_macro > 0.80} />
          </div>

          {/* CV */}
          {m.cv && (
            <div className="bg-warm-50 rounded-xl p-4 text-xs text-warm-600">
              <p className="font-semibold text-warm-800 mb-1">
                Validación cruzada 5-fold — Accuracy: {((m.cv.cv_accuracy_mean ?? 0) * 100).toFixed(1)}%
                {" "}± {((m.cv.cv_accuracy_std ?? 0) * 100).toFixed(1)}%
              </p>
              <div className="flex gap-2 mt-2">
                {(m.cv.cv_accuracy_folds ?? []).map((v: number, i: number) => (
                  <div key={i} className="flex-1 bg-white rounded-lg p-2 text-center">
                    <p className="font-bold text-terra">{(v * 100).toFixed(0)}%</p>
                    <p className="text-warm-400">Fold {i + 1}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Importancia de variables */}
          {Array.isArray(m.importancias) && m.importancias.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-warm-700 mb-2">Importancia de variables</p>
              <div className="space-y-2">
                {m.importancias
                  .slice()
                  .sort((a: any, b: any) => b.importancia - a.importancia)
                  .slice(0, 8)
                  .map((imp: any) => (
                    <BarraImportancia key={imp.feature} feature={imp.feature} value={imp.importancia} />
                  ))}
              </div>
            </div>
          )}

          {/* F1 por clase */}
          <div className="grid grid-cols-3 gap-3">
            {(["baja", "media", "alta"] as const).map((c) => {
              const key = `f1_${c}`;
              return (
                <div key={c} className="rounded-xl bg-warm-50 p-3 text-center">
                  <p className="text-sm font-bold text-warm-900">
                    {m[key] != null ? `${(m[key] * 100).toFixed(0)}%` : "—"}
                  </p>
                  <p className="text-xs text-warm-500">F1 clase {c.toUpperCase()}</p>
                </div>
              );
            })}
          </div>

          {val.desde_cache && (
            <p className="text-xs text-warm-300 text-center">
              Métricas en caché · <code>make validate</code> para recalcular
            </p>
          )}
        </div>
      )}
    </div>
  );
}
