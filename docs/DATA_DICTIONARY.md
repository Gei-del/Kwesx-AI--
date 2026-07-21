# Diccionario de Datos — Kwesx AI
**Modelo Territorial Unificado (MTU) v1.0**  
Fecha: Julio 2026 | Sistema: Kwesx AI Territorial Intelligence Platform

---

## Resumen

El MTU integra datos de 5 fuentes gubernamentales colombianas en un esquema normalizado
que permite análisis cruzados y modelos de IA territorial. Todas las tablas comparten
columnas base (código DANE, departamento, municipio, fecha, fuente).

| Tabla               | Fuente          | Registros aprox. | Frecuencia | Tipo     |
|---------------------|-----------------|-------------------|------------|----------|
| `mtu_ani`           | ANI             | 500K+             | Mensual    | Tráfico  |
| `mtu_upra`          | UPRA            | 60+               | Mensual    | Precios  |
| `mtu_ideam`         | IDEAM           | 200K+             | Diaria     | Clima    |
| `mtu_conectividad`  | DANE + MinTIC   | 2K+               | Anual      | Digital  |
| `mtu_educacion`     | MEN (SIMAT)     | 5K+               | Anual      | Social   |

---

## 1. Tabla `mtu_ani` — ANI Tráfico Vehicular en Peajes

**Fuente**: Agencia Nacional de Infraestructura (ANI)  
**API**: `https://www.datos.gov.co/resource/8yi9-t44c.json`  
**Granularidad**: Peaje × Categoría vehicular × Período (mensual)

| Variable              | Tipo      | Valores posibles / Rango  | Descripción                                                |
|-----------------------|-----------|---------------------------|------------------------------------------------------------|
| `id`                  | Integer   | Auto                      | Identificador interno MTU                                  |
| `codigo_dane`         | String(5) | ej. "05001"               | Código DANE del municipio donde está el peaje              |
| `departamento`        | String    | "Antioquia", "Valle", …   | Nombre del departamento                                    |
| `municipio`           | String    | "Medellín", "Cali", …     | Nombre del municipio                                       |
| `latitud`             | Float     | [-4.2, 12.5]              | Latitud geográfica del peaje                               |
| `longitud`            | Float     | [-79.0, -66.8]            | Longitud geográfica del peaje                              |
| `fecha`               | Date      | YYYY-MM-DD                | Fecha de inicio del período de medición                    |
| `idpeaje`             | String    | ej. "PEA-001"             | Código interno ANI del punto de peaje                      |
| `peaje`               | String    | ej. "El Vino"             | Nombre oficial del punto de peaje                          |
| `categoria_tarifa`    | String    | "I", "II", "III", …       | Categoría vehicular ANI (I=motos, II=autos, III=camiones+) |
| `fecha_inicio`        | Date      | YYYY-MM-DD                | Inicio del período de conteo                               |
| `fecha_fin`           | Date      | YYYY-MM-DD                | Fin del período de conteo                                  |
| `valor_tarifa`        | Float     | [0, 150000] COP           | Tarifa cobrada en el período (pesos colombianos)           |
| `cantidad_trafico`    | Integer   | [0, ∞)                    | Vehículos que pagaron tarifa en el período                 |
| `cantidad_evasores`   | Integer   | [0, ∞)                    | Vehículos que evadieron el cobro                           |
| `cantidad_exentos`    | Integer   | [0, ∞)                    | Vehículos exentos de pago (emergencias, etc.)              |
| `fuente`              | String    | "ANI"                     | Identificador de la fuente de datos                        |

**Notas**:
- `pct_evasion` se calcula como `cantidad_evasores / (cantidad_trafico + cantidad_evasores) * 100`
- Un peaje puede tener 4-6 registros por mes (uno por categoría vehicular)
- Los valores `NULL` en `codigo_dane` indican peajes cuya ubicación no pudo geocodificarse

---

## 2. Tabla `mtu_upra` — Índice de Precios de Insumos Agrícolas

**Fuente**: Unidad de Planificación Rural Agropecuaria (UPRA)  
**API**: `https://www.datos.gov.co/resource/gwbi-fnzs.json`  
**Granularidad**: Nacional × Mes

| Variable              | Tipo      | Valores posibles / Rango  | Descripción                                                |
|-----------------------|-----------|---------------------------|------------------------------------------------------------|
| `id`                  | Integer   | Auto                      | Identificador interno MTU                                  |
| `codigo_dane`         | String(5) | "00"                      | Código nacional (sin desglose geográfico)                  |
| `fecha`               | Date      | YYYY-MM-DD (día 1)        | Primer día del mes al que corresponde el índice            |
| `indice_total`        | Float     | [80, 200]                 | Índice compuesto de precios de insumos (base 100 = 2018)   |
| `total_fertilizantes` | Float     | [80, 200]                 | Subíndice de fertilizantes (nitrogenados, fosforados, etc.)|
| `total_plaguicidas`   | Float     | [80, 200]                 | Subíndice de plaguicidas (herbicidas, insecticidas, funig.)|
| `total_otros`         | Float     | [80, 200]                 | Subíndice de otros insumos (semillas, agroquímicos, etc.)  |
| `fuente`              | String    | "UPRA"                    | Identificador de la fuente                                 |

**Variables derivadas (calculadas en API)**:
- `variacion_mensual_pct`: `(indice_actual - indice_anterior) / indice_anterior * 100`
- `ivt_weight_upra`: Peso del índice UPRA en el IVT = `0.40`

**Interpretación del índice**:
- `< 95`: Precios bajos respecto a base 2018 (favorable para productores)
- `95–110`: Rango normal
- `> 110`: Presión inflacionaria en insumos (alerta MEDIA)
- `> 130`: Presión alta — puede reducir rentabilidad agrícola (alerta ALTA)

---

## 3. Tabla `mtu_ideam` — Variables Climáticas

**Fuente**: Instituto de Hidrología, Meteorología y Estudios Ambientales (IDEAM)  
**APIs**: 
  - Precipitación: `https://www.datos.gov.co/resource/s54a-sgyg.json`
  - Temperatura: `https://www.datos.gov.co/resource/sbwg-7ju4.json`  
**Granularidad**: Estación × Sensor × Fecha

| Variable              | Tipo      | Valores posibles / Rango         | Descripción                                                |
|-----------------------|-----------|----------------------------------|------------------------------------------------------------|
| `id`                  | Integer   | Auto                             | Identificador interno MTU                                  |
| `codigo_dane`         | String(5) | ej. "05001"                      | Código DANE del municipio de la estación                   |
| `departamento`        | String    | "Antioquia", …                   | Departamento de la estación meteorológica                  |
| `municipio`           | String    | "Medellín", …                    | Municipio de la estación                                   |
| `latitud`             | Float     | [-4.2, 12.5]                     | Latitud de la estación                                     |
| `longitud`            | Float     | [-79.0, -66.8]                   | Longitud de la estación                                    |
| `fecha`               | Date      | YYYY-MM-DD                       | Fecha de la medición                                       |
| `codigo_estacion`     | String    | ej. "2120609"                    | Código oficial IDEAM de la estación                        |
| `nombre_estacion`     | String    | ej. "Sta. Ana [21206090]"        | Nombre descriptivo de la estación                          |
| `codigo_sensor`       | String    | ej. "PTPM_TT_M"                  | Código del sensor/variable medida                          |
| `tipo_variable`       | String    | "precipitacion_mm", "temperatura_c" | Tipo de variable observada                              |
| `valor_observado`     | Float     | Precipitación: [0, 800] mm/mes; Temperatura: [0, 42] °C | Valor de la medición |
| `unidad_medida`       | String    | "mm", "°C"                       | Unidad de la variable                                      |
| `zona_hidrografica`   | String    | "Magdalena", "Caribe", …         | Zona hidrográfica de Colombia                              |
| `fuente`              | String    | "IDEAM"                          | Identificador de la fuente                                 |

**Umbrales de alerta IVT**:
- Precipitación promedio < 5 mm (7 días) → posible sequía (ALTA)
- Precipitación promedio > 150 mm (7 días) → riesgo inundación (ALTA)
- Temperatura promedio > 30°C → estrés térmico (MEDIA)

---

## 4. Tabla `mtu_conectividad` — Brecha Digital Municipal

**Fuente**: DANE Encuesta de Calidad de Vida (ECV) + MinTIC  
**Granularidad**: Municipio × Año × Zona (urbana/rural)

| Variable              | Tipo      | Valores posibles / Rango  | Descripción                                                |
|-----------------------|-----------|---------------------------|------------------------------------------------------------|
| `id`                  | Integer   | Auto                      | Identificador interno MTU                                  |
| `codigo_dane`         | String(5) | ej. "05001"               | Código DANE del municipio                                  |
| `departamento`        | String    | "Antioquia", …            | Nombre del departamento                                    |
| `municipio`           | String    | "Medellín", …             | Nombre del municipio                                       |
| `anio`                | Integer   | [2020, 2026]              | Año de la encuesta / reporte                               |
| `pct_hogares_internet`| Float     | [0, 100] %                | Porcentaje de hogares con acceso a internet                |
| `pct_hogares_celular` | Float     | [0, 100] %                | Porcentaje de hogares con teléfono celular                 |
| `pct_hogares_pc`      | Float     | [0, 100] %                | Porcentaje de hogares con computador o tablet              |
| `tipo_conexion`       | String    | "fija", "movil", "mixta"  | Tipo predominante de conexión                              |
| `velocidad_mbps`      | Float     | [0, 1000] Mbps            | Velocidad promedio de bajada                               |
| `poblacion`           | Integer   | [0, 10M+]                 | Población total del municipio (DANE)                       |
| `zona`                | String    | "urbana", "rural", "total"| Zona geográfica de desagregación                          |
| `fuente`              | String    | "DANE-MinTIC", "DANE-MinTIC-SIMULADO" | Fuente de los datos                             |

**Brecha digital Colombia (referencia ECV 2023)**:
- Urbana: 62% de hogares con internet
- Rural: 26% de hogares con internet
- Brecha urbano-rural: 36 puntos porcentuales

---

## 5. Tabla `mtu_educacion` — Cobertura Educativa

**Fuente**: Ministerio de Educación Nacional (MEN) — SIMAT  
**Granularidad**: Municipio × Nivel educativo × Año

| Variable              | Tipo      | Valores posibles / Rango   | Descripción                                               |
|-----------------------|-----------|----------------------------|-----------------------------------------------------------|
| `id`                  | Integer   | Auto                       | Identificador interno MTU                                 |
| `codigo_dane`         | String(5) | ej. "05001"                | Código DANE del municipio                                 |
| `anio`                | Integer   | [2018, 2026]               | Año escolar                                               |
| `nivel_educativo`     | String    | "preescolar", "primaria", "secundaria", "media" | Nivel educativo       |
| `matriculados`        | Integer   | [0, 2M+]                   | Total de estudiantes matriculados                         |
| `matriculados_oficial`| Integer   | [0, 2M+]                   | Matriculados en colegios oficiales (públicos)             |
| `matriculados_privado`| Integer   | [0, 500K+]                 | Matriculados en colegios no oficiales (privados)          |
| `tasa_cobertura_neta` | Float     | [0, 100] %                 | Matriculados en edad oficial / población en edad (%)      |
| `tasa_cobertura_bruta`| Float     | [0, 120] %                 | Total matriculados / población en edad (puede >100%)      |
| `tasa_aprobacion`     | Float     | [0, 100] %                 | Estudiantes que aprueban el año / total matriculados (%)  |
| `tasa_desercion`      | Float     | [0, 30] %                  | Estudiantes que abandonan en el año / total (%)           |
| `zona`                | String    | "total", "urbana", "rural" | Zona geográfica de desagregación                         |
| `fuente`              | String    | "MEN-SIMAT", "MEN-SIMAT-SIMULADO" | Fuente de los datos                                |

**Promedios nacionales Colombia 2022 (MEN)**:
- Primaria: cobertura neta 87%
- Secundaria: cobertura neta 68%
- Media: cobertura neta 34%
- Tasa de deserción: 3.1% primaria, 4.8% secundaria

---

## Columnas MTU Compartidas

Todas las tablas incluyen estas columnas comunes del esquema MTU:

| Columna     | Tipo      | Descripción                                           |
|-------------|-----------|-------------------------------------------------------|
| `id`        | Integer   | PK autoincremental                                    |
| `codigo_dane`| String(5)| Código DANE del municipio (5 dígitos, "00" = nacional)|
| `departamento`| String  | Nombre del departamento                               |
| `municipio` | String    | Nombre del municipio                                  |
| `latitud`   | Float     | Latitud WGS84 (puede ser NULL si no geocodificado)    |
| `longitud`  | Float     | Longitud WGS84 (puede ser NULL si no geocodificado)   |
| `fecha`     | Date      | Fecha del dato (ISO 8601)                             |
| `sector`    | String    | Sector temático: "transporte", "agropecuario", etc.   |
| `fuente`    | String    | Identificador de la fuente oficial                    |
| `created_at`| DateTime  | Timestamp de inserción en el MTU                      |

---

## Variables del Modelo IVT (Índice de Vulnerabilidad Territorial)

El modelo Ensemble (Random Forest 45% + XGBoost 55%) usa 10 variables:

| Variable                  | Fuente | Descripción                                    | Peso IVT |
|---------------------------|--------|------------------------------------------------|----------|
| `upra_indice_total`       | UPRA   | Índice mensual de precios de insumos           | 0.40×    |
| `upra_var_mensual_pct`    | UPRA   | Variación porcentual mensual del índice        | 0.40×    |
| `upra_fertilizantes`      | UPRA   | Subíndice de fertilizantes                     | 0.40×    |
| `upra_plaguicidas`        | UPRA   | Subíndice de plaguicidas                       | 0.40×    |
| `ideam_precipitacion_mm`  | IDEAM  | Precipitación mensual promedio (mm)            | 0.35×    |
| `ideam_precip_anomalia`   | IDEAM  | Anomalía vs. promedio histórico (mm)           | 0.35×    |
| `ideam_temperatura_c`     | IDEAM  | Temperatura mensual promedio (°C)              | 0.35×    |
| `ideam_temp_anomalia`     | IDEAM  | Anomalía de temperatura vs. histórico (°C)     | 0.35×    |
| `mes`                     | MTU    | Mes del año (1–12, captura estacionalidad)     | 0.25×    |
| `anio`                    | MTU    | Año (tendencia secular)                        | 0.25×    |

**Clases de salida IVT**:
- `0 = BAJA`: Condiciones favorables para la producción territorial
- `1 = MEDIA`: Presión moderada — monitoreo recomendado
- `2 = ALTA`: Condiciones adversas — intervención recomendada

---

## Licencias de los Datos

| Fuente   | Licencia              | URL de referencia                        |
|----------|-----------------------|------------------------------------------|
| ANI      | Datos Abiertos Gov CO | datos.gov.co/resource/8yi9-t44c          |
| UPRA     | Datos Abiertos Gov CO | datos.gov.co/resource/gwbi-fnzs          |
| IDEAM    | Datos Abiertos Gov CO | datos.gov.co/resource/s54a-sgyg          |
| DANE     | Uso libre con atribución | dane.gov.co                           |
| MinTIC   | Datos Abiertos Gov CO | datos.gov.co/resource/ghgs-xx6j          |
| MEN      | Datos Abiertos Gov CO | datos.gov.co/resource/nudc-7mev          |

Todos los datos son de uso libre con atribución. Ver [datos.gov.co](https://datos.gov.co)
para términos completos.

---

*Diccionario generado por Kwesx AI — Sistema Operativo Territorial Inteligente*  
*Versión 1.0 | Julio 2026*
