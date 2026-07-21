# Preguntas Frecuentes — Kwesx AI

---

## General

**¿Qué es Kwesx AI?**  
Kwesx AI es una plataforma de inteligencia territorial impulsada por IA y datos abiertos del gobierno colombiano. Transforma datos complejos en información comprensible para ciudadanos, campesinos, funcionarios e investigadores.

**¿Quién puede usar Kwesx AI?**  
Cualquier persona. La interfaz tiene un "Modo Fácil" diseñado para usuarios con baja alfabetización digital, adultos mayores y comunidades rurales. También hay un modo completo para investigadores y funcionarios.

**¿Los datos son reales?**  
Sí, cuando las APIs de datos.gov.co están disponibles. Cuando no hay conexión, el sistema usa datos sintéticos realistas (marcados con `-SIMULADO`) para mantener la plataforma funcional.

**¿Kwesx AI reemplaza a los organismos oficiales?**  
No. Kwesx AI es una herramienta de apoyo para la toma de decisiones. Para decisiones legales o institucionales, siempre consultar las fuentes oficiales: ANI, UPRA, IDEAM, DANE.

---

## Datos y Fuentes

**¿De dónde vienen los datos?**  
De 5 fuentes abiertas del gobierno colombiano, accedidas via la plataforma Socrata de datos.gov.co:
- **ANI:** Tráfico vehicular en peajes nacionales
- **UPRA:** Precios de insumos agrícolas (fertilizantes, plaguicidas, semillas, combustible)
- **IDEAM:** Variables climáticas de estaciones hidrometeorológicas
- **DANE + MinTIC:** Brecha de conectividad a internet por municipio
- **MEN-SIMAT:** Tasas de cobertura educativa por municipio y nivel

**¿Con qué frecuencia se actualizan los datos?**  
Depende de cada fuente: UPRA actualiza mensualmente, IDEAM casi diariamente, ANI quincenalmente. El ETL se puede ejecutar manualmente con `make etl` o programarse como tarea periódica.

**¿Puedo agregar nuevas fuentes de datos?**  
Sí. Ver la guía en [docs/ETL.md](docs/ETL.md#agregar-una-nueva-fuente-de-datos).

**¿Por qué algunos datos dicen "SIMULADO"?**  
Cuando la API de Socrata no está disponible o el dataset no tiene datos recientes, el ETL genera datos sintéticos calibrados con estadísticas reales. El campo `fuente` siempre indica el origen: `"ANI"` = datos reales, `"ANI-SIMULADO"` = datos sintéticos.

---

## Modelos de IA

**¿Qué es el IVT?**  
El Índice de Vulnerabilidad Territorial (IVT) es un score que combina condiciones de precios agrícolas, variables climáticas y factores temporales para clasificar el riesgo de una zona en BAJA, MEDIA o ALTA vulnerabilidad.

**¿Cómo funciona el Asistente IA?**  
El asistente usa NLP basado en TF-IDF y similitud coseno sobre 80+ frases de ejemplo en español colombiano. Reconoce 8 intenciones: precios, clima, vías, conectividad, educación, riesgos, IVT y saludo.

**¿Los modelos ML necesitan entrenamiento?**  
Sí, los modelos se entrenan localmente y se guardan como archivos `.pkl`. Al clonar el repositorio, debes ejecutar `make etl && make train-advanced` para tener modelos funcionales. Los archivos `.pkl` no se suben a Git.

**¿Qué significa si el modelo dice "no disponible"?**  
Que aún no se ha entrenado (o el archivo `.pkl` no existe). Ejecutar: `make train-advanced`.

---

## Instalación y Configuración

**¿Cuáles son los requisitos mínimos?**  
- Python 3.11+
- Node.js 18+
- PostgreSQL 15 (o Docker)
- 4 GB RAM (8 GB recomendados para entrenamiento ML)

**¿Necesito Docker?**  
No es obligatorio, pero sí recomendado para la base de datos. Sin Docker, necesitas PostgreSQL 15 instalado localmente.

**¿Cómo configuro las variables de entorno?**  
Copiar `.env.example` a `.env` y rellenar los valores. Ver [docs/CONFIGURACION.md](docs/CONFIGURACION.md) para descripción de cada variable.

**¿Por qué el frontend no conecta con el backend?**  
Verificar que `NEXT_PUBLIC_API_URL` en `.env` apunta a `http://localhost:8000` (desarrollo) o a la URL del backend en producción. También verificar que el backend esté corriendo con `make backend`.

---

## Despliegue

**¿Cómo despliego en Vercel?**  
Ver [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md). En resumen:
1. Importar repositorio en Vercel
2. Vercel detecta `vercel.json` con `rootDirectory: "frontend"` automáticamente
3. Configurar `NEXT_PUBLIC_API_URL` en Vercel Settings → Environment Variables

**¿Dónde despliego el backend?**  
El backend FastAPI se puede desplegar en Render, Railway, Fly.io o cualquier servicio con soporte para Python. Ver `Dockerfile` y `deploy/`.

**¿Funciona offline?**  
Parcialmente. El Service Worker cachea los assets del frontend para uso offline. Los datos requieren conexión al backend.

---

## Accesibilidad

**¿Kwesx AI cumple con estándares de accesibilidad?**  
Sí. La plataforma cumple WCAG 2.2 AA: contraste alto, navegación por teclado, ARIA labels, fuente escalable, botones de al menos 44×44px, y modo de reducción de movimiento.

**¿Hay soporte para lectores de pantalla?**  
Sí. Todos los elementos interactivos tienen `aria-label` descriptivos. El foco de teclado es visible en todo momento.

**¿Qué es el "Modo Fácil"?**  
Un modo de visualización simplificado que usa lenguaje más sencillo, fuentes más grandes y botones más prominentes. Diseñado para usuarios con baja alfabetización digital.

---

## Contribuciones

**¿Cómo puedo contribuir?**  
Ver [CONTRIBUTING.md](CONTRIBUTING.md) o [docs/CONTRIBUIR.md](docs/CONTRIBUIR.md).

**¿Aceptan traducciones a lenguas indígenas?**  
Sí, especialmente a lenguas con presencia fuerte en zonas rurales colombianas (Wayuunaiki, Nasa Yuwe, Embera, etc.). Abrir un issue con la etiqueta `i18n`.

**¿Cómo reporto un bug?**  
Usando el [template de bug report](.github/ISSUE_TEMPLATE/bug_report.md) en GitHub Issues.
