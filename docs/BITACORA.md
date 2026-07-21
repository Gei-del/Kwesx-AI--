# Bitácora del proyecto

Diario cronológico de Kwesx AI. Cada entrada responde: ¿qué se hizo?, ¿qué se decidió y por qué?, ¿qué sigue?. El objetivo es que cualquier persona (incluida la propia gei en el futuro) pueda entender el proyecto leyendo solo este archivo de arriba hacia abajo.

---

## 2026-06-29 — Kickoff del proyecto

**Qué se hizo:**
- Se analizó el documento base `Kwesx_AI_Documentacion_Profesional.docx` (visión completa del proyecto para el Concurso Datos al Ecosistema 2026, Nivel Intermedio).
- Se creó la estructura inicial del repositorio: `backend/`, `frontend/`, `etl/`, `data/`, `docs/`.
- Se creó la documentación base: `README.md`, `docs/ARQUITECTURA.md`, `docs/ROADMAP.md`, `docs/EQUIPO.md`.

**Qué se decidió y por qué:**
- El plazo de entrega es de **menos de 1 mes**, así que se recortó el alcance del MVP original (6 datasets → 3 datasets de prioridad "Muy Alta": ANI Tráfico Vehicular, UPRA Insumos Agrícolas, IDEAM Variables Climáticas). Razón: garantizar que todo lo comprometido se pueda terminar y demostrar, en vez de tener muchos módulos a medias.
- Stack técnico confirmado: FastAPI + PostgreSQL/PostGIS en backend, Next.js/React/TypeScript/Tailwind en frontend (igual al documento original).
- El asistente conversacional se construirá primero con reconocimiento de intención + plantillas (no NLP/LLM pesado), para tener algo funcional y confiable rápido. Se evaluará integrar un LLM externo en la Semana 2 si el tiempo lo permite.
- Se intentó inicializar git automáticamente desde el entorno de trabajo, pero la carpeta sincronizada presentó errores de filesystem con `git init`. **Acción pendiente para gei:** ejecutar `git init` directamente en una terminal en tu computador, dentro de la carpeta `Kwesx IA`, ya que ahí sí funcionará sin problema.

**Qué sigue:**
- Confirmar integrantes del equipo y roles (`docs/EQUIPO.md` queda con placeholder).
- Iniciar Semana 1 del roadmap: entorno de desarrollo + exploración de los 3 datasets priorizados.

---

## 2026-06-29 — Fechas reales del concurso y ajuste de roadmap

**Qué se hizo:**
- Se confirmaron las fechas oficiales del concurso: Entrega 1 el 1 de julio (solo documento de proyecto), Entrega 2 del 13 al 17 de julio (MVP funcional + pitch), y sustentación de finalistas la primera semana de agosto (si quedamos en el top 10).
- Se confirmó el equipo: 2 personas. gei (desarrolladora de software y ciencia de datos, asume todo lo técnico) + un/a compañero/a no técnico (documento, pitch, video, organización).
- Se reescribió `docs/ROADMAP.md` con 4 fases ancladas a fechas reales en lugar del estimado genérico de "menos de 1 mes".

**Qué se decidió y por qué:**
- La Entrega 1 (1 de julio) no requiere producto funcional, solo el documento — así que el esfuerzo de los próximos 2 días se concentra en pulir `Kwesx_AI_Documentacion_Profesional.docx` (diagramas reales, formato APA, referencias), no en código.
- El sprint real de construcción del MVP queda entre el 1 y el 13 de julio (~12 días). Como gei es la única persona técnica, el alcance se mantiene al mínimo defendible: 3 datasets, 1 modelo de IA, asistente básico, dashboard simple. Se definió un orden de recorte explícito en caso de atraso (ver `docs/ROADMAP.md` Fase B).

**Qué sigue:**
- Pulir el documento de proyecto para la Entrega 1 (figuras reales en vez de diagramas de texto, formato APA, referencias).
- Una vez enviada la Entrega 1, iniciar Día 1 del sprint MVP: entorno de desarrollo + ETL de los 3 datasets.

---

## 2026-06-29 — Documento final para la Entrega 1

**Qué se hizo:**
- Se generaron 3 figuras reales (PNG) a partir de los diagramas de texto de los Anexos A, B y C del documento original: arquitectura por capas, ciclo de inteligencia territorial y arquitectura modular del MVP. Quedaron guardadas en `docs/figuras/`.
- Se reescribió todo el contenido del documento (Introducción, Capítulos 1 a 11, Conclusiones, Referencias y Anexos) en un tono más humano y estudiantil, manteniendo intactos todos los datos, tablas y cifras del documento original.
- Se construyó `Kwesx_AI_Documento_Proyecto_Entrega1.docx` con formato APA 7.ª edición: márgenes de 2,54 cm, interlineado doble en el cuerpo y sencillo en tablas, numeración de página desde la portada, encabezado con el título abreviado, títulos de tabla en negrita y pies de figura en cursiva.
- Se quitó el Anexo D (la nota de recomendaciones de formato) y las demás notas entre corchetes, porque ya no aplican: este documento es la versión final, no un borrador de trabajo.
- Se validó el archivo (`validate.py`) y se revisó visualmente convirtiéndolo a PDF: portada, tablas y las 3 figuras se ven correctamente.

**Qué se decidió y por qué:**
- No se inventaron referencias académicas nuevas para la sección de Referencias Bibliográficas (la nota original lo sugería). Se prefirió mantener solo las fuentes institucionales reales citadas en el texto, para no comprometer la honestidad académica del documento.

**Qué sigue:**
- Revisar el documento entre las dos integrantes antes de subirlo el 1 de julio.
- Subir `Kwesx_AI_Documento_Proyecto_Entrega1.docx` a la plataforma del concurso.
- Después de la entrega, arrancar el Día 1 de la Fase B del roadmap: entorno de desarrollo + ETL de los 3 datasets priorizados (ANI, UPRA, IDEAM).

---

## 2026-06-30 — Sprint técnico: ETL + Backend FastAPI (Día 1 de Fase B)

**Qué se hizo:**
- Se confirmaron los IDs reales de los 3 datasets en datos.gov.co (API Socrata):
  - ANI Tráfico Vehicular: `8yi9-t44c` — 151,453 filas
  - UPRA Insumos Agrícolas: `gwbi-fnzs` — 89 filas (serie mensual 2021–2026)
  - IDEAM Precipitación: `s54a-sgyg` — actualización diaria, con dept/municipio/lat/lon
  - IDEAM Temperatura: `sbwg-7ju4` — mismo schema, actualización diaria
  - IDEAM Catálogo de Estaciones: `hp9r-jxuu` — para lookup de código DANE
- Se construyó la infraestructura base del proyecto:
  - `requirements.txt`, `.env.example`, `docker-compose.yml`, `Dockerfile`, `db/init.sql`
- Se implementó el pipeline ETL completo:
  - `etl/config.py` — configuración centralizada, IDs de datasets, parámetros
  - `etl/extractors/base.py` — clase `SocrataExtractor` con paginación y reintentos
  - `etl/extractors/ani.py` — extractor ANI + lookup de ~30 peajes a código DANE
  - `etl/extractors/upra.py` — extractor UPRA (índice mensual nacional)
  - `etl/extractors/ideam.py` — extractor IDEAM (precipitación + temperatura)
  - `etl/transformers/normalize.py` — normalizadores al MTU (ANINormalizer, UPRANormalizer, IDEAMNormalizer)
  - `etl/loaders/postgres.py` — loader con INSERT bulk + ON CONFLICT DO NOTHING
  - `etl/pipeline.py` — orquestador con CLI (`--fuente`, `--desde`, `--dry-run`)
- Se definió el schema de BD (Modelo Territorial Unificado):
  - `backend/app/models/mtu.py` — 3 tablas SQLAlchemy: `mtu_ani`, `mtu_upra`, `mtu_ideam`
  - Restricciones UNIQUE para evitar duplicados en cargas incrementales
  - Índices compuestos en `codigo_dane + fecha` para queries rápidas
- Se construyó el scaffold de la API FastAPI:
  - `backend/app/main.py` — app FastAPI con CORS y 3 routers registrados
  - `backend/app/config.py` — Settings con pydantic-settings
  - `backend/app/database.py` — motor async (asyncpg) + get_db dependency
  - `backend/app/routers/datos.py` — 7 endpoints de consulta al MTU
  - `backend/app/routers/asistente.py` — asistente conversacional MVP (keyword-based)
  - `backend/app/routers/salud.py` — health checks para Docker

**Qué se decidió y por qué:**
- UPRA se almacena con `codigo_dane = '00'` (convenio Kwesx AI para datos nacionales). Es un índice nacional, no tiene desglose geográfico. En el dashboard se mostrará como tendencia temporal, no como mapa.
- ANI no tiene lat/lon ni código DANE. Se resuelve con un diccionario manual de ~30 peajes principales. Los peajes no mapeados quedan con coordenadas NULL — funcional para el MVP, se amplía después.
- Para IDEAM se usan 2 datasets complementarios (precipitación + temperatura) en vez de uno solo, porque no existe un único dataset "variables climáticas" — cada variable tiene su propio dataset. El campo `tipo_variable` los discrimina en la tabla `mtu_ideam`.
- El asistente conversacional v1 usa reconocimiento por palabras clave (sin LLM). Decisión de velocidad: es funcional, honesto sobre sus limitaciones y se puede demostrar sin dependencias externas. Si sobra tiempo antes del 13 julio, se integra un LLM.
- Se usó `INSERT ... ON CONFLICT DO NOTHING` en el loader para que el ETL sea re-ejecutable sin duplicar datos.

**Qué sigue:**
- Levantar el entorno local: `docker compose up -d` + `pip install -r requirements.txt`
- Ejecutar el ETL en modo dry-run para verificar extracción: `python -m etl.pipeline --dry-run`
- Ejecutar el ETL real: `python -m etl.pipeline`
- Correr la API: `uvicorn backend.app.main:app --reload`
- Verificar en `http://localhost:8000/docs` que los endpoints responden
- Siguiente fase: frontend Next.js (dashboard con mapa + gráficas)

---

<!-- Próxima entrada: copiar el formato de arriba (fecha, qué se hizo, qué se decidió y por qué, qué sigue). -->
