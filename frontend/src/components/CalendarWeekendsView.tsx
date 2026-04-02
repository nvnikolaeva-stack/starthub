"use client";

import type { Event } from "@/lib/types";
import {
  dayKey,
  eventOverlapsDay,
  formatCompactDayMonthLocalized,
  weekdayShortLocalized,
} from "@/lib/dates";
import { SportIcon } from "@/components/SportIcon";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";
import { cn } from "@/lib/utils";

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

function nextEightWeekendPairs(from: Date): Array<{ sat: Date; sun: Date }> {
  const out: Array<{ sat: Date; sun: Date }> = [];
  let sat = nextSaturdayFrom(from);
  for (let i = 0; i < 8; i++) {
    const sun = new Date(sat);
    sun.setDate(sun.getDate() + 1);
    out.push({ sat: new Date(sat), sun: new Date(sun) });
    sat.setDate(sat.getDate() + 7);
  }
  return out;
}

function formatPairHeading(
  sat: Date,
  sun: Date,
  locale: string
): string {
  const ws = weekdayShortLocalized(sat, locale);
  const wu = weekdayShortLocalized(sun, locale);
  const ds = `${ws} ${sat.getDate()}`;
  const de = `${wu} ${sun.getDate()}`;
  const mon = new Intl.DateTimeFormat(locale === "en" ? "en-GB" : "ru-RU", {
    month: "long",
  }).format(sun);
  return `${ds} — ${de} ${mon}`;
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

  const pairs = useMemo(
    () => nextEightWeekendPairs(fromDate),
    [fromDate]
  );

  const rows = useMemo(() => {
    return pairs.map(({ sat, sun }) => {
      const evs = baseEvents.filter(
        (e) => eventOverlapsDay(e, sat) || eventOverlapsDay(e, sun)
      );
      return { sat, sun, events: evs };
    });
  }, [pairs, baseEvents]);

  return (
    <div className="space-y-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-sm)]">
      {rows.map(({ sat, sun, events: evs }) => {
        const k = dayKey(sat);
        const currentWeekend =
          todayKey >= dayKey(sat) && todayKey <= dayKey(sun);
        return (
          <section
            key={k}
            className={cn(
              "border-b border-[var(--color-border)] px-4 py-4 last:border-b-0",
              currentWeekend &&
                "bg-[rgba(var(--color-accent-rgb),0.08)] ring-2 ring-inset ring-[var(--color-primary)]"
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
                      className="card flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-tinted)] p-3 no-underline transition-colors hover:bg-[var(--color-surface-hover)]"
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
  );
}
