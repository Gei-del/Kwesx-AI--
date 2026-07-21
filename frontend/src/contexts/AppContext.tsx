"use client";

/**
 * contexts/AppContext.tsx
 * =======================
 * Estado global de accesibilidad y experiencia de usuario para Kwesx AI.
 *
 * Gestiona:
 *   - Modo Fácil: interfaz simplificada para usuarios sin experiencia tech
 *   - Tamaño de fuente: normal / grande / extra-grande
 *   - Alto contraste: WCAG 2.2 AA
 *   - Síntesis de voz: leer respuestas en voz alta
 *   - Notificaciones: alertas territoriales activadas o no
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
} from "react";

// ─── Tipos ────────────────────────────────────────────────────────────────────

type FontSize     = "normal" | "large" | "xlarge";
type ContrastMode = "normal" | "high";
type AppMode      = "normal" | "easy";

interface AppState {
  mode:           AppMode;
  fontSize:       FontSize;
  contrast:       ContrastMode;
  voiceEnabled:   boolean;
  alertsEnabled:  boolean;
  mobileNavOpen:  boolean;
  // Acciones
  toggleMode:       () => void;
  setFontSize:      (s: FontSize) => void;
  toggleContrast:   () => void;
  toggleVoice:      () => void;
  toggleAlerts:     () => void;
  speak:            (text: string) => void;
  toggleMobileNav:  () => void;
  closeMobileNav:   () => void;
}

// ─── Context ──────────────────────────────────────────────────────────────────

const AppContext = createContext<AppState | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [mode,          setMode]          = useState<AppMode>("normal");
  const [fontSize,      setFontSizeState] = useState<FontSize>("normal");
  const [contrast,      setContrast]      = useState<ContrastMode>("normal");
  const [voiceEnabled,  setVoiceEnabled]  = useState(false);
  const [alertsEnabled, setAlertsEnabled] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Restaurar preferencias guardadas
  useEffect(() => {
    try {
      const saved = localStorage.getItem("kwesx-prefs");
      if (saved) {
        const p = JSON.parse(saved);
        if (p.mode)     setMode(p.mode);
        if (p.fontSize) setFontSizeState(p.fontSize);
        if (p.contrast) setContrast(p.contrast);
        if (p.voice)    setVoiceEnabled(p.voice);
        if (p.alerts)   setAlertsEnabled(p.alerts);
      }
    } catch { /* ignore */ }
  }, []);

  // Persistir preferencias
  useEffect(() => {
    try {
      localStorage.setItem("kwesx-prefs", JSON.stringify({
        mode, fontSize, contrast,
        voice:   voiceEnabled,
        alerts:  alertsEnabled,
      }));
    } catch { /* ignore */ }
  }, [mode, fontSize, contrast, voiceEnabled, alertsEnabled]);

  // Aplicar atributos al <html> para que el CSS reaccione
  useEffect(() => {
    const html = document.documentElement;
    html.setAttribute("data-mode",     mode);
    html.setAttribute("data-font",     fontSize);
    html.setAttribute("data-contrast", contrast);
  }, [mode, fontSize, contrast]);

  const toggleMode      = useCallback(() => setMode((m) => m === "normal" ? "easy" : "normal"), []);
  const setFontSize     = useCallback((s: FontSize) => setFontSizeState(s), []);
  const toggleContrast  = useCallback(() => setContrast((c) => c === "normal" ? "high" : "normal"), []);
  const toggleVoice     = useCallback(() => setVoiceEnabled((v) => !v), []);
  const toggleAlerts    = useCallback(() => setAlertsEnabled((a) => !a), []);
  const toggleMobileNav = useCallback(() => setMobileNavOpen((o) => !o), []);
  const closeMobileNav  = useCallback(() => setMobileNavOpen(false), []);

  /** Leer texto en voz alta usando la Web Speech API del navegador */
  const speak = useCallback((text: string) => {
    if (!voiceEnabled) return;
    if (!("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang  = "es-CO";
    utt.rate  = 0.9;
    utt.pitch = 1.0;

    // Preferir voz en español si está disponible
    const voices = window.speechSynthesis.getVoices();
    const esVoice = voices.find(
      (v) => v.lang.startsWith("es") && v.localService
    );
    if (esVoice) utt.voice = esVoice;

    window.speechSynthesis.speak(utt);
  }, [voiceEnabled]);

  const value = useMemo<AppState>(() => ({
    mode, fontSize, contrast, voiceEnabled, alertsEnabled, mobileNavOpen,
    toggleMode, setFontSize, toggleContrast, toggleVoice, toggleAlerts, speak,
    toggleMobileNav, closeMobileNav,
  }), [mode, fontSize, contrast, voiceEnabled, alertsEnabled, mobileNavOpen,
       toggleMode, setFontSize, toggleContrast, toggleVoice, toggleAlerts, speak,
       toggleMobileNav, closeMobileNav]);

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp debe usarse dentro de <AppProvider>");
  return ctx;
}
