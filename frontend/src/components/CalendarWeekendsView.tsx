"use client";

import type { Event } from "@/lib/types";
import {
  dayKey,
  eventOverlapsDay,
  weekdayShortLocalized,
} from "@/lib/dates";
import { SportIcon } from "@/components/SportIcon";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";
import { cn } from "@/lib/utils";

/** ~2 года вперёд: 52 недели × 2 года */
const WEEKEND_PAIR_COUNT = 104;

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

function weekendPairsTwoYears(from: Date): Array<{ sat: Date; sun: Date }> {
  const out: Array<{ sat: Date; sun: Date }> = [];
  const sat = nextSaturdayFrom(from);
  for (let i = 0; i < WEEKEND_PAIR_COUNT; i++) {
    const s = new Date(sat);
    const u = new Date(sat);
    u.setDate(u.getDate() + 1);
    out.push({ sat: s, sun: u });
    sat.setDate(sat.getDate() + 7);
  }
  return out;
}

function formatPairHeading(sat: Date, sun: Date, locale: string): string {
  const ws = weekdayShortLocalized(sat, locale);
  const wu = weekdayShortLocalized(sun, locale);
  const ds = `${ws} ${sat.getDate()}`;
  const de = `${wu} ${sun.getDate()}`;
  const mon = new Intl.DateTimeFormat(
    locale === "en" ? "en-GB" : "ru-RU",
    { month: "long" }
  ).format(sun);
  return `${ds} — ${de} ${mon}`;
}

function monthGroupKey(d: Date): string {
  return `${d.getFullYear()}-${d.getMonth()}`;
}

function stickyMonthTitle(d: Date): string {
  const s = new Intl.DateTimeFormat("ru-RU", {
    month: "long",
    year: "numeric",
  }).format(d);
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function participantCount(ev: Event): number {
  return ev.registrations?.length ?? 0;
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
  const te = useTranslations("event");

  const baseEvents = useMemo(() => {
    return showPast
      ? events
      : events.filter(
          (e) => (e.date_end || e.date_start).slice(0, 10) >= todayKey
        );
  }, [events, showPast, todayKey]);

  const pairs = useMemo(() => weekendPairsTwoYears(fromDate), [fromDate]);

  const rows = useMemo(() => {
    return pairs.map(({ sat, sun }) => {
      const evs = baseEvents.filter(
        (e) => eventOverlapsDay(e, sat) || eventOverlapsDay(e, sun)
      );
      return { sat, sun, events: evs };
    });
  }, [pairs, baseEvents]);

  const byMonth = useMemo(() => {
    const map = new Map<
      string,
      { title: string; rows: typeof rows }
    >();
    for (const row of rows) {
      const key = monthGroupKey(row.sat);
      let g = map.get(key);
      if (!g) {
        g = { title: stickyMonthTitle(row.sat), rows: [] };
        map.set(key, g);
      }
      g.rows.push(row);
    }
    return [...map.entries()].map(([k, v]) => ({ key: k, ...v }));
  }, [rows]);

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-sm)]">
      {byMonth.map((group) => (
        <div key={group.key}>
          <div className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)]/90 px-4 py-2 font-semibold text-lg text-[var(--color-text)] backdrop-blur">
            📅 {group.title}
          </div>
          {group.rows.map(({ sat, sun, events: evs }) => {
            const k = dayKey(sat);
            const currentWeekend =
              todayKey >= dayKey(sat) && todayKey <= dayKey(sun);
            const hasEvents = evs.length > 0;
            return (
              <section
                key={k}
                className={cn(
                  "border-b border-[var(--color-border)] px-4 py-4 last:border-b-0",
                  hasEvents
                    ? "bg-lime-50/90 ring-1 ring-inset ring-lime-200/80"
                    : "bg-[var(--color-bg)]/80 opacity-75",
                  currentWeekend &&
                    hasEvents &&
                    "ring-2 ring-inset ring-[var(--color-primary)]"
                )}
              >
                <h3 className="mb-2 text-sm font-semibold text-[var(--color-text)]">
                  {formatPairHeading(sat, sun, locale)}
                </h3>
                {evs.length === 0 ? (
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {t("weekendsNoEvents")}
                  </p>
                ) : (
                  <ul className="flex flex-col gap-2">
                    {evs.map((ev) => (
                      <li key={`${k}-${ev.id}`}>
                        <Link
                          href={`/event/${ev.id}`}
                          className="card flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-3 no-underline shadow-sm transition-colors hover:bg-[var(--color-surface-hover)]"
                        >
                          <SportIcon
                            sport={ev.sport_type}
                            size={18}
                            className="shrink-0"
                          />
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium text-[var(--color-text)]">
                              {ev.name}
                            </p>
                            <p className="truncate text-xs text-[var(--color-text-muted)]">
                              {ev.location} •{" "}
                              {te("participantsCountInline", {
                                count: participantCount(ev),
                              })}
                            </p>
                          </div>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            );
          })}
        </div>
      ))}
    </div>
  );
}
