# Guía de Contribución — Kwesx AI

¡Gracias por tu interés en contribuir! Este documento describe cómo participar en el desarrollo de Kwesx AI.

## Código de Conducta

Al participar, aceptas cumplir nuestro [Código de Conducta](CODE_OF_CONDUCT.md). Queremos que este proyecto sea un espacio seguro e inclusivo para todos.

## ¿Cómo contribuir?

### 1. Reportar un bug

1. Verifica que el bug no esté ya reportado en [Issues](../../issues)
2. Abre un nuevo Issue con la plantilla **Bug Report**
3. Incluye: descripción, pasos para reproducir, comportamiento esperado, capturas

### 2. Proponer una mejora

1. Abre un Issue con la plantilla **Feature Request**
2. Describe el problema que resuelve y la solución propuesta
3. Espera feedback antes de implementar

### 3. Enviar un Pull Request

```bash
# 1. Fork y clonar
git clone https://github.com/TU-USUARIO/kwesx-ai.git
cd kwesx-ai

# 2. Crear rama descriptiva
git checkout -b feat/nombre-de-la-feature
# o
git checkout -b fix/descripcion-del-bug

# 3. Configurar entorno
make setup-dev

# 4. Hacer cambios con commits descriptivos
git commit -m "feat(ml): agregar soporte para modelo XGBoost en IVT"

# 5. Verificar calidad
make lint
make test

# 6. Push y PR
git push origin feat/nombre-de-la-feature
```

## Convención de commits

Seguimos [Conventional Commits](https://conventionalcommits.org):

```
feat:     Nueva funcionalidad
fix:      Corrección de bug
docs:     Cambios en documentación
style:    Cambios de formato (sin lógica)
refactor: Refactorización sin nuevas funciones
test:     Agregar o mejorar pruebas
chore:    Mantenimiento (deps, config, etc.)
perf:     Mejoras de rendimiento
```

Ejemplos:
```
feat(etl): agregar extractor para DANE códigos municipales
fix(ml): corregir thresholds IVT con datos IDEAM sintéticos
docs(api): documentar endpoints de /prediccion
test(backend): agregar pruebas de integración para /datos/ani
```

## Estándares de código

### Python

- **Formateador:** `black` (line-length 100)
- **Imports:** `isort` con perfil black
- **Tipos:** Type hints en todas las funciones públicas
- **Docstrings:** Obligatorios en módulos, clases y funciones públicas
- **Tests:** Cobertura mínima del 60% para nuevas funciones

```bash
make format   # Formatear automáticamente
make lint     # Verificar antes del PR
make test     # Correr pruebas
```

### TypeScript / React

- **Sin `any` implícito** — tipado estricto en interfaces
- **Componentes funcionales** con hooks (no clases)
- **Accessibility:** aria-labels, roles, keyboard navigation
- **No `console.log`** en código de producción

```bash
cd frontend
npm run lint    # ESLint
npm run build   # Verificar compilación
```

## Estructura de carpetas

Antes de agregar archivos, revisa la [estructura del proyecto](README.md#estructura-del-proyecto) para colocarlos en el lugar correcto.

## Prioridades del proyecto

Las áreas de mayor impacto para el concurso son:

1. **Accesibilidad** — Mejorar el Modo Fácil y compatibilidad con lectores de pantalla
2. **Modelo IVT** — Mejorar métricas del clasificador (F1-macro > 0.8)
3. **ETL** — Manejo de errores y reintentos más robusto
4. **Asistente** — Agregar más intenciones reconocidas
5. **Testing** — Aumentar cobertura de pruebas

## Revisión de PRs

- Un miembro del equipo revisará en máximo 48 horas
- Se requiere al menos 1 aprobación para hacer merge
- Los CI checks (lint + tests) deben pasar
- Mantén los PRs pequeños y enfocados en un solo cambio

¡Gracias por contribuir a hacer Kwesx AI mejor para Colombia! 🇨🇴
