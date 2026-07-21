import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppProvider } from "@/contexts/AppContext";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import FloatingAlertButton from "@/components/ui/FloatingAlertButton";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display:  "swap",
});

export const metadata: Metadata = {
  title: "Kwesx AI — Tu Territorio Inteligente",
  description:
    "Consulta el estado de tu territorio en Colombia: clima, precios del campo, estado de las vías y calidad de vida. Datos abiertos explicados en lenguaje sencillo.",
  keywords: [
    "Colombia", "territorio", "datos abiertos", "clima", "cultivos",
    "vías", "Kwesx AI", "inteligencia territorial", "comunidades"
  ],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans`}>
        <AppProvider>
          {/* Skip link para accesibilidad de teclado */}
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[9999] focus:px-4 focus:py-2 focus:bg-terra focus:text-white focus:rounded-xl focus:text-sm focus:font-semibold focus:shadow-lg"
          >
            Ir al contenido principal
          </a>

          <div className="flex h-screen overflow-hidden bg-warm-50">
            {/* Navegación lateral — en desktop siempre visible; en móvil como drawer */}
            <Sidebar />

            {/* Área de contenido */}
            <div className="flex flex-col flex-1 overflow-hidden">
              <TopBar />
              <main
                id="main-content"
                className="flex-1 overflow-y-auto"
                aria-label="Contenido principal"
              >
                <div className="p-4 md:p-6 lg:p-8 max-w-screen-xl mx-auto">
                  {children}
                </div>
              </main>
            </div>
          </div>

          {/* Botón flotante de alertas — visible en todas las páginas */}
          <FloatingAlertButton />
        </AppProvider>
      </body>
    </html>
  );
}
