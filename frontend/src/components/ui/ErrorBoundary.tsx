"use client";

/**
 * components/ui/ErrorBoundary.tsx
 * ================================
 * Captura errores de React y muestra una UI de recuperación amigable
 * en lugar de un pantalla en blanco.
 *
 * Uso:
 *   <ErrorBoundary>
 *     <ComponenteQuePodriaFallar />
 *   </ErrorBoundary>
 */

import React from "react";

interface Props {
  children: React.ReactNode;
  /** Componente de fallback personalizado. Por defecto muestra el banner estándar. */
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error:    Error | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // En producción reemplazar con un servicio de monitoreo (Sentry, etc.)
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div
          role="alert"
          className="flex flex-col items-center justify-center min-h-[200px] p-8 rounded-2xl border border-red-100 bg-red-50 text-center"
        >
          <span className="text-4xl mb-3" aria-hidden>⚠️</span>
          <h2 className="text-base font-bold text-red-800 mb-1">
            Algo salió mal
          </h2>
          <p className="text-sm text-red-600 mb-4 max-w-sm">
            Esta sección no pudo cargarse. Puedes intentar nuevamente o continuar usando la app.
          </p>
          <button
            onClick={this.handleReset}
            className="px-4 py-2 bg-red-600 text-white text-sm font-semibold rounded-xl hover:bg-red-700 transition-colors"
          >
            Reintentar
          </button>
          {process.env.NODE_ENV === "development" && this.state.error && (
            <details className="mt-4 text-left max-w-lg">
              <summary className="text-xs text-red-500 cursor-pointer">Detalle técnico</summary>
              <pre className="text-2xs text-red-400 mt-2 whitespace-pre-wrap break-all">
                {this.state.error.message}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}
