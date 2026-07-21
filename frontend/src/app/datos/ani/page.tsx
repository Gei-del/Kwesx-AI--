"use client";

/**
 * /datos/ani — Tráfico Vehicular en Peajes · ANI
 *
 * Fuente: ANI / datos.gov.co (8yi9-t44c)
 * 151,453 registros · Peajes nacionales · Por categoría de vehículo
 */

import { useEffect, useState, useMemo } from "react";
import { Map, Truck, Filter, ChevronDown } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from "recharts";
import { api, ANIRegistro } from "@/lib/api";

// ─── Helpers ─────────────────────────────────────────────────────────────────

const COLORES = ["#1B3A6B", "#3FA796", "#F2A541", "#C0392B", "#8E44AD", "#2ECC71"];

function fmt(n: number | undefined | null) {
  if (n == null) return "—";
  return n.toLocaleString("es-CO");
}

function fmtFecha(s: string) {
  try {
    return new Date(s).toLocaleDateString("es-CO", {
      day: "2-digit", month: "short", year: "numeric"
    });
  } catch { return s; }
}

// ─── Página ──────────────────────────────────────────────────────────────────

export default function ANIPage() {
  const [datos, setDatos]         = useState<ANIRegistro[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [filtroDept, setFiltroDept] = useState("Todos");
  const [filtroCateg, setFiltroCateg] = useState("Todas");
  const [pagina, setPagina]       = useState(0);
  const POR_PAGINA = 15;

  useEffect(() => {
    api.ani({ limit: 500 })
      .then((r) => setDatos(r.datos))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Listas de filtros
  const departamentos = useMemo(() => {
    const set = new Set(datos.map((d) => d.departamento ?? "Sin geo").filter(Boolean));
    return ["Todos", ...Array.from(set).sort()];
  }, [datos]);

  const categorias = useMemo(() => {
    const set = new Set(datos.map((d) => d.categoria_tarifa).filter(Boolean));
    return ["Todas", ...Array.from(set).sort()];
  }, [datos]);

  // Aplicar filtros
  const filtrados = useMemo(() => {
    return datos.filter((d) => {
      const dept  = filtroDept === "Todos"  || (d.departamento ?? "Sin geo") === filtroDept;
      const categ = filtroCateg === "Todas" || d.categoria_tarifa === filtroCateg;
      return dept && categ;
    });
  }, [datos, filtroDept, filtroCateg]);

  // Agregación para la gráfica: tráfico por categoría
  const porCategoria = useMemo(() => {
    const map: Record<string, number> = {};
    filtrados.forEach((d) => {
      map[d.categoria_tarifa] = (map[d.categoria_tarifa] ?? 0) + d.cantidad_trafico;
    });
    return Object.entries(map)
      .map(([categ, trafico]) => ({ categ, trafico }))
      .sort((a, b) => b.trafico - a.trafico)
      .slice(0, 8);
  }, [filtrados]);

  // Agregación: top peajes por tráfico
  const topPeajes = useMemo(() => {
    const map: Record<string, { peaje: string; dept: string; trafico: number }> = {};
    filtrados.forEach((d) => {
      if (!map[d.peaje]) {
        map[d.peaje] = { peaje: d.peaje, dept: d.departamento ?? "—", trafico: 0 };
      }
      map[d.peaje].trafico += d.cantidad_trafico;
    });
    return Object.values(map).sort((a, b) => b.trafico - a.trafico).slice(0, 5);
  }, [filtrados]);

  // KPIs
  const totalTrafico  = filtrados.reduce((s, d) => s + d.cantidad_trafico, 0);
  const totalEvasores = filtrados.reduce((s, d) => s + d.cantidad_evasores, 0);
  const tasaEvasion   = totalTrafico > 0 ? (totalEvasores / totalTrafico) * 100 : 0;
  const peajesUnicos  = new Set(filtrados.map((d) => d.peaje)).size;

  // Paginación de tabla
  const paginas      = Math.ceil(filtrados.length / POR_PAGINA);
  const datosPagina  = filtrados.slice(pagina * POR_PAGINA, (pagina + 1) * POR_PAGINA);

  if (loading) return <PageSkeleton />;
  if (error)   return <ErrorBanner msg={error} />;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">

      {/* Encabezado */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Map size={20} className="text-navy" />
            <h1 className="text-lg font-semibold text-gray-900">Tráfico Vehicular en Peajes — ANI</h1>
          </div>
          <p className="text-sm text-gray-500">
            Volumen de vehículos por categoría · Fuente: ANI / datos.gov.co · {datos.length} registros cargados
          </p>
        </div>
        <span className="text-xs bg-navy/10 text-navy font-semibold px-3 py-1 rounded-full">
          Dataset 8yi9-t44c
        </span>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Vehículos (muestra)", value: fmt(totalTrafico),   sub: `${filtrados.length} registros`, color: "border-l-navy"     },
          { label: "Peajes únicos",       value: peajesUnicos,         sub: "Con datos disponibles",          color: "border-l-teal"     },
          { label: "Evasores",            value: fmt(totalEvasores),   sub: `${tasaEvasion.toFixed(1)}% tasa`, color: "border-l-red-400"  },
          { label: "Categorías",          value: categorias.length - 1, sub: "Tipos de vehículo",             color: "border-l-sand"     },
        ].map(({ label, value, sub, color }) => (
          <div key={label} className={`card border-l-4 ${color} py-3 px-4`}>
            <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
            <div className="text-xl font-bold text-gray-900 my-1">{value}</div>
            <p className="text-xs text-gray-400">{sub}</p>
          </div>
        ))}
      </div>

      {/* Filtros */}
      <div className="card py-3 px-5 flex flex-wrap gap-4 items-center">
        <Filter size={15} className="text-gray-400" />
        <span className="text-sm font-medium text-gray-600">Filtrar:</span>
        <SelectFiltro
          label="Departamento"
          options={departamentos}
          value={filtroDept}
          onChange={(v) => { setFiltroDept(v); setPagina(0); }}
        />
        <SelectFiltro
          label="Categoría"
          options={categorias}
          value={filtroCateg}
          onChange={(v) => { setFiltroCateg(v); setPagina(0); }}
        />
        {(filtroDept !== "Todos" || filtroCateg !== "Todas") && (
          <button
            onClick={() => { setFiltroDept("Todos"); setFiltroCateg("Todas"); setPagina(0); }}
            className="text-xs text-red-500 hover:text-red-700 underline"
          >
            Limpiar
          </button>
        )}
        <span className="ml-auto text-xs text-gray-400">{filtrados.length} registros</span>
      </div>

      {/* Gráfica + Top peajes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Tráfico por categoría de vehículo
          </h2>
          {porCategoria.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
              Sin datos para mostrar
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={porCategoria} layout="vertical" margin={{ left: 8, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => v.toLocaleString("es-CO")} />
                <YAxis type="category" dataKey="categ" width={100} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(v: number) => [v.toLocaleString("es-CO"), "Vehículos"]}
                  contentStyle={{ fontSize: 12, borderRadius: 8 }}
                />
                <Bar dataKey="trafico" radius={[0, 4, 4, 0]}>
                  {porCategoria.map((_, i) => (
                    <Cell key={i} fill={COLORES[i % COLORES.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Top 5 peajes
          </h2>
          <div className="space-y-3">
            {topPeajes.map((p, i) => (
              <div key={p.peaje} className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-navy text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{p.peaje}</p>
                  <p className="text-xs text-gray-400">{p.dept}</p>
                  <div className="mt-1 bg-gray-100 rounded-full h-1.5">
                    <div
                      className="bg-teal h-1.5 rounded-full"
                      style={{ width: `${(p.trafico / (topPeajes[0]?.trafico || 1)) * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{fmt(p.trafico)} vehículos</p>
                </div>
              </div>
            ))}
            {topPeajes.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-4">Sin datos</p>
            )}
          </div>
        </div>
      </div>

      {/* Tabla paginada */}
      <div className="card overflow-hidden p-0">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <Truck size={15} className="text-gray-400" />
            Registros detallados
          </h2>
          <span className="text-xs text-gray-400">
            Pág. {pagina + 1} de {paginas || 1}
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500 tracking-wide">
              <tr>
                <th className="px-4 py-3 text-left">Peaje</th>
                <th className="px-4 py-3 text-left">Depto.</th>
                <th className="px-4 py-3 text-left">Categoría</th>
                <th className="px-4 py-3 text-right">Fecha inicio</th>
                <th className="px-4 py-3 text-right">Tráfico</th>
                <th className="px-4 py-3 text-right">Evasores</th>
                <th className="px-4 py-3 text-right">Tarifa $</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {datosPagina.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-2.5 font-medium text-gray-800 max-w-[160px] truncate">{r.peaje}</td>
                  <td className="px-4 py-2.5 text-gray-600 text-xs">{r.departamento ?? "—"}</td>
                  <td className="px-4 py-2.5">
                    <span className="bg-navy/10 text-navy text-xs font-medium px-2 py-0.5 rounded-full">
                      {r.categoria_tarifa}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right text-xs text-gray-500">{fmtFecha(r.fecha_inicio)}</td>
                  <td className="px-4 py-2.5 text-right font-mono">{fmt(r.cantidad_trafico)}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-red-600">{fmt(r.cantidad_evasores)}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-gray-600">
                    {r.valor_tarifa ? `$${fmt(r.valor_tarifa)}` : "—"}
                  </td>
                </tr>
              ))}
              {datosPagina.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-400 text-sm">
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

      {/* Nota */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl px-5 py-4 text-sm text-blue-800">
        <p className="font-semibold mb-1">Sobre los datos ANI</p>
        <p className="text-blue-700 leading-relaxed">
          El dataset incluye el volumen de tráfico en peajes de la red vial concesionada de Colombia
          por categoría de vehículo (automóviles, camiones, buses, etc.) y período. La geolocalización
          se enriqueció mediante el diccionario <code className="bg-blue-100 px-1 rounded">PEAJES_DANE</code> que
          mapea cada peaje a su municipio DANE correspondiente, permitiendo el cruce territorial con UPRA e IDEAM.
        </p>
      </div>
    </div>
  );
}

// ─── Sub-componentes ──────────────────────────────────────────────────────────

function SelectFiltro({
  label, options, value, onChange
}: { label: string; options: string[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none text-sm border border-gray-200 rounded-lg px-3 py-1.5 pr-7 text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-navy/20"
      >
        {options.map((o) => <option key={o}>{o}</option>)}
      </select>
      <ChevronDown size={13} className="absolute right-2 top-2.5 text-gray-400 pointer-events-none" />
    </div>
  );
}

function PageSkeleton() {
  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3" />
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-gray-200 rounded-xl" />)}
      </div>
      <div className="h-12 bg-gray-200 rounded-xl" />
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 h-64 bg-gray-200 rounded-xl" />
        <div className="h-64 bg-gray-200 rounded-xl" />
      </div>
      <div className="h-64 bg-gray-200 rounded-xl" />
    </div>
  );
}

function ErrorBanner({ msg }: { msg: string }) {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="card border border-warm-200 bg-warm-50 text-center py-12 px-6">
        <div className="w-16 h-16 bg-warm-100 rounded-3xl flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">🛣️</span>
        </div>
        <h2 className="text-lg font-bold text-warm-800 mb-2">
          Datos no disponibles por ahora
        </h2>
        <p className="text-warm-500 text-sm max-w-sm mx-auto leading-relaxed">
          No fue posible conectarse con el servidor de datos ANI.
          Cuando el servicio esté activo, aquí verás el estado del tráfico,
          concesiones viales y condición de carreteras en Colombia.
        </p>
        <div className="mt-6 flex items-center justify-center gap-2">
          <button
            onClick={() => window.location.reload()}
            className="btn-primary text-sm px-5 py-2.5"
          >
            Reintentar
          </button>
          <a
            href="https://www.datos.gov.co/Transporte/Informaci-n-Peajes-Informaci-n-de-Recaudos-de-P/8yi9-t44c"
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
