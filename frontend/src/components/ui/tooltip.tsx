"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Tooltip({
  content,
  children,
  className,
}: {
  content: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span className={cn("group relative inline-flex", className)}>
      {children}
      <span
        className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-1 hidden w-max max-w-[220px] -translate-x-1/2 rounded-md bg-slate-900 px-2 py-1 text-xs text-white shadow group-hover:block group-focus:block whitespace-pre-line"
      >
        {content}
      </span>
    </span>
  );
}
