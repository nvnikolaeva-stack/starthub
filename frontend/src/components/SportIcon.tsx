import { Waves, PersonStanding, Bike, Triangle, Medal } from "lucide-react";

const SPORT_ICONS = {
  swimming: Waves,
  running: PersonStanding,
  cycling: Bike,
  triathlon: Triangle,
  other: Medal,
} as const;

const SPORT_COLORS = {
  swimming: "var(--sport-swimming)",
  running: "var(--sport-running)",
  cycling: "var(--sport-cycling)",
  triathlon: "var(--sport-triathlon)",
  other: "var(--sport-other)",
} as const;

export type SportIconName = keyof typeof SPORT_ICONS;

export function SportIcon({
  sport,
  size = 16,
  className,
}: {
  sport: string;
  size?: number;
  className?: string;
}) {
  const Icon =
    SPORT_ICONS[sport as SportIconName] ?? SPORT_ICONS.other;
  const color =
    SPORT_COLORS[sport as SportIconName] ?? "var(--sport-other)";
  return (
    <Icon
      size={size}
      color={color}
      className={className}
      aria-hidden
    />
  );
}
