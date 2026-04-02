"use client";

import type { Event, SportType } from "@/lib/types";
import {
  calendarGridMonth,
  dayKey,
  eventOverlapsDay,
} from "@/lib/dates";
import { SPORT_CARD_DATE } from "@/lib/sport";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";

function monthHeading(d: Date, locale: string): string {
  if (locale === "en") {
    const s = new Intl.DateTimeFormat("en-GB", {
      month: "long",
      year: "numeric",
    }).format(d);
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  return new Intl.DateTimeFormat("ru-RU", {
    month: "long",
    year: "numeric",
  }).format(d);
}

function sportForDay(events: Event[], cell: Date): SportType {
  const hit = events.find((e) => eventOverlapsDay(e, cell));
  return (hit?.sport_type as SportType) ?? "other";
}

type Props = {
  year: number;
  events: Event[];
  onYearChange: (y: number) => void;
  onDayWithEventsClick: (d: Date) => void;
};

export function YearView({
  year,
  events,
  onYearChange,
  onDayWithEventsClick,
}: Props) {
  const locale = useLocale();
  const t = useTranslations("calendar");
  const today = useMemo(() => new Date(), []);
  const todayK = dayKey(today);
  const currentYM =
    today.getFullYear() === year ? today.getMonth() : null;

  const weekHdr = useMemo(
    () =>
      [
        t("weekdays.mon"),
        t("weekdays.tue"),
        t("weekdays.wed"),
        t("weekdays.thu"),
        t("weekdays.fri"),
        t("weekdays.sat"),
        t("weekdays.sun"),
      ] as const,
    [t]
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-center gap-3">
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="min-h-10"
          onClick={() => onYearChange(year - 1)}
          aria-label={t("prevYearAria")}
        >
          ← {year - 1}
        </Button>
        <span className="min-w-[5rem] text-center text-base font-semibold text-[var(--color-text)]">
          {year}
        </span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="min-h-10"
          onClick={() => onYearChange(year + 1)}
          aria-label={t("nextYearAria")}
        >
          {year + 1} →
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 12 }, (_, m) => {
          const view = new Date(year, m, 1);
          const grid = calendarGridMonth(view);
          const isCurrentMonth = currentYM === m;
          return (
            <div
              key={m}
              className={cn(
                "w-full max-w-[180px] justify-self-center rounded-[var(--radius-md)] border bg-[var(--color-surface)] p-2 shadow-[var(--shadow-sm)]",
                isCurrentMonth
                  ? "border-2 border-[var(--color-primary)]"
                  : "border-[var(--color-border)]"
              )}
            >
              <p
                className={cn(
                  "mb-1.5 text-center text-xs font-semibold",
                  isCurrentMonth
                    ? "text-[var(--color-primary)]"
                    : "text-[var(--color-text)]"
                )}
              >
                {monthHeading(view, locale)}
              </p>
              <div className="grid grid-cols-7 gap-px text-center text-[10px] font-medium leading-tight text-[var(--color-text-muted)]">
                {weekHdr.map((w, wi) => (
                  <div
                    key={w}
                    className={cn(
                      wi >= 5 &&
                        "font-bold text-[var(--color-primary)] bg-[rgba(var(--color-accent-rgb),0.12)]"
                    )}
                  >
                    {w}
                  </div>
                ))}
              </div>
              <div className="mt-px grid grid-cols-7 gap-px">
                {grid.map((cell, i) => {
                  const col = i % 7;
                  const weekendCol = col >= 5;
                  if (!cell) {
                    return (
                      <div
                        key={`e-${i}`}
                        className={cn(
                          "min-h-[1.25rem]",
                          weekendCol &&
                            "bg-[rgba(var(--color-accent-rgb),0.08)]"
                        )}
                      />
                    );
                  }
                  const k = dayKey(cell);
                  const has = events.some((e) => eventOverlapsDay(e, cell));
                  const past = k < todayK;
                  const sport = has ? sportForDay(events, cell) : "other";
                  const fill = SPORT_CARD_DATE[sport].bg;

                  return (
                    <button
                      key={k}
                      type="button"
                      disabled={!has}
                      onClick={() => {
                        if (has) onDayWithEventsClick(cell);
                      }}
                      className={cn(
                        "flex min-h-[1.35rem] w-full items-center justify-center rounded-sm text-[11px] font-medium transition-colors",
                        weekendCol &&
                          !has &&
                          "bg-[rgba(var(--color-accent-rgb),0.1)]",
                        has &&
                          "cursor-pointer hover:brightness-95 dark:hover:brightness-110",
                        !has && "cursor-default text-[var(--color-text-muted)]",
                        past && has && "opacity-80"
                      )}
                      style={
                        has
                          ? {
                              backgroundColor: fill,
                              color: SPORT_CARD_DATE[sport].text,
                            }
                          : undefined
                      }
                    >
                      {cell.getDate()}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
