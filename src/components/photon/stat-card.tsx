import type { LucideIcon } from "lucide-react";

export function StatCard({
  label,
  value,
  unit,
  icon: Icon,
  tone = "muted",
}: {
  label: string;
  value: string;
  unit?: string;
  icon: LucideIcon;
  tone?: "primary" | "success" | "muted";
}) {
  const toneClass =
    tone === "primary"
      ? "text-primary"
      : tone === "success"
        ? "text-success"
        : "text-muted-foreground";
  return (
    <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
      <div className="flex items-start justify-between gap-2">
        <p className="text-[15px] text-muted-foreground">{label}</p>
        <Icon className={`size-4 ${toneClass}`} />
      </div>
      <p className="mt-3 font-mono text-3xl font-medium tracking-tight">
        {value}
        {unit ? (
          <span className="ml-1.5 font-sans text-xs text-muted-foreground">{unit}</span>
        ) : null}
      </p>
    </div>
  );
}
