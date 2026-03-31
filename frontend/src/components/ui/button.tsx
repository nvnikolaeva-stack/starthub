import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg";
};

export function Button({
  className,
  variant = "default",
  size = "md",
  ...props
}: Props) {
  const base =
    "inline-flex min-h-11 items-center justify-center rounded-md font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-border-focus)] focus-visible:outline-offset-2 disabled:opacity-50";
  const variants = {
    default: "bg-slate-900 text-white hover:bg-slate-800",
    outline:
      "border border-slate-300 bg-white hover:bg-slate-50 text-slate-900",
    ghost: "hover:bg-slate-100 text-slate-900",
    destructive: "bg-red-600 text-white hover:bg-red-700",
  };
  const sizes = {
    sm: "min-h-11 px-3 text-sm",
    md: "min-h-11 px-4 text-sm",
    lg: "min-h-11 px-6 text-base",
  };
  return (
    <button
      className={cn(base, variants[variant], sizes[size], className)}
      {...props}
    />
  );
}
