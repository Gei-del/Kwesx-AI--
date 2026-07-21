"use client";

/**
 * /datos/upra — Serie mensual UPRA: Índice de Precios de Insumos Agrícolas
 *
 * Fuente: UPRA / datos.gov.co (gwbi-fnzs)
 * 89 meses · Nacional · 2018-2026
 */

import { useEffect, useState, useMemo } from "react";
import { BarChart2, TrendingUp, TrendingDown, Minus, Download } from "lucide-react";
import { api, UPRARegistro } from "@/lib/api";
import UpraLineChart from "@/components/charts/UpraLineChart";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmt(n: number | undefined | null, dec = 2) {
  if (n == null) return "—";
  return n.toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

function fmtFecha(s: string) {
  const d = new Date(s);
  return d.toLocaleDateString("es-CO", { year: "numeric", month: "short" });
}

function VariacionChip({ v }: { v?: number | null }) {
  if (v == null) return <span className="text-gray-400">—</span>;
  const color = v > 0 ? "text-red-600" : v < 0 ? "text-green-600" : "text-gray-500";
  const Icon  = v > 0 ? TrendingUp : v < 0 ? TrendingDown : Minus;
  return (
    <span className={`inline-flex items-center gap-1 font-mono text-sm ${color}`}>
      <Icon size={13} />
      {v > 0 ? "+" : ""}{fmt(v)}%
    </span>
  );
}

// ─── Página ──────────────────────────────────────────────────────────────────

export default function UPRAPage() {
  const [datos, setDatos]     = useState<UPRARegistro[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);
  const [filtro, setFiltro]   = useState<"todos" | "12m" | "24m">("todos");

  useEffect(() => {
    api.upraTendencia()
      .then((r) => setDatos(r.datos))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Filtrar según rango seleccionado
  const datosFiltrados = useMemo(() => {
    if (filtro === "todos") return datos;
    const meses = filtro === "12m" ? 12 : 24;
    return datos.slice(-meses);
  }, [datos, filtro]);

  // KPIs del último mes
  const ultimo    = datos[datos.length - 1];
  const penultimo = datos[datos.length - 2];

  const cambio12m = datos.length >= 13
    ? ((ultimo?.indice_total ?? 0) - (datos[datos.length - 13]?.indice_total ?? 0)) /
      (datos[datos.length - 13]?.indice_total ?? 1) * 100
    : null;

  if (loading) return <PageSkeleton />;
  if (error)   return <ErrorBanner msg={error} />;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">

      {/* Encabezado */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BarChart2 size={20} className="text-teal" />
            <h1 className="text-lg font-semibold text-gray-900">Precios de Insumos Agrícolas — UPRA</h1>
          </div>
          <p className="text-sm text-gray-500">
            Índice mensual nacional · Fuente: UPRA / datos.gov.co · {datos.length} meses disponibles
          </p>
        </div>
        <span className="text-xs bg-teal/10 text-teal font-semibold px-3 py-1 rounded-full">
          Dataset gwbi-fnzs
        </span>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: "Índice actual",
            value: fmt(ultimo?.indice_total, 1),
            sub: fmtFecha(ultimo?.fecha ?? ""),
            color: "border-l-teal",
          },
          {
            label: "Var. mensual",
            value: <VariacionChip v={ultimo?.variacion_mensual_pct} />,
            sub: "Vs. mes anterior",
            color: (ultimo?.variacion_mensual_pct ?? 0) > 0 ? "border-l-red-400" : "border-l-green-400",
          },
          {
            label: "Cambio 12 meses",
            value: <VariacionChip v={cambio12m} />,
            sub: "Variación interanual",
            color: (cambio12m ?? 0) > 0 ? "border-l-red-400" : "border-l-green-400",
          },
          {
            label: "Fertilizantes",
            value: fmt(ultimo?.total_fertilizantes, 1),
            sub: `Plaguicidas: ${fmt(ultimo?.total_plaguicidas, 1)}`,
            color: "border-l-sand",
          },
        ].map(({ label, value, sub, color }) => (
          <div key={label} className={`card border-l-4 ${color} py-3 px-4`}>
            <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
            <div className="text-xl font-bold text-gray-900 my-1">{value}</div>
            <p className="text-xs text-gray-400">{sub}</p>
          </div>
        ))}
      </div>

      {/* Gráfica con selector de rango */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Evolución del Índice UPRA
          </h2>
          <div className="flex rounded-lg border border-gray-200 overflow-hidden text-xs">
            {(["12m", "24m", "todos"] as const).map((r) => (
              <button
                key={r}
                onClick={() => setFiltro(r)}
                className={`px-3 py-1.5 font-medium transition-colors ${
                  filtro === r
                    ? "bg-navy text-white"
                    : "text-gray-500 hover:bg-gray-50"
                }`}
              >
                {r === "todos" ? "Todo" : r}
              </button>
            ))}
          </div>
        </div>
        <UpraLineChart datos={datosFiltrados} />
      </div>

      {/* Tabla */}
      <div className="card overflow-hidden p-0">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">Datos mensuales completos</h2>
          <span className="text-xs text-gray-400">{datos.length} registros</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500 tracking-wide">
              <tr>
                <th className="px-5 py-3 text-left">Fecha</th>
                <th className="px-5 py-3 text-right">Índice Total</th>
                <th className="px-5 py-3 text-right">Fertilizantes</th>
                <th className="px-5 py-3 text-right">Plaguicidas</th>
                <th className="px-5 py-3 text-right">Var. mensual</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {[...datos].reverse().map((r) => (
                <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-700">{fmtFecha(r.fecha)}</td>
                  <td className="px-5 py-3 text-right font-mono">{fmt(r.indice_total, 1)}</td>
                  <td className="px-5 py-3 text-right font-mono text-gray-600">{fmt(r.total_fertilizantes, 1)}</td>
                  <td className="px-5 py-3 text-right font-mono text-gray-600">{fmt(r.total_plaguicidas, 1)}</td>
                  <td className="px-5 py-3 text-right">
                    <VariacionChip v={r.variacion_mensual_pct} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Nota metodológica */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl px-5 py-4 text-sm text-blue-800">
        <p className="font-semibold mb-1">¿Qué mide este índice?</p>
        <p className="text-blue-700 leading-relaxed">
          El índice UPRA refleja la evolución mensual del precio de los insumos agrícolas en Colombia
          (fertilizantes, plaguicidas, semillas, servicios). Base 100 = 2021. Un valor mayor a 100
          indica que los insumos son más caros que en el año base, afectando directamente la rentabilidad
          del sector rural y la seguridad alimentaria territorial.
        </p>
      </div>
    </div>
  );
}

// ─── Sub-componentes ──────────────────────────────────────────────────────────

function PageSkeleton() {
  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3" />
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-gray-200 rounded-xl" />)}
      </div>
      <div className="h-72 bg-gray-200 rounded-xl" />
      <div className="h-64 bg-gray-200 rounded-xl" />
    </div>
  );
}

function ErrorBanner({ msg }: { msg: string }) {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="card border border-warm-200 bg-warm-50 text-center py-12 px-6">
        <div className="w-16 h-16 bg-warm-100 rounded-3xl flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">📡</span>
        </div>
        <h2 className="text-lg font-bold text-warm-800 mb-2">
          Datos no disponibles por ahora
        </h2>
        <p className="text-warm-500 text-sm max-w-sm mx-auto leading-relaxed">
          No fue posible conectarse con el servidor de datos UPRA.
          Cuando el servicio esté activo, aquí verás los precios de fertilizantes,
          semillas e insumos agrícolas de Colombia.
        </p>
        <div className="mt-6 flex items-center justify-center gap-2">
          <button
            onClick={() => window.location.reload()}
            className="btn-primary text-sm px-5 py-2.5"
          >
            Reintentar
          </button>
          <a
            href="https://www.datos.gov.co/Agricultura-y-Desarrollo-Rural/ndice-de-Precios-de-Insumos-Agropecuarios-UPRA/gwbi-fnzs"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-sm px-5 py-2.5"
          >
            Ver fuente oficial
          </a>
        </div>
        <p className="text-xs text-warm-300 mt-4 font-mono hidden">
          {msg}
        </p>
      </div>
    </div>
  );
}
