"use client";

import type { Event } from "@/lib/types";
import { dayKey, formatDayMonthYearLocalized } from "@/lib/dates";
import { EventCard } from "@/components/EventCard";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

export function CalendarDetailPanel({
  selectedDay,
  dayEvents,
  upcomingEvents,
  onQuickView,
}: {
  selectedDay: Date | null;
  dayEvents: Event[];
  upcomingEvents: Event[];
  onQuickView?: (e: Event) => void;
}) {
  const locale = useLocale();
  const t = useTranslations("calendar");

  const addHref = selectedDay
    ? `/add?date=${dayKey(selectedDay)}`
    : "/add";

  return (
    <aside
      className={cn(
        "flex flex-col rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-[var(--shadow-sm)]",
        "min-h-[280px] lg:min-h-[320px]"
      )}
    >
      {selectedDay ? (
        <>
          <h2 className="mb-3 text-sm font-medium text-[var(--color-text-secondary)]">
            {formatDayMonthYearLocalized(selectedDay, locale)}
          </h2>
          {dayEvents.length === 0 ? (
            <div className="flex flex-1 flex-col gap-3">
              <p className="text-sm text-[var(--color-text-muted)]">
                {t("detailEmptyDay")}
              </p>
              <Link
                href={addHref}
                className="btn-accent inline-flex min-h-11 w-fit items-center justify-center rounded-[var(--radius-full)] px-4 text-sm no-underline"
              >
                {t("detailAddOnDate", {
                  date: formatDayMonthYearLocalized(selectedDay, locale),
                })}
              </Link>
            </div>
          ) : (
            <ul className="flex flex-col gap-2">
              {dayEvents.map((ev) => (
                <li key={ev.id}>
                  <EventCard
                    event={ev}
                    enableQuickView={Boolean(onQuickView)}
                    onQuickView={onQuickView}
                  />
                </li>
              ))}
            </ul>
          )}
        </>
      ) : (
        <>
          <h2 className="mb-3 text-sm font-semibold text-[var(--color-text)]">
            {t("detailUpcomingTitle")}
          </h2>
          {upcomingEvents.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)]">
              {t("noEventsInSelection")}
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {upcomingEvents.slice(0, 5).map((ev) => (
                <li key={ev.id}>
                  <EventCard
                    event={ev}
                    enableQuickView={Boolean(onQuickView)}
                    onQuickView={onQuickView}
                  />
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </aside>
  );
}
