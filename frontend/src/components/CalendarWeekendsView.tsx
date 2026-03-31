"use client";

import type { Event } from "@/lib/types";
import {
  dayKey,
  eventOverlapsDay,
  formatDayMonthYearLocalized,
  weekdayShortLocalized,
} from "@/lib/dates";
import { SportIcon } from "@/components/SportIcon";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";

function nextSaturdayFrom(d: Date): Date {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const wd = x.getDay();
  if (wd === 6) return x;
  if (wd === 0) {
    x.setDate(x.getDate() + 6);
    return x;
  }
  x.setDate(x.getDate() + (6 - wd));
  return x;
}

function pairsWithEvents(
  events: Event[],
  from: Date,
  pairCount: number
): Array<{ sat: Date; sun: Date; events: Event[] }> {
  const out: Array<{ sat: Date; sun: Date; events: Event[] }> = [];
  let sat = nextSaturdayFrom(from);
  let guard = 0;
  while (out.length < pairCount && guard < 104) {
    const sun = new Date(sat);
    sun.setDate(sun.getDate() + 1);
    const evs = events.filter(
      (e) => eventOverlapsDay(e, sat) || eventOverlapsDay(e, sun)
    );
    if (evs.length) {
      out.push({ sat: new Date(sat), sun: new Date(sun), events: evs });
    }
    sat.setDate(sat.getDate() + 7);
    guard++;
  }
  return out;
}

export function CalendarWeekendsView({
  events,
  showPast,
  todayKey,
  fromDate,
}: {
  events: Event[];
  showPast: boolean;
  todayKey: string;
  fromDate: Date;
}) {
  const locale = useLocale();
  const t = useTranslations("calendar");

  const pairs = useMemo(() => {
    const base = fromDate;
    const filtered = showPast
      ? events
      : events.filter(
          (e) => (e.date_end || e.date_start).slice(0, 10) >= todayKey
        );
    return pairsWithEvents(filtered, base, 6);
  }, [events, showPast, todayKey, fromDate]);

  if (pairs.length === 0) {
    return (
      <p className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-sm text-[var(--color-text-muted)]">
        {t("weekendsEmpty")}
      </p>
    );
  }

  return (
    <div className="space-y-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-[var(--shadow-sm)]">
      {pairs.map(({ sat, sun, events: evs }) => (
        <section
          key={`${dayKey(sat)}-${dayKey(sun)}`}
          className="border-b border-[var(--color-border)] pb-4 last:border-0 last:pb-0"
        >
          <h3 className="mb-2 text-sm font-semibold text-[var(--color-text)]">
            {formatDayMonthYearLocalized(sat, locale)} ({weekdayShortLocalized(sat, locale)}) —{" "}
            {formatDayMonthYearLocalized(sun, locale)} ({weekdayShortLocalized(sun, locale)})
          </h3>
          <ul className="flex flex-col gap-2">
            {evs.map((ev) => (
              <li key={`${dayKey(sat)}-${ev.id}`}>
                <Link
                  href={`/event/${ev.id}`}
                  className="card flex items-center gap-2 p-3 no-underline transition-colors hover:bg-[var(--color-surface-hover)]"
                >
                  <SportIcon sport={ev.sport_type} size={18} className="shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{ev.name}</p>
                    <p className="truncate text-xs text-[var(--color-text-muted)]">
                      {ev.location}
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
