"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";

interface UPRAChartProps {
  datos: Array<{
    fecha: string;
    indice_total: number;
    total_fertilizantes: number;
    total_plaguicidas: number;
    variacion_mensual_pct?: number;
  }>;
}

export default function UpraLineChart({ datos }: UPRAChartProps) {
  const formatted = datos.map((d) => ({
    ...d,
    mes: format(parseISO(d.fecha), "MMM yy", { locale: es }),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={formatted} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="mes"
          tick={{ fontSize: 11, fill: "#6b7280" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#6b7280" }}
          tickLine={false}
          axisLine={false}
          domain={["auto", "auto"]}
        />
        <Tooltip
          contentStyle={{
            borderRadius: "8px",
            border: "1px solid #e5e7eb",
            fontSize: 12,
          }}
          formatter={(value: number, name: string) => [
            value.toFixed(2),
            name === "indice_total" ? "Índice Total" :
            name === "total_fertilizantes" ? "Fertilizantes" : "Plaguicidas",
          ]}
        />
        <Legend
          formatter={(value) =>
            value === "indice_total" ? "Índice Total" :
            value === "total_fertilizantes" ? "Fertilizantes" : "Plaguicidas"
          }
        />
        <Line
          type="monotone"
          dataKey="indice_total"
          stroke="#1B3B5F"
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 5 }}
        />
        <Line
          type="monotone"
          dataKey="total_fertilizantes"
          stroke="#3FA796"
          strokeWidth={1.5}
          dot={false}
          strokeDasharray="4 2"
        />
        <Line
          type="monotone"
          dataKey="total_plaguicidas"
          stroke="#F2A541"
          strokeWidth={1.5}
          dot={false}
          strokeDasharray="4 2"
        />
        {/* Línea de referencia en base 100 */}
        <ReferenceLine y={100} stroke="#9ca3af" strokeDasharray="3 3" label={{ value: "Base 100", position: "right", fontSize: 10, fill: "#9ca3af" }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
