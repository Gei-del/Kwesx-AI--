"use client";

/**
 * ColombiaMap.tsx
 * ---------------
 * Mapa interactivo de Colombia usando React-Leaflet.
 *
 * Muestra puntos de las estaciones IDEAM con color según el tipo de
 * variable (precipitación = azul, temperatura = naranja).
 *
 * IMPORTANTE: Leaflet no funciona en SSR (no tiene acceso a window).
 * Este componente se importa con `dynamic(..., { ssr: false })` desde
 * la página que lo usa.
 */

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { IDEAMRegistro } from "@/lib/api";

interface ColombiaMapProps {
  puntos: IDEAMRegistro[];
}

const COLOR: Record<string, string> = {
  precipitacion_mm: "#2E8C84",
  temperatura_c:    "#F2A541",
};

export default function ColombiaMap({ puntos }: ColombiaMapProps) {
  // Filtrar solo los que tienen coordenadas
  const conCoordenadas = puntos.filter(
    (p) => p.latitud !== null && p.longitud !== null
  );

  return (
    <MapContainer
      center={[4.5709, -74.2973]}  // centroide de Colombia
      zoom={5}
      style={{ height: "100%", width: "100%", borderRadius: "0.75rem" }}
      scrollWheelZoom={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {conCoordenadas.map((punto) => (
        <CircleMarker
          key={punto.id}
          center={[punto.latitud!, punto.longitud!]}
          radius={5}
          pathOptions={{
            color: COLOR[punto.tipo_variable] || "#1B3B5F",
            fillColor: COLOR[punto.tipo_variable] || "#1B3B5F",
            fillOpacity: 0.7,
            weight: 1,
          }}
        >
          <Popup>
            <div className="text-sm">
              <p className="font-semibold">{punto.nombre_estacion}</p>
              <p className="text-gray-600">{punto.municipio}, {punto.departamento}</p>
              <p className="mt-1">
                <span className="font-medium">
                  {punto.tipo_variable === "precipitacion_mm" ? "☁️ Precipitación" : "🌡️ Temperatura"}:
                </span>{" "}
                {punto.valor_observado} {punto.unidad_medida}
              </p>
              <p className="text-gray-400 text-xs mt-1">{punto.fecha}</p>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
