"use client";

import type { Event, SportType } from "@/lib/types";
import {
  ApiError,
  getEvents,
  getEvent,
  getDistances,
} from "@/lib/api";
import {
  dayKey,
  eventOverlapsDay,
  formatDayMonthYearLocalized,
} from "@/lib/dates";
import {
  defaultCalendarFilters,
  applyCalendarFilters,
  computeFetchRange,
  isCalendarFiltersActive,
} from "@/lib/calendarFilters";
import { Calendar } from "@/components/Calendar";
import { CalendarDetailPanel } from "@/components/CalendarDetailPanel";
import { CalendarListView } from "@/components/CalendarListView";
import { CalendarWeekendsView } from "@/components/CalendarWeekendsView";
import { EmptyStateCard, ServerUnavailableCard } from "@/components/EmptyStateCard";
import { YearView } from "@/components/YearView";
import { EventQuickDrawer } from "@/components/EventQuickDrawer";
import { EventCard } from "@/components/EventCard";
import { FilterBar } from "@/components/FilterBar";
import { useIsMobile } from "@/hooks/use-is-mobile";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useLocale, useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

async function enrichWithDetails(events: Event[]): Promise<Event[]> {
  const ids = [...new Set(events.map((e) => e.id))];
  const chunk = 15;
  const byId = new Map<string, Event>();
  for (let i = 0; i < ids.length; i += chunk) {
    const part = ids.slice(i, i + chunk);
    const rows = await Promise.all(
      part.map((id) => getEvent(id).catch(() => null))
    );
    for (const r of rows) {
      if (r) byId.set(r.id, r);
    }
  }
  return events.map((e) => byId.get(e.id) || e);
}

export type CalendarMainView = "month" | "list" | "weekends" | "year";

export function HomeCalendar() {
  const t = useTranslations("calendar");
  const tCommon = useTranslations("common");
  const tEmpty = useTranslations("empty");
  const locale = useLocale();
  const isMobile = useIsMobile();
  const [filters, setFilters] = useState(defaultCalendarFilters);
  const [viewMonth, setViewMonth] = useState(() => new Date());
  const [viewYear, setViewYear] = useState(() => new Date().getFullYear());
  const [fetchedEvents, setFetchedEvents] = useState<Event[]>([]);
  const [distanceOptions, setDistanceOptions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [calView, setCalView] = useState<CalendarMainView>("month");
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);
  const [quickEvent, setQuickEvent] = useState<Event | null>(null);
  const yearCacheRef = useRef<Map<number, Event[]>>(new Map());
  const [yearBucket, setYearBucket] = useState<{
    y: number;
    events: Event[];
  } | null>(null);
  const [yearLoading, setYearLoading] = useState(false);

  useLayoutEffect(() => {
    if (typeof window === "undefined") return;
    if (window.matchMedia("(max-width: 767px)").matches) {
      setCalView("list");
    }
  }, []);

  useEffect(() => {
    if (!error) return;
    const id = window.setTimeout(() => {
      setReloadKey((k) => k + 1);
    }, 30000);
    return () => window.clearTimeout(id);
  }, [error]);

  const retryFetch = useCallback(() => {
    setError(null);
    setReloadKey((k) => k + 1);
  }, []);

  const fetchRange = useMemo(
    () =>
      computeFetchRange(
        filters.periodPreset,
        viewMonth,
        filters.customDateFrom,
        filters.customDateTo
      ),
    [
      filters.periodPreset,
      filters.customDateFrom,
      filters.customDateTo,
      viewMonth,
    ]
  );

  useEffect(() => {
    let c = false;
    (async () => {
      const types: SportType[] = [
        "swimming",
        "running",
        "cycling",
        "triathlon",
        "other",
      ];
      const rows = await Promise.all(
        types.map((t) => getDistances(t).catch(() => []))
      );
      if (c) return;
      setDistanceOptions(
        [...new Set(rows.flat())].sort((a, b) => a.localeCompare(b))
      );
    })();
    return () => {
      c = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      setError(null);
      try {
        const raw = await getEvents({
          date_from: fetchRange.date_from,
          date_to: fetchRange.date_to,
          upcoming: false,
          limit: 500,
          period: "all",
          sport_type: filters.sport === "all" ? undefined : filters.sport,
        });
        if (cancelled) return;

        let merged = await enrichWithDetails(raw);
        if (cancelled) return;

        setFetchedEvents(merged);
      } catch (e) {
        if (cancelled) return;
        setError(
          e instanceof ApiError ? e.message : tCommon("serverError")
        );
        setFetchedEvents([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
  }, [fetchRange.date_from, fetchRange.date_to, filters.sport, reloadKey, tCommon]);

  useEffect(() => {
    if (calView !== "year") return;
    const y = viewYear;
    const cached = yearCacheRef.current.get(y);
    if (cached) {
      setYearBucket({ y, events: cached });
      setYearLoading(false);
      return;
    }
    let cancelled = false;
    setYearLoading(true);
    setYearBucket(null);
    (async () => {
      try {
        const raw = await getEvents({
          date_from: `${y}-01-01`,
          date_to: `${y}-12-31`,
          upcoming: false,
          limit: 500,
          period: "all",
        });
        if (cancelled) return;
        const merged = await enrichWithDetails(raw);
        if (cancelled) return;
        yearCacheRef.current.set(y, merged);
        setYearBucket({ y, events: merged });
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof ApiError ? e.message : tCommon("serverError")
          );
        }
      } finally {
        if (!cancelled) setYearLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [calView, viewYear, reloadKey, tCommon]);

  const locationOptions = useMemo(() => {
    const s = new Set<string>();
    for (const e of fetchedEvents) {
      if (e.location?.trim()) s.add(e.location.trim());
    }
    return [...s].sort((a, b) => a.localeCompare(b));
  }, [fetchedEvents]);

  const displayEvents = useMemo(
    () =>
      applyCalendarFilters(fetchedEvents, filters, {
        weekendsOnly: fetchRange.weekendsOnly,
      }),
    [fetchedEvents, filters, fetchRange.weekendsOnly]
  );

  const filtersActive = useMemo(
    () => isCalendarFiltersActive(filters),
    [filters]
  );

  const yearRawEvents = useMemo(() => {
    if (!yearBucket || yearBucket.y !== viewYear) return [];
    return yearBucket.events;
  }, [yearBucket, viewYear]);

  const yearDisplayEvents = useMemo(
    () =>
      applyCalendarFilters(yearRawEvents, filters, {
        weekendsOnly: false,
      }),
    [yearRawEvents, filters]
  );

  const todayKey = useMemo(() => dayKey(new Date()), []);

  const selectedDayKey = selectedDay ? dayKey(selectedDay) : null;

  const onSelectDay = useCallback(
    (d: Date) => {
      setSelectedDay(d);
      if (calView !== "month" || typeof window === "undefined") return;
      if (!window.matchMedia("(max-width: 767px)").matches) return;
      const id = `mobile-day-events-${dayKey(d)}`;
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          document.getElementById(id)?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        });
      });
    },
    [calView]
  );

  const onSelectFromList = useCallback((d: Date) => {
    setSelectedDay(d);
  }, []);

  const upcomingForPanel = useMemo(() => {
    const sorted = [...displayEvents].sort((a, b) =>
      a.date_start.localeCompare(b.date_start)
    );
    const future = sorted.filter(
      (e) => (e.date_end || e.date_start).slice(0, 10) >= todayKey
    );
    return future.slice(0, 5);
  }, [displayEvents, todayKey]);

  const dayEventsForPanel = useMemo(() => {
    if (!selectedDay) return [];
    return displayEvents.filter((e) => eventOverlapsDay(e, selectedDay));
  }, [displayEvents, selectedDay]);

  const onResetAll = useCallback(() => {
    setFilters(defaultCalendarFilters());
    setViewMonth(new Date());
  }, []);

  const showFilterEmpty =
    !loading &&
    !error &&
    displayEvents.length === 0 &&
    filtersActive;
  const showTrueEmpty =
    !loading &&
    !error &&
    displayEvents.length === 0 &&
    !filtersActive;

  const yearShowFilterEmpty =
    calView === "year" &&
    !yearLoading &&
    !error &&
    yearDisplayEvents.length === 0 &&
    filtersActive;
  const yearShowTrueEmpty =
    calView === "year" &&
    !yearLoading &&
    !error &&
    yearDisplayEvents.length === 0 &&
    !filtersActive;

  const viewTabs = (
    <div className="mb-4 flex flex-wrap gap-1 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-tinted)] p-1">
      {(
        [
          ["month", t("viewMonth")] as const,
          ["list", t("viewList")] as const,
          ["weekends", t("viewWeekends")] as const,
          ["year", t("viewYear")] as const,
        ] as const
      ).map(([id, label]) => (
        <button
          key={id}
          type="button"
          onClick={() => {
            setCalView(id);
            if (id === "year") {
              setViewYear(viewMonth.getFullYear());
              setSelectedDay(null);
            } else if (id !== "month") {
              setSelectedDay(null);
            }
          }}
          className={cn(
            "min-h-11 rounded-[var(--radius-sm)] px-3 py-2 text-sm transition-colors",
            calView === id
              ? "bg-[var(--color-surface)] font-medium text-[var(--color-text)] shadow-sm"
              : "text-[var(--color-text-secondary)] hover:text-[var(--color-text)]"
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <h1 className="mb-4 text-2xl font-bold text-[var(--color-text)]">
        {t("title")}
      </h1>
      {error && (
        <ServerUnavailableCard
          className="mb-4"
          title={tEmpty("serverError")}
          description={tEmpty("serverErrorDesc")}
          retryLabel={tEmpty("retry")}
          onRetry={retryFetch}
        />
      )}
      <FilterBar
        filters={filters}
        onFiltersChange={(p) =>
          setFilters((f) => ({ ...f, ...p }))
        }
        viewMonth={viewMonth}
        onViewMonthChange={setViewMonth}
        distanceOptions={distanceOptions}
        locations={locationOptions}
        onResetAll={onResetAll}
      />

      {viewTabs}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 lg:items-start">
        <div className="lg:col-span-8">
          {calView === "year" ? (
            yearLoading ? (
              <p className="text-sm text-[var(--color-text-muted)]">
                {t("loading")}
              </p>
            ) : yearShowFilterEmpty ? (
              <EmptyStateCard
                title={tEmpty("noFilterResults")}
                onAction={onResetAll}
                actionButtonLabel={tEmpty("resetFilters")}
              />
            ) : yearShowTrueEmpty ? (
              <EmptyStateCard
                title={tEmpty("noEvents")}
                description={tEmpty("noEventsDesc")}
                actionHref="/add"
                actionLabel={tEmpty("addFirst")}
              />
            ) : (
              <YearView
                year={viewYear}
                events={yearDisplayEvents}
                onYearChange={setViewYear}
                onDayWithEventsClick={(d) => {
                  setCalView("month");
                  setViewMonth(new Date(d.getFullYear(), d.getMonth(), 1));
                  setSelectedDay(d);
                }}
              />
            )
          ) : loading ? (
            <p className="text-sm text-[var(--color-text-muted)]">
              {t("loading")}
            </p>
          ) : showFilterEmpty ? (
            <EmptyStateCard
              title={tEmpty("noFilterResults")}
              onAction={onResetAll}
              actionButtonLabel={tEmpty("resetFilters")}
            />
          ) : showTrueEmpty ? (
            <EmptyStateCard
              title={tEmpty("noEvents")}
              description={tEmpty("noEventsDesc")}
              actionHref="/add"
              actionLabel={tEmpty("addFirst")}
            />
          ) : calView === "month" ? (
            <>
              <Calendar
                view={viewMonth}
                onViewChange={setViewMonth}
                events={displayEvents}
                showPast={fetchRange.showPastCalendar}
                selectedDayKey={selectedDayKey}
                onSelectDay={onSelectDay}
              />
              {isMobile && selectedDay ? (
                <section
                  id={`mobile-day-events-${dayKey(selectedDay)}`}
                  className="mt-4 scroll-mt-28 border-t border-[var(--color-border)] pt-3 lg:hidden"
                >
                  <h3 className="mb-2 text-sm font-semibold text-[var(--color-text)]">
                    {formatDayMonthYearLocalized(selectedDay, locale)} —{" "}
                    {t("eventsDay")}
                  </h3>
                  {dayEventsForPanel.length === 0 ? (
                    <p className="text-sm text-[var(--color-text-muted)]">
                      {t("detailEmptyDay")}
                    </p>
                  ) : (
                    <ul className="flex flex-col gap-2">
                      {dayEventsForPanel.map((ev) => (
                        <li key={ev.id} className="w-full min-w-0">
                          <EventCard event={ev} />
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              ) : null}
            </>
          ) : calView === "list" ? (
            <CalendarListView
              events={displayEvents}
              showPast={fetchRange.showPastCalendar}
              todayKey={todayKey}
              onSelectEventDay={onSelectFromList}
            />
          ) : (
            <CalendarWeekendsView
              events={displayEvents}
              showPast={fetchRange.showPastCalendar}
              todayKey={todayKey}
              fromDate={new Date()}
            />
          )}
        </div>
        <div className="lg:col-span-4">
          <CalendarDetailPanel
            selectedDay={selectedDay}
            dayEvents={dayEventsForPanel}
            upcomingEvents={upcomingForPanel}
            onQuickView={setQuickEvent}
          />
        </div>
      </div>

      <EventQuickDrawer
        event={quickEvent}
        open={Boolean(quickEvent)}
        onOpenChange={(open) => {
          if (!open) setQuickEvent(null);
        }}
      />
    </div>
  );
}
