"use client";

import { cn } from "@/lib/utils";

type Props = {
  checked: boolean;
  onCheckedChange: (v: boolean) => void;
  id?: string;
  disabled?: boolean;
};

export function Switch({ checked, onCheckedChange, id, disabled }: Props) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onCheckedChange(!checked)}
      className={cn(
        "inline-flex h-11 w-14 shrink-0 items-center justify-center rounded-full border-2 border-transparent bg-transparent transition-colors",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-border-focus)] focus-visible:outline-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-50"
      )}
    >
      <span
        className={cn(
          "relative inline-flex h-7 w-12 shrink-0 rounded-full border-2 border-transparent transition-colors",
          checked ? "bg-slate-900" : "bg-slate-300"
        )}
      >
        <span
          className={cn(
            "pointer-events-none inline-block h-6 w-6 rounded-full bg-white shadow ring-0 transition",
            checked ? "translate-x-5" : "translate-x-0.5"
          )}
        />
      </span>
    </button>
  );
}
