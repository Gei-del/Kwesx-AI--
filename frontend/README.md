# Kwesx AI — Frontend

**Stack:** Next.js 14 App Router · TypeScript 5 · Tailwind CSS 3 · React 18

Dashboard territorial con Asistente IA, mapa interactivo, graficas y modulos ML.

---

## Paginas disponibles

| Ruta | Pagina |
|---|---|
| `/` | Dashboard principal — resumen del territorio hoy |
| `/asistente` | Asistente IA — conversacion en espanol colombiano |
| `/mapa` | Mapa territorial interactivo (Leaflet) |
| `/datos` | Explorador de datos MTU (ANI, UPRA, IDEAM) |
| `/insights` | Insights ML avanzados — forecasting, clustering, anomalias |
| `/prediccion` | Predictor IVT — vulnerabilidad territorial |
| `/recomendaciones` | Recomendaciones territoriales IA |
| `/alertas` | Centro de alertas y notificaciones |
| `/exportar` | Exportar datos y reportes |
| `/configuracion` | Configuracion de accesibilidad y preferencias |

---

## Configuracion

```bash
# Instalar dependencias
cd frontend
npm ci

# Variable de entorno (crear frontend/.env.local)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Correr en desarrollo
npm run dev
# -> http://localhost:3000
```

---

## Verificar antes de commit

```bash
npm run type-check   # TypeScript — 0 errores
npm run lint         # ESLint — 0 warnings
npm run build        # Build produccion — debe completar sin errores
```

---

## Estructura de carpetas

```
src/
├── app/             # Next.js App Router (10 paginas)
├── components/
│   ├── layout/      # Sidebar (drawer responsivo), TopBar (hamburguesa)
│   ├── ui/          # ErrorBoundary, componentes reutilizables
│   ├── dashboard/   # Widgets del dashboard
│   ├── charts/      # Graficas recharts
│   └── map/         # Mapa Leaflet
├── contexts/
│   ├── AppContext.tsx    # Estado global: modo facil, accesibilidad, nav movil
│   └── AuthContext.tsx   # Auth skeleton (demo mode)
├── hooks/
│   ├── useServiceWorker.ts  # Push notifications (stub VAPID)
│   └── useAuth.ts
├── lib/
│   └── api.ts        # Cliente API: AbortController + retry + cache 5min
├── middleware.ts     # Next.js middleware (auth skeleton)
└── types/
    ├── auth.ts           # Interfaces TypeScript de autenticacion
    └── notifications.ts  # Tipos para push notifications
public/
├── sw.js             # Service Worker (offline + push notifications stub)
└── manifest.json     # PWA manifest
```

---

## Tokens de diseno

| Token | Hex | Uso |
|---|---|---|
| `terra` | `#1A6B42` | Color principal — sidebar, botones primarios |
| `amber` | `#F59E0B` | Alertas, enfasis |
| `warm-*` | grises calidos | Fondo, texto secundario, bordes |

WCAG 2.2 AA: contraste alto, teclado, ARIA, touch 44px, fuentes escalables.

---

## Despliegue

`vercel.json` en la raiz del repo tiene `"rootDirectory": "frontend"` — Vercel lo detecta automaticamente.
Solo configurar `NEXT_PUBLIC_API_URL` en Vercel → Project Settings → Environment Variables.
