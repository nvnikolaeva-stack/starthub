"use client";

import type { Event } from "@/lib/types";
import {
  addMonths,
  calendarGridMonth,
  dayKey,
  eventOverlapsDay,
} from "@/lib/dates";
import { CalendarDay } from "@/components/CalendarDay";
import { Button } from "@/components/ui/button";
import { useIsMobile } from "@/hooks/use-is-mobile";
import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";

function isEventPast(ev: Event, today: string): boolean {
  const end = (ev.date_end || ev.date_start).slice(0, 10);
  return end < today;
}

type Props = {
  view: Date;
  onViewChange: (d: Date) => void;
  events: Event[];
  showPast: boolean;
  selectedDayKey: string | null;
  onSelectDay: (d: Date) => void;
};

export function Calendar({
  view,
  onViewChange,
  events,
  showPast,
  selectedDayKey,
  onSelectDay,
}: Props) {
  const locale = useLocale();
  const t = useTranslations("calendar");
  const monthCompact = useIsMobile();

  const todayKey = useMemo(() => dayKey(new Date()), []);

  const grid = useMemo(() => calendarGridMonth(view), [view]);

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

  const monthHeading = useMemo(() => {
    if (locale === "en") {
      const s = new Intl.DateTimeFormat("en-US", {
        month: "long",
        year: "numeric",
      }).format(view);
      return s.charAt(0).toUpperCase() + s.slice(1);
    }
    return new Intl.DateTimeFormat("ru-RU", {
      month: "long",
      year: "numeric",
    }).format(view);
  }, [view, locale]);

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-2 shadow-[var(--shadow-sm)] sm:p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-11 min-h-11 w-11 min-w-11 shrink-0 px-0"
          onClick={() => onViewChange(addMonths(view, -1))}
          aria-label={t("prevMonthAria")}
        >
          ←
        </Button>
        <h2 className="text-center text-base font-semibold text-[var(--color-text)] sm:text-lg">
          {monthHeading}
        </h2>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-11 min-h-11 w-11 min-w-11 shrink-0 px-0"
          onClick={() => onViewChange(addMonths(view, 1))}
          aria-label={t("nextMonthAria")}
        >
          →
        </Button>
      </div>
      <div className="mb-1 grid grid-cols-7 gap-1 text-center text-[11px] font-medium text-[var(--color-text-muted)] sm:text-xs">
        {weekHdr.map((w) => (
          <div key={w}>{w}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1 sm:gap-1.5">
        {grid.map((cell, i) => {
          const dim =
            showPast &&
            cell != null &&
            dayKey(cell) < todayKey &&
            events.some(
              (e) =>
                cell &&
                eventOverlapsDay(e, cell) &&
                isEventPast(e, todayKey)
            );
          return (
            <CalendarDay
              key={i}
              date={cell}
              todayKey={todayKey}
              events={events}
              showPast={showPast}
              selectedDayKey={selectedDayKey}
              onSelectDay={onSelectDay}
              dayId={cell ? `day-${dayKey(cell)}` : undefined}
              dimmedPast={Boolean(dim)}
              monthCompact={monthCompact}
            />
          );
        })}
      </div>
    </div>
  );
}
