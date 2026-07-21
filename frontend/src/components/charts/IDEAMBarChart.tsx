"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from "recharts";

interface IDEAMBarChartProps {
  datos: Array<{
    departamento: string | null;
    valor_observado: number;
    tipo_variable: string;
  }>;
  tipo: "precipitacion_mm" | "temperatura_c";
}

const COLORES_PRECIPITACION = ["#7FC8BC", "#3FA796", "#2E8C84", "#1B6B68", "#155E63"];
const COLORES_TEMPERATURA    = ["#F2A541", "#E8892A", "#D96F1C", "#C05510", "#9C3D08"];

export default function IDEAMBarChart({ datos, tipo }: IDEAMBarChartProps) {
  // Agrupar por departamento y promediar
  const porDepto: Record<string, number[]> = {};
  datos.forEach((d) => {
    const key = d.departamento || "Desconocido";
    if (!porDepto[key]) porDepto[key] = [];
    porDepto[key].push(d.valor_observado);
  });

  const chartData = Object.entries(porDepto)
    .map(([depto, values]) => ({
      depto: depto.slice(0, 10),
      valor: parseFloat((values.reduce((a, b) => a + b, 0) / values.length).toFixed(2)),
    }))
    .sort((a, b) => b.valor - a.valor)
    .slice(0, 10); // Top 10

  const colores = tipo === "precipitacion_mm" ? COLORES_PRECIPITACION : COLORES_TEMPERATURA;
  const unidad  = tipo === "precipitacion_mm" ? "mm" : "°C";

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fontSize: 11, fill: "#6b7280" }}
          tickLine={false}
          unit={unidad}
        />
        <YAxis
          type="category"
          dataKey="depto"
          tick={{ fontSize: 11, fill: "#374151" }}
          tickLine={false}
          axisLine={false}
          width={80}
        />
        <Tooltip
          formatter={(value: number) => [`${value} ${unidad}`, "Promedio"]}
          contentStyle={{ borderRadius: "8px", fontSize: 12 }}
        />
        <Bar dataKey="valor" radius={[0, 4, 4, 0]}>
          {chartData.map((_, index) => (
            <Cell
              key={index}
              fill={colores[index % colores.length]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
