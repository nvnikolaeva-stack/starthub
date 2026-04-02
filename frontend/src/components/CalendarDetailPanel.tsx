"use client";

import type { Event } from "@/lib/types";
import { dayKey, formatDayMonthYearLocalized } from "@/lib/dates";
import { EventCard } from "@/components/EventCard";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { EmptyStateCard } from "@/components/EmptyStateCard";

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
  const tEmpty = useTranslations("empty");

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
            <EmptyStateCard
              className="border-none bg-transparent py-6"
              title={tEmpty("noEventsOnDateDetailed", {
                date: formatDayMonthYearLocalized(selectedDay, locale),
              })}
              description={tEmpty("addOnDatePrompt")}
              actionHref={addHref}
              actionLabel={tEmpty("addFirst")}
            />
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
            <EmptyStateCard
              className="border-none bg-transparent py-6"
              title={tEmpty("noEvents")}
              description={tEmpty("noEventsDesc")}
              actionHref="/add"
              actionLabel={tEmpty("addFirst")}
            />
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
