import clsx from "clsx";

type IVTLabel = "BAJA" | "MEDIA" | "ALTA";

interface IVTBadgeProps {
  etiqueta: IVTLabel;
  probabilidades?: { BAJA: number; MEDIA: number; ALTA: number };
  size?: "sm" | "md" | "lg";
}

const STYLES: Record<IVTLabel, string> = {
  BAJA:  "bg-green-100 text-green-800 border-green-200",
  MEDIA: "bg-yellow-100 text-yellow-800 border-yellow-200",
  ALTA:  "bg-red-100 text-red-800 border-red-200",
};

const ICONS: Record<IVTLabel, string> = {
  BAJA: "✅",
  MEDIA: "🟡",
  ALTA: "⚠️",
};

export default function IVTBadge({ etiqueta, probabilidades, size = "md" }: IVTBadgeProps) {
  return (
    <div className="flex flex-col items-center gap-2">
      <span className={clsx(
        "border font-bold rounded-full px-4 py-1",
        STYLES[etiqueta],
        size === "lg" ? "text-lg px-6 py-2" : size === "sm" ? "text-xs" : "text-sm",
      )}>
        {ICONS[etiqueta]} Vulnerabilidad {etiqueta}
      </span>

      {probabilidades && (
        <div className="flex gap-3 text-xs text-gray-500">
          {(["BAJA", "MEDIA", "ALTA"] as IVTLabel[]).map((label) => (
            <span key={label} className={clsx(
              "px-2 py-0.5 rounded",
              label === etiqueta ? "font-bold opacity-100" : "opacity-50"
            )}>
              {label}: {(probabilidades[label] * 100).toFixed(0)}%
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
