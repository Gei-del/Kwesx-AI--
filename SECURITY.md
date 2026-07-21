# Política de Seguridad — Kwesx AI

## Versiones soportadas

| Versión | Soportada |
|---------|-----------|
| 1.x (main) | ✅ Activa |
| < 1.0 | ❌ Sin soporte |

## Reportar una vulnerabilidad

**Por favor NO abras un Issue público para reportar vulnerabilidades de seguridad.**

Reporta vulnerabilidades de forma privada a:

📧 **gpontonca@gmail.com**

Incluye en tu reporte:
- Descripción clara del problema
- Pasos para reproducir la vulnerabilidad
- Impacto potencial estimado
- Versión o commit afectado

### Proceso de respuesta

1. **Acuse de recibo:** 48 horas hábiles
2. **Evaluación inicial:** 5 días hábiles
3. **Corrección y parche:** Según severidad (crítico: 7 días, alto: 14 días, medio/bajo: 30 días)
4. **Divulgación coordinada:** Anunciamos el fix antes de hacer el reporte público

## Alcance

### En alcance (acepta reportes)
- API FastAPI — inyección SQL, bypass de autenticación, CORS mal configurado
- Frontend Next.js — XSS, CSRF, exposición de datos sensibles
- Pipeline ETL — ejecución de código arbitrario en transformaciones
- Configuración Docker — escalada de privilegios, exposición de puertos

### Fuera de alcance
- Datos de prueba o sintéticos del modelo IVT
- Servicios de terceros (datos.gov.co, IDEAM, ANI, UPRA)
- Ataques de fuerza bruta contra cuentas de desarrollo
- Problemas en versiones sin soporte

## Buenas prácticas que seguimos

- Variables de entorno para secrets (nunca hardcodeados)
- Dependencias auditadas regularmente con `pip audit` y `npm audit`
- CORS configurado explícitamente en `backend/app/main.py`
- Sin datos personales almacenados (solo datos de uso y datasets públicos)
- HTTPS obligatorio en producción (terminación en load balancer o Vercel)

## Reconocimiento

Los investigadores que reporten vulnerabilidades válidas serán reconocidos en el CHANGELOG (con su permiso) y en nuestra lista de contribuidores de seguridad.

---

*Última actualización: Julio 2026*
