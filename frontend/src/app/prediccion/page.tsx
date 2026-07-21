"use client";

/**
 * Página del Modelo IVT — Índice de Vulnerabilidad Territorial
 *
 * Muestra el IVT actual + simulador interactivo de escenarios.
 */

import { useState, useEffect } from "react";
import { Brain, Play, RefreshCw } from "lucide-react";
import { api, IVTResultado } from "@/lib/api";
import IVTBadge from "@/components/ui/IVTBadge";

const DEFAULT_PARAMS = {
  upra_indice: 120.0,
  upra_var_pct: 1.0,
  upra_fertilizantes: 125.0,
  upra_plaguicidas: 112.0,
  precipitacion_mm: 130.0,
  temperatura_c: 23.0,
};

type ParamKey = keyof typeof DEFAULT_PARAMS;

const PARAM_META: Record<ParamKey, { label: string; min: number; max: number; step: number; unit: string }> = {
  upra_indice:        { label: "Índice UPRA total",        min: 80, max: 200, step: 0.5,  unit: "" },
  upra_var_pct:       { label: "Variación mensual UPRA",   min: -5, max: 15,  step: 0.1,  unit: "%" },
  upra_fertilizantes: { label: "Subíndice fertilizantes",  min: 80, max: 200, step: 0.5,  unit: "" },
  upra_plaguicidas:   { label: "Subíndice plaguicidas",    min: 80, max: 200, step: 0.5,  unit: "" },
  precipitacion_mm:   { label: "Precipitación mensual",    min: 0,  max: 500, step: 5,    unit: "mm" },
  temperatura_c:      { label: "Temperatura promedio",     min: 10, max: 35,  step: 0.5,  unit: "°C" },
};

export default function PrediccionPage() {
  const [actual, setActual]     = useState<IVTResultado | null>(null);
  const [params, setParams]     = useState(DEFAULT_PARAMS);
  const [simulado, setSimulado] = useState<IVTResultado | null>(null);
  const [loading, setLoading]   = useState(true);
  const [simLoading, setSimLoading] = useState(false);

  useEffect(() => {
    api.ivtActual().then(setActual).finally(() => setLoading(false));
  }, []);

  const simular = async () => {
    setSimLoading(true);
    try {
      const r = await api.ivtSimular(params);
      setSimulado(r);
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">

      {/* IVT Actual */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Brain size={20} className="text-navy" />
          <h2 className="font-semibold text-gray-900">IVT Actual — Tiempo Real</h2>
        </div>

        {loading ? (
          <div className="h-32 bg-gray-100 animate-pulse rounded-lg" />
        ) : !actual?.modelo_disponible ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
            <p className="font-semibold mb-1">⚠️ Modelo no entrenado</p>
            <p>Ejecuta el script de entrenamiento para activar el modelo:</p>
            <code className="block mt-2 bg-yellow-100 px-3 py-2 rounded font-mono text-xs">
              python -m ml.train
            </code>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col items-center justify-center py-4">
              <IVTBadge
                etiqueta={actual!.ivt!.etiqueta}
                probabilidades={actual!.ivt!.probabilidades}
                size="lg"
              />
              {actual?.interpretacion && (
                <p className="text-sm text-gray-600 mt-4 text-center leading-relaxed">
                  {actual.interpretacion}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Inputs del modelo</h3>
              {actual?.inputs && Object.entries(actual.inputs).map(([k, v]) => v !== null && (
                <div key={k} className="flex justify-between text-sm py-1 border-b border-gray-50">
                  <span className="text-gray-600">{k.replace(/_/g, " ")}</span>
                  <span className="font-mono font-medium text-gray-900">
                    {typeof v === "number" ? v.toFixed(2) : v}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Simulador */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Play size={18} className="text-teal" />
            <h2 className="font-semibold text-gray-900">Simulador de Escenarios</h2>
          </div>
          <button
            onClick={() => setParams(DEFAULT_PARAMS)}
            className="text-xs text-gray-500 flex items-center gap-1 hover:text-navy"
          >
            <RefreshCw size={12} /> Restaurar
          </button>
        </div>

        <p className="text-sm text-gray-500 mb-5">
          Ajusta los parámetros para explorar escenarios: ¿qué pasaría con el IVT si la lluvia cae a 50 mm
          y los precios de fertilizantes suben 10%?
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
          {(Object.entries(PARAM_META) as [ParamKey, typeof PARAM_META[ParamKey]][]).map(([key, meta]) => (
            <div key={key}>
              <div className="flex justify-between text-sm mb-1">
                <label className="text-gray-700 font-medium">{meta.label}</label>
                <span className="font-mono text-navy font-semibold">
                  {params[key]}{meta.unit}
                </span>
              </div>
              <input
                type="range"
                min={meta.min}
                max={meta.max}
                step={meta.step}
                value={params[key]}
                onChange={(e) => setParams((p) => ({ ...p, [key]: parseFloat(e.target.value) }))}
                className="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-navy"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-0.5">
                <span>{meta.min}{meta.unit}</span>
                <span>{meta.max}{meta.unit}</span>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={simular}
          disabled={simLoading}
          className="btn-primary flex items-center gap-2 mx-auto"
        >
          {simLoading ? (
            <><RefreshCw size={16} className="animate-spin" /> Calculando...</>
          ) : (
            <><Play size={16} /> Simular escenario</>
          )}
        </button>

        {/* Resultado de simulación */}
        {simulado && (
          <div className="mt-6 pt-6 border-t border-gray-100">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide text-center mb-4">
              Resultado de la simulación
            </h3>
            {!simulado.modelo_disponible ? (
              <p className="text-center text-sm text-gray-500">Modelo no disponible.</p>
            ) : (
              <div className="flex justify-center">
                <IVTBadge
                  etiqueta={simulado.ivt!.etiqueta}
                  probabilidades={simulado.ivt!.probabilidades}
                  size="lg"
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Explicación del modelo */}
      <div className="card bg-navy text-white">
        <h2 className="font-semibold mb-3">¿Cómo funciona el modelo IVT?</h2>
        <div className="text-sm text-white/80 space-y-2">
          <p>
            El <strong>Índice de Vulnerabilidad Territorial (IVT)</strong> es un clasificador
            Random Forest que cruza datos de 3 fuentes del gobierno colombiano para evaluar
            el estado de los territorios en una escala de Baja → Media → Alta vulnerabilidad.
          </p>
          <p>
            <strong>Features:</strong> índice UPRA, variación mensual de precios, subíndices
            de fertilizantes y plaguicidas, precipitación y temperatura IDEAM, mes del año.
          </p>
          <p>
            <strong>Transparencia:</strong> los targets de entrenamiento se generaron con una
            función de scoring ponderada y auditible — no hay caja negra.
            El código completo está en <code className="bg-white/10 px-1 rounded">ml/modelo_territorial.py</code>.
          </p>
        </div>
      </div>
    </div>
  );
}
