"use client";

/**
 * /asistente — "Pregúntale a Kwesx"
 *
 * UX mejorado:
 * ✓ Sin duplicidad de sugerencias (un solo bloque gamificado)
 * ✓ Micro-copy con iconos en lugar de párrafos densos
 * ✓ Skeleton shimmer atractivo mientras la IA responde
 * ✓ Microinteracciones: scale(1.02) + hover suave en sugerencias
 * ✓ Badges de gamificación: Tendencia / Popular / Nuevo
 * ✓ Saludo dinámico según hora del día
 * ✓ Error amigable sin exponer detalles técnicos
 */

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Mic, MicOff, Send, Bot, User, Volume2,
  RefreshCw, ChevronRight, Sparkles, Flame, Star, Zap,
} from "lucide-react";
import clsx from "clsx";
import { api, ChatResponse } from "@/lib/api";
import { useApp } from "@/contexts/AppContext";

// ─── Tipos ────────────────────────────────────────────────────────────────────

interface Mensaje {
  id:       string;
  tipo:     "usuario" | "asistente";
  texto:    string;
  datos?:   Record<string, unknown>;
  seguimiento?: string[];
  loading?: boolean;
}

type Badge = "tendencia" | "popular" | "nuevo" | "top";

interface Sugerencia {
  emoji:  string;
  texto:  string;
  badge?: Badge;
  desc:   string;
}

// ─── Datos de sugerencias con gamificación ────────────────────────────────────

const SUGERENCIAS: Sugerencia[] = [
  {
    emoji: "🌧️",
    texto: "¿Va a llover hoy?",
    badge: "tendencia",
    desc:  "Clima e IDEAM",
  },
  {
    emoji: "🚜",
    texto: "¿Cómo están los precios del campo?",
    badge: "popular",
    desc:  "Índice UPRA",
  },
  {
    emoji: "🛣️",
    texto: "¿Hay cierres en las carreteras?",
    badge: "top",
    desc:  "Red vial ANI",
  },
  {
    emoji: "🌱",
    texto: "¿Cuánto costaron los fertilizantes?",
    badge: "nuevo",
    desc:  "Insumos agrícolas",
  },
  {
    emoji: "🏘️",
    texto: "¿Cómo está mi municipio?",
    desc:  "Análisis IVT",
  },
  {
    emoji: "📊",
    texto: "¿Cuántos datos tiene Kwesx AI?",
    desc:  "Fuentes oficiales",
  },
];

const BADGE_CONFIG: Record<Badge, { label: string; icon: React.ElementType; className: string }> = {
  tendencia: { label: "Tendencia", icon: Flame,    className: "bg-red-50 text-red-500 border-red-100" },
  popular:   { label: "Popular",   icon: Star,     className: "bg-amber-pale text-amber-dark border-amber-pale" },
  nuevo:     { label: "Nuevo",     icon: Sparkles, className: "bg-sky-50 text-sky-500 border-sky-100" },
  top:       { label: "Top",       icon: Zap,      className: "bg-terra-faint text-terra border-terra-pale" },
};

// ─── Mensaje de bienvenida (micro-copy con iconos) ────────────────────────────

function getBienvenida(): Mensaje {
  const h = new Date().getHours();
  const saludo =
    h < 12 ? "¡Buenos días!" : h < 18 ? "¡Buenas tardes!" : "¡Buenas noches!";

  return {
    id:    "bienvenida",
    tipo:  "asistente",
    texto: saludo, // solo el saludo; el resto va en un bloque especial
    datos: { __bienvenida: true },
  };
}

// ─── Página ───────────────────────────────────────────────────────────────────

export default function AsistentePage() {
  const { voiceEnabled, speak, mode } = useApp();
  const isEasy = mode === "easy";

  const [mensajes,   setMensajes]   = useState<Mensaje[]>([getBienvenida()]);
  const [input,      setInput]      = useState("");
  const [enviando,   setEnviando]   = useState(false);
  const [escuchando, setEscuchando] = useState(false);
  const [sinVoz,     setSinVoz]     = useState(false);
  const [mostrarSug, setMostrarSug] = useState(true);

  const bottomRef      = useRef<HTMLDivElement>(null);
  const inputRef       = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);

  // Auto-scroll al final
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes]);

  // Reconocimiento de voz
  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setSinVoz(true); return; }

    const rec = new SR();
    rec.lang           = "es-CO";
    rec.continuous     = false;
    rec.interimResults = true;

    rec.onresult = (e: any) => {
      const t = e.results[0][0].transcript;
      setInput(t);
      if (e.results[0].isFinal) { setEscuchando(false); enviar(t); }
    };
    rec.onerror = () => setEscuchando(false);
    rec.onend   = () => setEscuchando(false);

    recognitionRef.current = rec;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const enviar = useCallback(async (texto: string) => {
    const t = texto.trim();
    if (!t || enviando) return;

    setInput("");
    setEnviando(true);
    setMostrarSug(false);

    const id = Date.now().toString();

    setMensajes((prev) => [
      ...prev,
      { id,        tipo: "usuario",    texto: t },
      { id: id+"r", tipo: "asistente", texto: "", loading: true },
    ]);

    try {
      const resp: ChatResponse = await api.chat(t);
      const msg: Mensaje = {
        id:          id + "r",
        tipo:        "asistente",
        texto:       resp.respuesta,
        datos:       resp.datos,
        seguimiento: resp.sugerencias,
      };
      setMensajes((prev) => [...prev.slice(0, -1), msg]);
      if (voiceEnabled) speak(resp.respuesta);
    } catch {
      setMensajes((prev) => [
        ...prev.slice(0, -1),
        {
          id:    id + "r",
          tipo:  "asistente",
          texto: "Parece que el servidor está descansando un momento 🔌. Intenta de nuevo en unos segundos.",
        },
      ]);
    } finally {
      setEnviando(false);
      inputRef.current?.focus();
    }
  }, [enviando, voiceEnabled, speak]);

  const toggleVoz = useCallback(() => {
    if (!recognitionRef.current) return;
    if (escuchando) {
      recognitionRef.current.stop();
      setEscuchando(false);
    } else {
      try { recognitionRef.current.start(); setEscuchando(true); setInput(""); }
      catch { /* ya corriendo */ }
    }
  }, [escuchando]);

  const limpiar = () => {
    setMensajes([getBienvenida()]);
    setMostrarSug(true);
  };

  const handleTextarea = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  return (
    <div className="flex flex-col" style={{ height: "calc(100vh - 64px - 4rem)" }}>

      {/* ── Header del chat ──────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 pb-4 border-b border-warm-100 shrink-0">
        <div className="relative">
          <div className="w-11 h-11 rounded-2xl gradient-terra flex items-center justify-center shadow-sm">
            <Bot size={22} className="text-white" aria-hidden />
          </div>
          <span
            className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-400 rounded-full border-2 border-white"
            aria-hidden
          />
        </div>
        <div className="flex-1">
          <h1 className="font-bold text-warm-900 text-[15px]">Kwesx AI</h1>
          <p className="text-xs text-warm-500 flex items-center gap-1.5">
            <span className="status-dot" aria-hidden />
            Guía territorial · Datos ANI, UPRA e IDEAM
          </p>
        </div>
        <button
          onClick={limpiar}
          className="btn-ghost text-xs gap-1.5 advanced-feature"
          aria-label="Nueva conversación"
        >
          <RefreshCw size={13} aria-hidden />
          Nueva consulta
        </button>
      </div>

      {/* ── Área de mensajes ─────────────────────────────────────────────── */}
      <div
        className="flex-1 overflow-y-auto space-y-4 py-4 pr-1"
        role="log"
        aria-live="polite"
        aria-label="Conversación con Kwesx AI"
      >
        {mensajes.map((msg, i) => (
          <BurbujaMensaje
            key={msg.id}
            msg={msg}
            isEasy={isEasy}
            voiceEnabled={voiceEnabled}
            onSpeak={speak}
            onSeguimiento={enviar}
            index={i}
          />
        ))}
        <div ref={bottomRef} aria-hidden />
      </div>

      {/* ── Sugerencias gamificadas ───────────────────────────────────────── */}
      {mostrarSug && !enviando && (
        <div className="py-3 shrink-0">
          <p className="text-xs text-warm-400 font-semibold uppercase tracking-wide mb-3">
            ¿Qué quieres saber hoy?
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2.5">
            {SUGERENCIAS.map((s, i) => (
              <SugerenciaCard
                key={s.texto}
                sug={s}
                onSelect={enviar}
                delay={i * 40}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── Input ────────────────────────────────────────────────────────── */}
      <div className="pt-3 border-t border-warm-100 shrink-0">
        {sinVoz && (
          <p className="text-xs text-warm-400 bg-warm-50 rounded-xl px-3 py-2 mb-2">
            ℹ️ Voz disponible en Chrome y Edge
          </p>
        )}

        <form
          onSubmit={(e) => { e.preventDefault(); enviar(input); }}
          className="flex gap-2 items-end"
        >
          {/* Micrófono */}
          <button
            type="button"
            onClick={toggleVoz}
            disabled={sinVoz}
            className={clsx(
              "shrink-0 rounded-2xl transition-all duration-200",
              "flex items-center justify-center",
              escuchando
                ? "bg-danger text-white scale-110 shadow-lg shadow-red-200"
                : sinVoz
                ? "bg-warm-100 text-warm-300 cursor-not-allowed"
                : "bg-terra-pale text-terra hover:bg-terra hover:text-white hover:scale-105"
            )}
            style={{ width: 48, height: 48, minWidth: 48 }}
            aria-label={escuchando ? "Detener voz" : "Hablar con Kwesx"}
            aria-pressed={escuchando}
          >
            {escuchando
              ? <MicOff size={20} aria-hidden />
              : <Mic    size={20} aria-hidden />
            }
          </button>

          {/* Textarea */}
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleTextarea}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  enviar(input);
                }
              }}
              placeholder={
                escuchando
                  ? "🎤 Escuchando... habla ahora"
                  : isEasy
                  ? "¿Qué quieres saber?"
                  : "Escribe tu pregunta en español..."
              }
              disabled={enviando || escuchando}
              rows={1}
              className="input-base resize-none overflow-hidden pr-2"
              style={{ minHeight: 48 }}
              aria-label="Tu pregunta para Kwesx"
            />
            {/* Ondas de voz */}
            {escuchando && (
              <div className="absolute right-3 top-3.5 flex items-end gap-0.5" aria-hidden>
                {[3, 5, 4, 6, 3].map((h, i) => (
                  <div
                    key={i}
                    className="w-1 bg-danger rounded-full"
                    style={{
                      height: `${h * 3}px`,
                      animation: `typingBounce 0.8s ease-in-out infinite`,
                      animationDelay: `${i * 80}ms`,
                    }}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Enviar */}
          <button
            type="submit"
            disabled={!input.trim() || enviando}
            className={clsx(
              "btn-primary shrink-0 px-4 rounded-2xl transition-all duration-200",
              (!input.trim() || enviando) && "opacity-50 cursor-not-allowed"
            )}
            style={{ width: 48, height: 48, minWidth: 48 }}
            aria-label="Enviar pregunta"
          >
            {enviando
              ? <RefreshCw size={18} className="animate-spin" aria-hidden />
              : <Send      size={18} aria-hidden />
            }
          </button>
        </form>

        <p className="text-xs text-warm-300 text-center mt-2">
          Datos oficiales de Colombia · ANI · UPRA · IDEAM
        </p>
      </div>
    </div>
  );
}

// ─── Tarjeta de sugerencia gamificada ─────────────────────────────────────────

function SugerenciaCard({
  sug, onSelect, delay,
}: {
  sug:      Sugerencia;
  onSelect: (t: string) => void;
  delay:    number;
}) {
  const badge = sug.badge ? BADGE_CONFIG[sug.badge] : null;

  return (
    <button
      onClick={() => onSelect(sug.texto)}
      className="suggestion-card animate-slide-up group"
      style={{ animationDelay: `${delay}ms`, animationFillMode: "both" }}
      aria-label={sug.texto}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <span
          className="text-2xl leading-none group-hover:scale-110 transition-transform duration-200"
          aria-hidden
        >
          {sug.emoji}
        </span>
        {badge && (
          <span className={clsx(
            "inline-flex items-center gap-1 text-2xs font-semibold px-1.5 py-0.5 rounded-full border shrink-0",
            badge.className
          )}>
            <badge.icon size={9} aria-hidden />
            {badge.label}
          </span>
        )}
      </div>
      <p className="text-sm font-semibold text-warm-900 leading-snug text-left">
        {sug.texto}
      </p>
      <p className="text-xs text-warm-400 mt-1 text-left">{sug.desc}</p>
    </button>
  );
}

// ─── Burbuja de mensaje ───────────────────────────────────────────────────────

function BurbujaMensaje({
  msg, isEasy, voiceEnabled, onSpeak, onSeguimiento, index,
}: {
  msg:           Mensaje;
  isEasy:        boolean;
  voiceEnabled:  boolean;
  onSpeak:       (t: string) => void;
  onSeguimiento: (t: string) => void;
  index:         number;
}) {
  const esUsuario    = msg.tipo === "usuario";
  const esBienvenida = !esUsuario && msg.datos?.__bienvenida === true;

  // Bienvenida especial: bloque visual con micro-copy
  if (esBienvenida) return <BienvenidaCard saludo={msg.texto} index={index} />;

  return (
    <div
      className={clsx(
        "flex gap-3 animate-slide-up",
        esUsuario ? "flex-row-reverse" : "flex-row"
      )}
      style={{ animationDelay: `${Math.min(index * 35, 180)}ms`, animationFillMode: "both" }}
    >
      {/* Avatar */}
      <div
        className={clsx(
          "w-8 h-8 rounded-xl shrink-0 flex items-center justify-center mt-0.5",
          esUsuario ? "gradient-terra" : "bg-warm-100"
        )}
        aria-hidden
      >
        {esUsuario
          ? <User size={14} className="text-white" />
          : <Bot  size={14} className="text-terra"  />
        }
      </div>

      {/* Contenido */}
      <div className={clsx("max-w-[80%] space-y-2", esUsuario && "flex flex-col items-end")}>

        {/* Burbuja */}
        <div className={clsx(
          "px-4 py-3 text-sm leading-relaxed",
          esUsuario
            ? "gradient-terra text-white rounded-2xl rounded-tr-sm"
            : "bg-white border border-warm-100 shadow-card text-warm-800 rounded-2xl rounded-tl-sm",
          isEasy && "text-base px-5 py-4"
        )}>
          {msg.loading
            ? <ShimmerTyping />
            : <TextoMarkdown texto={msg.texto} />
          }
        </div>

        {/* Botón leer en voz alta */}
        {!esUsuario && !msg.loading && voiceEnabled && msg.texto && (
          <button
            onClick={() => onSpeak(msg.texto)}
            className="flex items-center gap-1 text-xs text-warm-300 hover:text-terra transition-colors px-1"
            aria-label="Escuchar respuesta"
          >
            <Volume2 size={11} aria-hidden />
            Escuchar
          </button>
        )}

        {/* Datos de respaldo */}
        {!esUsuario && !msg.loading && msg.datos && Object.keys(msg.datos).filter(k => k !== "__bienvenida").length > 0 && (
          <div className="bg-terra-faint border border-terra-pale rounded-2xl p-3 text-xs space-y-1 advanced-feature w-full">
            <p className="font-semibold text-terra flex items-center gap-1.5 mb-2">
              <Sparkles size={11} aria-hidden />
              Datos oficiales de respaldo
            </p>
            {Object.entries(msg.datos)
              .filter(([k, v]) => k !== "__bienvenida" && typeof v !== "object" && v !== null)
              .map(([k, v]) => (
                <div key={k} className="flex justify-between gap-3">
                  <span className="text-warm-500 capitalize">{k.replace(/_/g, " ")}</span>
                  <span className="font-mono font-semibold text-warm-900">
                    {typeof v === "number" ? v.toLocaleString("es-CO") : String(v)}
                  </span>
                </div>
              ))
            }
          </div>
        )}

        {/* Preguntas de seguimiento */}
        {!esUsuario && !msg.loading && msg.seguimiento && msg.seguimiento.length > 0 && (
          <div className="flex flex-col gap-1.5 pt-1 w-full">
            {msg.seguimiento.slice(0, 3).map((s) => (
              <button
                key={s}
                onClick={() => onSeguimiento(s)}
                className="flex items-center gap-2 text-xs bg-warm-50 hover:bg-terra-faint border border-warm-100 hover:border-terra-pale text-warm-600 hover:text-terra rounded-xl px-3 py-2 transition-all text-left"
              >
                <ChevronRight size={11} className="shrink-0" aria-hidden />
                {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Skeleton mientras IA responde ────────────────────────────────────────────

function ShimmerTyping() {
  return (
    <div aria-label="Kwesx está pensando..." className="space-y-2 py-1 min-w-[160px]">
      {/* Dots animados */}
      <div className="flex items-center gap-2 mb-3">
        {[0, 150, 300].map((d) => (
          <span
            key={d}
            className="typing-dot"
            style={{ animationDelay: `${d}ms` }}
            aria-hidden
          />
        ))}
        <span className="text-xs text-warm-400 ml-1">Analizando datos...</span>
      </div>
      {/* Shimmer lines */}
      <div className="shimmer-line h-3 w-4/5" />
      <div className="shimmer-line h-3 w-full" />
      <div className="shimmer-line h-3 w-3/5" />
    </div>
  );
}

// ─── Bienvenida visual (micro-copy + iconos) ──────────────────────────────────

function BienvenidaCard({ saludo, index }: { saludo: string; index: number }) {
  return (
    <div
      className="flex gap-3 animate-slide-up"
      style={{ animationDelay: `${index * 35}ms`, animationFillMode: "both" }}
    >
      {/* Avatar */}
      <div
        className="w-8 h-8 rounded-xl bg-warm-100 shrink-0 flex items-center justify-center mt-0.5"
        aria-hidden
      >
        <Bot size={14} className="text-terra" />
      </div>

      {/* Card de bienvenida */}
      <div className="bg-white border border-warm-100 shadow-card rounded-2xl rounded-tl-sm overflow-hidden max-w-[84%]">

        {/* Cabecera con gradiente */}
        <div className="gradient-terra px-5 py-4">
          <p className="text-white font-bold text-base">{saludo} 👋</p>
          <p className="text-white/80 text-sm mt-0.5">Soy <strong>Kwesx</strong>, tu guía territorial para Colombia</p>
        </div>

        {/* Capacidades en micro-copy */}
        <div className="px-4 py-3 space-y-2.5">
          {[
            { icon: "🌱", title: "Precios del campo",    desc: "Fertilizantes, semillas e insumos · UPRA" },
            { icon: "🛣️", title: "Estado de las vías",   desc: "Carreteras y peajes en tiempo real · ANI" },
            { icon: "🌦️", title: "Clima de Colombia",    desc: "Lluvia, temperatura y anomalías · IDEAM" },
            { icon: "🧠", title: "Análisis territorial", desc: "Riesgos e indicadores de tu zona · IA" },
          ].map(({ icon, title, desc }) => (
            <div key={title} className="flex items-center gap-3">
              <span className="text-xl w-7 text-center shrink-0" aria-hidden>{icon}</span>
              <div>
                <p className="text-sm font-semibold text-warm-900 leading-none">{title}</p>
                <p className="text-xs text-warm-400 mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="px-4 pb-4 pt-1">
          <p className="text-xs text-warm-500 bg-warm-50 rounded-xl px-3 py-2.5 flex items-center gap-2">
            <span aria-hidden>✍️</span>
            Escribe, <strong>habla</strong> 🎤 o elige una pregunta abajo
          </p>
        </div>
      </div>
    </div>
  );
}

// ─── Helper de texto con markdown básico ──────────────────────────────────────

function TextoMarkdown({ texto }: { texto: string }) {
  return (
    <div>
      {texto.split(/(\*\*[^*]+\*\*)/).map((part, i) =>
        part.startsWith("**")
          ? <strong key={i}>{part.slice(2, -2)}</strong>
          : <span key={i}>{part}</span>
      )}
    </div>
  );
}
