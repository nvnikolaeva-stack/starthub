import type { InputHTMLAttributes } from "react";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return (
      <input
        ref={ref}
        className={cn(
          "flex min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-[var(--color-text-placeholder)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-border-focus)] focus-visible:outline-offset-2",
          className
        )}
        {...props}
      />
    );
  }
);
