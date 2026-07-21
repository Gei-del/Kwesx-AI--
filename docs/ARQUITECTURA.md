# Arquitectura de Kwesx AI

Este documento traduce la visión completa del proyecto (ver el .docx original) a decisiones técnicas concretas para el MVP del concurso. Lo que está marcado **[MVP]** se construye ahora. Lo marcado **[FUTURO]** queda documentado pero no se implementa en este sprint.

## 1. Stack tecnológico (decisión cerrada)

| Capa | Tecnología | Por qué |
|---|---|---|
| Backend / API | Python + FastAPI | Rápido de levantar, tipado, ideal para servir modelos de ML y endpoints REST. |
| Base de datos | PostgreSQL + PostGIS | PostGIS da soporte geoespacial nativo (consultas por municipio, distancias, polígonos). |
| ETL / Ciencia de datos | Pandas, NumPy, Scikit-learn | Estándar de la industria, buena documentación, el equipo ya tiene base. |
| Geoespacial | GeoPandas + Leaflet (frontend) | Leaflet es liviano y rápido de integrar en React. Folium/Kepler.gl quedan como [FUTURO] si hay tiempo. |
| Frontend | Next.js + React + TypeScript + Tailwind CSS | Como define el documento original. |
| Modelos de IA | 1 modelo supervisado (Random Forest o Gradient Boosting) | Se prioriza UN modelo bien validado en vez de varios modelos a medias. |

## 2. Las 6 capas del documento original — qué se hace ahora

1. **Arquitectura Funcional** — módulos: Asistente Inteligente, Dashboard Territorial. **[MVP]**. Explorador de Datasets, Centro de Reportes, Modo Ciudadano/Analista: **[FUTURO]**.
2. **Arquitectura de Datos** — Motor ETL simple (extracción → limpieza → estandarización → carga) sobre 3 datasets. **[MVP]**. ETL con versionado y enriquecimiento avanzado: **[FUTURO]**.
3. **Arquitectura de IA** — 1 modelo predictivo + asistente de lenguaje natural basado en reconocimiento de intención (no NLP profundo). **[MVP]**. Embeddings semánticos, Explainable AI completo: **[FUTURO]**.
4. **Arquitectura Geoespacial** — mapa interactivo con Leaflet sobre datos por municipio (Código DANE). **[MVP]**. Capas satelitales (Sentinel-2, Landsat), PostGIS avanzado: **[FUTURO]**.
5. **Arquitectura Tecnológica** — ver tabla del stack arriba. **[MVP]**.
6. **Seguridad y Gobernanza** — control de versiones en git, variables de entorno para credenciales. **[MVP]** a nivel básico. Auditoría completa, despliegue cloud productivo: **[FUTURO]**.

## 3. Datasets del MVP (recorte de 6 a 3)

El documento original proponía 6 datasets. Para caber en menos de un mes, el MVP arranca con los **3 de prioridad "Muy Alta"** según la Matriz de Inteligencia de Datos del documento original:

| Dataset | Fuente | Por qué es el núcleo |
|---|---|---|
| Tráfico Vehicular | ANI | Mayor cantidad de variables + mayor potencial geoespacial. |
| Índice de Precios de Insumos Agrícolas | UPRA | Es el reto oficial del concurso (UPRA) — alto valor para el jurado. |
| Variables Climáticas | IDEAM | Da contexto a los otros dos (clima afecta movilidad y agricultura). |

Si el tiempo lo permite, se agregan Educación Superior (MEN) y Pasajeros Transporte Masivo como datasets adicionales — pero no son bloqueantes para la entrega.

## 4. Modelo Territorial Unificado (MTU) — simplificado

Igual que en el documento original, la clave de integración es el **Código DANE** del municipio. Variables maestras para el MVP:

- `codigo_dane` (clave principal)
- `departamento`
- `municipio`
- `latitud`, `longitud`
- `fecha` (año/mes)
- `sector` (transporte / agricultura / clima)
- `fuente` (trazabilidad del dato)

Cada dataset, sin importar su fuente original, se transforma en el ETL para tener estas columnas antes de cargarse a PostgreSQL.

## 5. Decisiones abiertas / por confirmar

- **Asistente conversacional**: ¿reglas + plantillas (rápido, controlable) o integrar una API de LLM externa (más natural, pero depende de un servicio externo y su costo)? — Se decide al iniciar la Semana 2 del roadmap.
- **Hosting/despliegue**: por definir según lo que el equipo ya tenga disponible (Vercel para frontend es buena opción; backend puede ir en Render/Railway).

## 6. Diagrama de flujo (texto, del documento original)

```
Datos abiertos → Integración ETL → Análisis Territorial → Modelos IA
→ Visualización → Recomendaciones → Toma de decisiones
```

Este diagrama se reemplazará por una figura real (Figma/draw.io) antes de la entrega final.
