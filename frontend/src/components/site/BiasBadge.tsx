import { TrendDownIcon, TrendUpIcon } from "@/components/icons";

interface BiasBadgeProps {
  value: number;
  size?: "sm" | "md";
}

export function BiasBadge({ value, size = "sm" }: BiasBadgeProps) {
  const pct = Math.round(Math.abs(value) * 100);
  const isLeft = value < 0;
  const Icon = isLeft ? TrendDownIcon : TrendUpIcon;
  const tone = isLeft ? "bias-down" : "bias-up";
  const dim = size === "md" ? 14 : 12;

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium ${tone}`}
      title={`bias score ${value.toFixed(2)} · leans ${isLeft ? "left" : "right"}`}
    >
      <Icon width={dim} height={dim} />
      <span>{pct}%</span>
    </span>
  );
}
