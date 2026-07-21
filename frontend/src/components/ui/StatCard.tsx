import clsx from "clsx";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: { value: number; label: string };
  color?: "navy" | "teal" | "green" | "sand";
  loading?: boolean;
}

const COLOR_MAP = {
  navy:  { bg: "bg-navy",       text: "text-white",    iconBg: "bg-white/20" },
  teal:  { bg: "bg-teal",       text: "text-white",    iconBg: "bg-white/20" },
  green: { bg: "bg-green",      text: "text-white",    iconBg: "bg-white/20" },
  sand:  { bg: "bg-sand",       text: "text-white",    iconBg: "bg-white/20" },
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = "navy",
  loading = false,
}: StatCardProps) {
  const { bg, text, iconBg } = COLOR_MAP[color];

  if (loading) {
    return (
      <div className="card animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-3" />
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-2" />
        <div className="h-3 bg-gray-200 rounded w-2/3" />
      </div>
    );
  }

  return (
    <div className={clsx("rounded-xl p-5 flex items-start justify-between", bg, text)}>
      <div className="flex-1">
        <p className="text-sm font-medium opacity-80">{title}</p>
        <p className="text-3xl font-bold mt-1">{value}</p>
        {subtitle && (
          <p className="text-xs opacity-70 mt-1">{subtitle}</p>
        )}
        {trend && (
          <div className="flex items-center gap-1 mt-2">
            <span className={clsx(
              "text-xs font-semibold",
              trend.value >= 0 ? "text-green-200" : "text-red-200"
            )}>
              {trend.value >= 0 ? "▲" : "▼"} {Math.abs(trend.value)}%
            </span>
            <span className="text-xs opacity-60">{trend.label}</span>
          </div>
        )}
      </div>
      <div className={clsx("p-3 rounded-lg", iconBg)}>
        <Icon size={22} />
      </div>
    </div>
  );
}
