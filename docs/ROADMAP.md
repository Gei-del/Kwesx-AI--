# Roadmap — Fechas reales del concurso

> Actualizado el 2026-06-29 con las fechas oficiales. Reemplaza la versión anterior, que asumía "menos de 1 mes" sin hitos intermedios.

## Hitos del concurso

| Fecha | Hito | Qué se evalúa |
|---|---|---|
| **1 de julio** | Entrega 1 | Solo el documento de proyecto (propuesta). No se pide producto funcional todavía. |
| **13 al 17 de julio** | Entrega 2 | MVP funcional + pitch/sustentación ante jurado. |
| **Primera semana de agosto** | Sustentación final | Solo si quedamos entre los 9 primeros puestos. Presentación final como finalistas. |

Equipo: **Geidy** (toda la parte técnica: backend, ETL, modelos, frontend) + **Nelcy** (no técnico: documento, pitch, video, organización).

---

## Fase A — Entrega 1: Documento de proyecto (HOY → 1 de julio, ~2 días)

No requiere código. El contenido de fondo ya existe en `Kwesx_AI_Documentacion_Profesional.docx`. Lo que falta es pulirlo para entrega formal:

- Reemplazar los diagramas en texto (Anexos A, B, C) por figuras reales.
- Aplicar formato APA 7ª edición (ver Anexo D del documento: márgenes, interlineado doble, numeración de páginas, encabezado, títulos de tablas).
- Verificar y completar referencias bibliográficas.
- Revisión final de redacción.

División de trabajo sugerida: el compañero/a no técnico puede liderar el formato APA y la redacción; gei aporta precisión técnica donde se necesite (arquitectura, datasets, modelos).

**Entregable:** documento final en Word/PDF listo para subir, antes del 1 de julio.

---

## Fase B — Sprint de construcción del MVP (1 → 13 de julio, ~12 días)

Esta es la fase crítica: Geidy construye el producto sola. El alcance se mantiene deliberadamente mínimo (ver MoSCoW abajo). Plan día a día, ajustable:

| Días | Foco | Entregable |
|---|---|---|
| 1–3 (1–3 jul) | Datos | 3 datasets (ANI, UPRA, IDEAM) limpios y cargados en PostgreSQL bajo el Modelo Territorial Unificado. |
| 4–6 (4–6 jul) | Backend + IA | API FastAPI funcionando + 1 modelo de IA entrenado y validado (ej. tendencia de precios UPRA). |
| 7–9 (7–9 jul) | Asistente | Asistente Inteligente v1 (reconocimiento de intención + respuestas con datos reales) + recomendaciones básicas por reglas. |
| 10–12 (10–12 jul) | Frontend | Dashboard en Next.js: mapa interactivo, gráficas, chat del asistente, conectado a la API. |
| 13 jul | Buffer | Pulido, corrección de bugs, ensayo de demo. |

Si algo se atrasa, el orden de recorte es: primero se sacrifica el motor de recomendaciones, después un dataset adicional (si se había agregado), nunca el ETL+API+1 modelo+dashboard básico (eso es el corazón defendible del proyecto).

---

## Fase C — Entrega 2: MVP + pitch (13 al 17 de julio)

- Demo funcional en vivo o grabada como respaldo.
- Pitch deck (a cargo del Nelcy, con insumos técnicos de Geidy).
- Video demostrativo corto del producto funcionando.
- Ensayo de la sustentación.

---

## Fase D — Si quedamos en el top 9: Finalista (primera semana de agosto)

Pendiente de detallar cuando se confirme. Previsiblemente: pulir el MVP con el feedback de la Entrega 2, fortalecer el pitch, posible demo más robusta.

---

## Matriz MoSCoW del MVP (Fase B)

| Categoría | Funcionalidades |
|---|---|
| **Must have** | ETL de 3 datasets, Modelo Territorial Unificado, API funcional, 1 modelo de IA validado, Asistente básico en lenguaje natural, Dashboard con mapa interactivo. |
| **Should have** | Motor de recomendaciones por reglas, gráficas comparativas por municipio. |
| **Could have** | Dataset adicional (Educación o Transporte Masivo), exportar resultados a CSV. |
| **Won't have (este sprint)** | Modo Ciudadano/Analista separados, soporte multilingüe, capas satelitales, IA explicable completa, alertas automáticas, API pública. |

## Cómo se actualiza este roadmap

Cada cambio de alcance o de fecha se registra primero aquí y luego se explica el por qué en `docs/BITACORA.md`.
