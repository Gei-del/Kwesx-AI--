"use client";

/**
 * /datos/ideam — Variables Climáticas · IDEAM
 *
 * Fuente: IDEAM / datos.gov.co
 *   Precipitación: s54a-sgyg
 *   Temperatura:   sbwg-7ju4
 *
 * Muestra datos de estaciones hidrometeorológicas en Colombia:
 * precipitación (mm) y temperatura ambiente (°C) por departamento.
 */

import { useEffect, useState, useMemo } from "react";
import { Activity, CloudRain, Thermometer, ChevronDown, MapPin } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend
} from "recharts";
import dynamic from "next/dynamic";
import { api, IDEAMRegistro } from "@/lib/api";

// Mapa Leaflet (solo cliente)
const ColombiaMap = dynamic(() => import("@/components/map/ColombiaMap"), {
  ssr: false,
  loading: () => (
    <div className="h-full bg-gray-100 rounded-xl flex items-center justify-center text-gray-400 text-sm">
      Cargando mapa...
    </div>
  ),
});

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmt(n: number | undefined | null, dec = 1) {
  if (n == null) return "—";
  return n.toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

function fmtFecha(s: string) {
  try {
    return new Date(s).toLocaleDateString("es-CO", {
      day: "2-digit", month: "short", year: "numeric"
    });
  } catch { return s; }
}

// ─── Página ──────────────────────────────────────────────────────────────────

export default function IDEAMPage() {
  const [datos, setDatos]       = useState<IDEAMRegistro[]>([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);
  const [tipo, setTipo]         = useState<"todos" | "precipitacion" | "temperatura">("todos");
  const [filtroDept, setFiltroDept] = useState("Todos");
  const [pagina, setPagina]     = useState(0);
  const POR_PAGINA = 15;

  useEffect(() => {
    // Traer últimos 30 días, máx 1000 registros
    api.ideam({ limit: 1000, dias: 30 })
      .then((r) => setDatos(r.datos))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Listas únicas para filtros
  const departamentos = useMemo(() => {
    const set = new Set(datos.map((d) => d.departamento ?? "Sin geo").filter(Boolean));
    return ["Todos", ...Array.from(set).sort()];
  }, [datos]);

  // Filtro combinado
  const filtrados = useMemo(() => {
    return datos.filter((d) => {
      const tipoOk  = tipo === "todos" || d.tipo_variable?.toLowerCase().includes(
        tipo === "precipitacion" ? "prec" : "temp"
      );
      const deptOk  = filtroDept === "Todos" || (d.departamento ?? "Sin geo") === filtroDept;
      return tipoOk && deptOk;
    });
  }, [datos, tipo, filtroDept]);

  // Separar precipitación y temperatura
  const precipitacion = useMemo(
    () => datos.filter((d) => d.tipo_variable?.toLowerCase().includes("prec")),
    [datos]
  );
  const temperatura = useMemo(
    () => datos.filter((d) => d.tipo_variable?.toLowerCase().includes("temp")),
    [datos]
  );

  // Gráfica: promedio por departamento (top 8)
  const porDepartamento = useMemo(() => {
    const mapPrec: Record<string, number[]> = {};
    const mapTemp: Record<string, number[]> = {};

    datos.forEach((d) => {
      const dept = d.departamento ?? "Sin geo";
      if (d.tipo_variable?.toLowerCase().includes("prec")) {
        if (!mapPrec[dept]) mapPrec[dept] = [];
        mapPrec[dept].push(d.valor_observado);
      } else if (d.tipo_variable?.toLowerCase().includes("temp")) {
        if (!mapTemp[dept]) mapTemp[dept] = [];
        mapTemp[dept].push(d.valor_observado);
      }
    });

    const depts = Array.from(
      new Set([...Object.keys(mapPrec), ...Object.keys(mapTemp)])
    );

    return depts
      .map((dept) => ({
        dept: dept.length > 12 ? dept.slice(0, 12) + "…" : dept,
        prec: mapPrec[dept] ? mapPrec[dept].reduce((a, b) => a + b, 0) / mapPrec[dept].length : null,
        temp: mapTemp[dept] ? mapTemp[dept].reduce((a, b) => a + b, 0) / mapTemp[dept].length : null,
      }))
      .filter((d) => d.prec != null || d.temp != null)
      .sort((a, b) => (b.prec ?? 0) - (a.prec ?? 0))
      .slice(0, 8);
  }, [datos]);

  // KPIs
  const promPrec = precipitacion.length > 0
    ? precipitacion.reduce((s, d) => s + d.valor_observado, 0) / precipitacion.length
    : null;
  const promTemp = temperatura.length > 0
    ? temperatura.reduce((s, d) => s + d.valor_observado, 0) / temperatura.length
    : null;
  const estaciones = new Set(datos.map((d) => d.nombre_estacion)).size;

  // Paginación
  const paginas     = Math.ceil(filtrados.length / POR_PAGINA);
  const datosPagina = filtrados.slice(pagina * POR_PAGINA, (pagina + 1) * POR_PAGINA);

  if (loading) return <PageSkeleton />;
  if (error)   return <ErrorBanner msg={error} />;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">

      {/* Encabezado */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Activity size={20} className="text-teal" />
            <h1 className="text-lg font-semibold text-gray-900">Variables Climáticas — IDEAM</h1>
          </div>
          <p className="text-sm text-gray-500">
            Precipitación y temperatura · Últimos 30 días · {datos.length} mediciones · {estaciones} estaciones
          </p>
        </div>
        <span className="text-xs bg-teal/10 text-teal font-semibold px-3 py-1 rounded-full">
          s54a-sgyg · sbwg-7ju4
        </span>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: "Precipitación media",
            value: promPrec != null ? `${fmt(promPrec)} mm` : "—",
            sub: `${precipitacion.length} mediciones`,
            color: "border-l-teal",
            Icon: CloudRain,
          },
          {
            label: "Temperatura media",
            value: promTemp != null ? `${fmt(promTemp)} °C` : "—",
            sub: `${temperatura.length} mediciones`,
            color: "border-l-sand",
            Icon: Thermometer,
          },
          {
            label: "Estaciones activas",
            value: estaciones,
            sub: "Con datos recientes",
            color: "border-l-navy",
            Icon: MapPin,
          },
          {
            label: "Departamentos",
            value: departamentos.length - 1,
            sub: "Con cobertura",
            color: "border-l-green-400",
            Icon: Activity,
          },
        ].map(({ label, value, sub, color, Icon }) => (
          <div key={label} className={`card border-l-4 ${color} py-3 px-4`}>
            <div className="flex items-center gap-1.5 mb-1">
              <Icon size={13} className="text-gray-400" />
              <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
            </div>
            <div className="text-xl font-bold text-gray-900 my-1">{value}</div>
            <p className="text-xs text-gray-400">{sub}</p>
          </div>
        ))}
      </div>

      {/* Mapa */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Distribución Geográfica de Estaciones
          </h2>
          <div className="flex gap-2 text-xs">
            <span className="flex items-center gap-1 text-gray-500">
              <span className="w-3 h-3 rounded-full bg-teal inline-block" /> Precipitación
            </span>
            <span className="flex items-center gap-1 text-gray-500">
              <span className="w-3 h-3 rounded-full bg-sand inline-block" /> Temperatura
            </span>
          </div>
        </div>
        <div style={{ height: "380px" }}>
          <ColombiaMap puntos={datos.filter((d) => d.latitud && d.longitud)} />
        </div>
        <p className="text-xs text-gray-400 mt-2 text-right">
          {datos.filter((d) => d.latitud && d.longitud).length} estaciones con coordenadas
        </p>
      </div>

      {/* Gráfica por departamento */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Promedio por Departamento (Top 8)
        </h2>
        {porDepartamento.length === 0 ? (
          <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
            Sin datos suficientes para graficar
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={porDepartamento} margin={{ left: 4, right: 16, top: 4 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis dataKey="dept" tick={{ fontSize: 10 }} />
              <YAxis yAxisId="prec" orientation="left" tick={{ fontSize: 11 }}
                label={{ value: "mm", angle: -90, position: "insideLeft", fontSize: 11, fill: "#9ca3af" }} />
              <YAxis yAxisId="temp" orientation="right" tick={{ fontSize: 11 }}
                label={{ value: "°C", angle: 90, position: "insideRight", fontSize: 11, fill: "#9ca3af" }} />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8 }}
                formatter={(v: number, name: string) => [
                  `${v.toFixed(1)} ${name === "prec" ? "mm" : "°C"}`,
                  name === "prec" ? "Precipitación" : "Temperatura"
                ]}
              />
              <Legend formatter={(v) => v === "prec" ? "Precipitación (mm)" : "Temperatura (°C)"} />
              <Bar yAxisId="prec" dataKey="prec" fill="#3FA796" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="temp" dataKey="temp" fill="#F2A541" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Filtros + Tabla */}
      <div className="card overflow-hidden p-0">
        {/* Barra de filtros */}
        <div className="px-5 py-3 border-b border-gray-100 flex flex-wrap gap-3 items-center bg-gray-50">
          <span className="text-sm font-medium text-gray-600">Filtrar:</span>

          {/* Tipo de variable */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden text-xs">
            {(["todos", "precipitacion", "temperatura"] as const).map((t) => (
              <button
                key={t}
                onClick={() => { setTipo(t); setPagina(0); }}
                className={`px-3 py-1.5 font-medium capitalize transition-colors ${
                  tipo === t ? "bg-navy text-white" : "text-gray-500 hover:bg-gray-100 bg-white"
                }`}
              >
                {t === "todos" ? "Todos" : t === "precipitacion" ? "Precipitación" : "Temperatura"}
              </button>
            ))}
          </div>

          {/* Departamento */}
          <div className="relative">
            <select
              value={filtroDept}
              onChange={(e) => { setFiltroDept(e.target.value); setPagina(0); }}
              className="appearance-none text-sm border border-gray-200 rounded-lg px-3 py-1.5 pr-7 text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-navy/20"
            >
              {departamentos.map((o) => <option key={o}>{o}</option>)}
            </select>
            <ChevronDown size={13} className="absolute right-2 top-2.5 text-gray-400 pointer-events-none" />
          </div>

          <span className="ml-auto text-xs text-gray-400">{filtrados.length} registros</span>
        </div>

        {/* Tabla */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500 tracking-wide">
              <tr>
                <th className="px-4 py-3 text-left">Estación</th>
                <th className="px-4 py-3 text-left">Depto.</th>
                <th className="px-4 py-3 text-left">Variable</th>
                <th className="px-4 py-3 text-right">Fecha</th>
                <th className="px-4 py-3 text-right">Valor</th>
                <th className="px-4 py-3 text-right">Unidad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {datosPagina.map((r) => {
                const esPrec = r.tipo_variable?.toLowerCase().includes("prec");
                return (
                  <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-2.5 font-medium text-gray-800 max-w-[180px] truncate">
                      {r.nombre_estacion}
                    </td>
                    <td className="px-4 py-2.5 text-gray-600 text-xs">{r.departamento ?? "—"}</td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
                        esPrec ? "bg-teal/10 text-teal" : "bg-amber-pale text-amber-dark"
                      }`}>
                        {esPrec ? <CloudRain size={11} /> : <Thermometer size={11} />}
                        {esPrec ? "Precipitación" : "Temperatura"}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right text-xs text-gray-500">{fmtFecha(r.fecha)}</td>
                    <td className="px-4 py-2.5 text-right font-mono font-semibold">
                      {fmt(r.valor_observado, esPrec ? 1 : 2)}
                    </td>
                    <td className="px-4 py-2.5 text-right text-xs text-gray-400">{r.unidad_medida}</td>
                  </tr>
                );
              })}
              {datosPagina.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">
                    Sin registros con los filtros actuales
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        {paginas > 1 && (
          <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
            <button
              onClick={() => setPagina((p) => Math.max(0, p - 1))}
              disabled={pagina === 0}
              className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
            >
              ← Anterior
            </button>
            <span className="text-xs text-gray-500">
              {pagina * POR_PAGINA + 1}–{Math.min((pagina + 1) * POR_PAGINA, filtrados.length)} de {filtrados.length}
            </span>
            <button
              onClick={() => setPagina((p) => Math.min(paginas - 1, p + 1))}
              disabled={pagina >= paginas - 1}
              className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
            >
              Siguiente →
            </button>
          </div>
        )}
      </div>

      {/* Nota metodológica */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl px-5 py-4 text-sm text-blue-800">
        <p className="font-semibold mb-1">Sobre los datos IDEAM</p>
        <p className="text-blue-700 leading-relaxed">
          Las mediciones provienen de la red de estaciones hidrometeorológicas del IDEAM distribuidas
          en todo el territorio colombiano. Cada registro corresponde a una observación diaria en una
          estación específica. Las anomalías climáticas se calculan respecto a las Normales Climatológicas
          del periodo 1961-2020, siendo esta comparación clave para el Índice de Vulnerabilidad Territorial (IVT).
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
      <div className="h-80 bg-gray-200 rounded-xl" />
      <div className="h-56 bg-gray-200 rounded-xl" />
      <div className="h-64 bg-gray-200 rounded-xl" />
    </div>
  );
}

function ErrorBanner({ msg }: { msg: string }) {
  return (
    <div className="card border border-red-200 bg-red-50 text-red-800 text-sm">
      <p className="font-semibold mb-1">Error al cargar datos IDEAM</p>
      <p className="text-red-600 font-mono text-xs">{msg}</p>
      <p className="mt-2 text-red-700">Verifica que la API esté corriendo en <code>localhost:8000</code></p>
    </div>
  );
}
