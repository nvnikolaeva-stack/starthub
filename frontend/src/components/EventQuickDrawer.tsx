"use client";

import type { Event } from "@/lib/types";
import {
  formatEventRangeLocalized,
  parseISODate,
  weekdayShortLocalized,
} from "@/lib/dates";
import { SportIcon } from "@/components/SportIcon";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useEffect } from "react";
import { cn } from "@/lib/utils";

function eventDistances(ev: Event): string {
  const regs = ev.registrations;
  if (!regs?.length) return "—";
  const set = new Set<string>();
  for (const r of regs) {
    for (const d of r.distances || []) {
      if (d) set.add(d);
    }
  }
  return [...set].join(", ") || "—";
}

export function EventQuickDrawer({
  event,
  open,
  onOpenChange,
}: {
  event: Event | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const locale = useLocale();
  const t = useTranslations("event");
  const tf = useTranslations("filters");

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onOpenChange(false);
    };
    if (open) {
      document.addEventListener("keydown", onKey);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onOpenChange]);

  if (!open || !event) return null;

  const start = parseISODate(event.date_start.slice(0, 10));
  const names =
    event.registrations
      ?.map(
        (r) =>
          r.participant_display_name ||
          r.participant?.display_name ||
          t("defaultParticipant")
      )
      .filter(Boolean)
      .join(", ") || t("noParticipantsShort");

  return (
    <div className="fixed inset-0 z-[60]">
      <button
        type="button"
        aria-label="Close"
        className="absolute inset-0 bg-black/40"
        onClick={() => onOpenChange(false)}
      />
      <aside
        role="dialog"
        aria-modal
        aria-label={event.name}
        className={cn(
          "absolute right-0 top-0 flex h-full w-full max-w-md flex-col",
          "border-l border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-md)]"
        )}
      >
        <div className="flex items-start justify-between gap-3 border-b border-[var(--color-border)] p-4">
          <div className="flex min-w-0 flex-1 items-start gap-2">
            <SportIcon sport={event.sport_type} size={22} className="mt-0.5 shrink-0" />
            <div className="min-w-0">
              <h2 className="text-lg font-semibold leading-snug text-[var(--color-text)]">
                {event.name}
              </h2>
              <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
                {formatEventRangeLocalized(
                  event.date_start,
                  event.date_end,
                  locale
                )}
                {" · "}
                {weekdayShortLocalized(start, locale)}
              </p>
            </div>
          </div>
          <button
            type="button"
            className="shrink-0 rounded-md p-2 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)]"
            onClick={() => onOpenChange(false)}
          >
            ✕
          </button>
        </div>
        <div className="flex-1 space-y-3 overflow-y-auto p-4 text-sm text-[var(--color-text)]">
          <p>
            <span className="font-medium text-[var(--color-text-secondary)]">
              {t("location")}:{" "}
            </span>
            {event.location}
          </p>
          <p>
            <span className="font-medium text-[var(--color-text-secondary)]">
              {t("distance")}:{" "}
            </span>
            {eventDistances(event)}
          </p>
          <p>
            <span className="font-medium text-[var(--color-text-secondary)]">
              {t("participants")}:{" "}
            </span>
            {names}
          </p>
          <p className="text-[var(--color-text-muted)]">
            {tf(event.sport_type)}
          </p>
        </div>
        <div className="border-t border-[var(--color-border)] p-4">
          <Link
            href={`/event/${event.id}`}
            onClick={() => onOpenChange(false)}
            className="inline-flex h-10 w-full items-center justify-center rounded-[var(--radius-md)] bg-[var(--color-primary)] text-sm font-medium text-white no-underline hover:opacity-95"
          >
            {t("openFullPage")}
          </Link>
        </div>
      </aside>
    </div>
  );
}
