"use client";

import type { Event } from "@/lib/types";
import {
  dayKey,
  eventOverlapsDay,
  formatCompactDayMonthLocalized,
  parseISODate,
  startOfMonth,
  weekdayShortLocalized,
} from "@/lib/dates";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";

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

function participantCount(ev: Event): number {
  return ev.registrations?.length ?? 0;
}

export function CalendarListView({
  events,
  showPast,
  todayKey,
  onSelectEventDay,
}: {
  events: Event[];
  showPast: boolean;
  todayKey: string;
  onSelectEventDay?: (day: Date, evs: Event[]) => void;
}) {
  const locale = useLocale();
  const t = useTranslations("calendar");
  const tf = useTranslations("filters");

  const rows = useMemo(() => {
    const filtered = showPast
      ? [...events]
      : events.filter(
          (e) => (e.date_end || e.date_start).slice(0, 10) >= todayKey
        );
    const sorted = filtered.sort((a, b) =>
      a.date_start.localeCompare(b.date_start)
    );

    type Row = {
      monthKey: string;
      monthLabel: string;
      event: Event;
      rowDay: Date;
    };
    const out: Row[] = [];
    for (const ev of sorted) {
      const start = parseISODate(ev.date_start.slice(0, 10));
      const end = ev.date_end
        ? parseISODate(ev.date_end.slice(0, 10))
        : start;
      const m0 = startOfMonth(start);
      const monthKey = dayKey(m0);
      const monthLabel =
        locale === "en"
          ? new Intl.DateTimeFormat("en-GB", {
              month: "long",
              year: "numeric",
            }).format(m0)
          : `${m0.toLocaleString("ru-RU", { month: "long" })} ${m0.getFullYear()}`;
      if (start.getTime() === end.getTime()) {
        out.push({ monthKey, monthLabel, event: ev, rowDay: start });
        continue;
      }
      for (
        let d = new Date(start);
        d <= end;
        d.setDate(d.getDate() + 1)
      ) {
        const copy = new Date(d);
        const mk = dayKey(startOfMonth(copy));
        const ml =
          locale === "en"
            ? new Intl.DateTimeFormat("en-GB", {
                month: "long",
                year: "numeric",
              }).format(startOfMonth(copy))
            : `${startOfMonth(copy).toLocaleString("ru-RU", {
                month: "long",
              })} ${startOfMonth(copy).getFullYear()}`;
        out.push({
          monthKey: mk,
          monthLabel: ml,
          event: ev,
          rowDay: copy,
        });
      }
    }
    out.sort((a, b) => {
      const da = dayKey(a.rowDay);
      const db = dayKey(b.rowDay);
      if (da !== db) return da.localeCompare(db);
      return a.event.date_start.localeCompare(b.event.date_start);
    });
    return out;
  }, [events, showPast, todayKey, locale]);

  const groups = useMemo(() => {
    const map = new Map<string, { label: string; items: typeof rows }>();
    for (const r of rows) {
      const g = map.get(r.monthKey) ?? { label: r.monthLabel, items: [] };
      g.items.push(r);
      map.set(r.monthKey, g);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [rows]);

  if (rows.length === 0) {
    return (
      <p className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-sm text-[var(--color-text-muted)]">
        {t("listEmpty")}
      </p>
    );
  }

  return (
    <div className="space-y-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-[var(--shadow-sm)]">
      {groups.map(([key, { label, items }]) => (
        <section key={key}>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
            {label}
          </h3>
          <div className="flex flex-col gap-0">
            {items.map(({ event: ev, rowDay }) => {
              const sameDay = events.filter((e) => eventOverlapsDay(e, rowDay));
              const dk = dayKey(rowDay);
              return (
                <Link
                  key={`${ev.id}-${dk}`}
                  href={`/event/${ev.id}`}
                  onClick={() => onSelectEventDay?.(rowDay, sameDay)}
                  className="flex flex-col gap-1 border-b border-[var(--color-border)] py-2.5 text-left text-xs last:border-0 sm:flex-row sm:flex-wrap sm:items-baseline sm:gap-x-4 sm:text-sm"
                >
                  <span className="shrink-0 text-[var(--color-text-secondary)]">
                    {formatCompactDayMonthLocalized(rowDay, locale)}{" "}
                    {weekdayShortLocalized(rowDay, locale)}
                  </span>
                  <span className="min-w-0 flex-1 truncate font-medium text-[var(--color-text)] sm:max-w-[min(40vw,14rem)]">
                    {ev.name}
                  </span>
                  <span className="shrink-0 text-[var(--color-text-muted)]">
                    {tf(ev.sport_type)}
                  </span>
                  <span className="shrink-0 text-[var(--color-text-secondary)]">
                    {eventDistances(ev)}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-[var(--color-text-muted)] sm:max-w-[10rem]">
                    {ev.location}
                  </span>
                  <span className="shrink-0 text-[var(--color-text-muted)]">
                    {t("participantsCountShort", {
                      count: participantCount(ev),
                    })}
                  </span>
                </Link>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
