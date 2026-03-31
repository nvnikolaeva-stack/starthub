import type { Event, SportType } from "@/lib/types";
import {
  parseISODate,
  dayKey,
  startOfMonth,
  endOfMonth,
  addMonths,
} from "@/lib/dates";

export type PeriodPreset =
  | "all"
  | "weekends"
  | "this_month"
  | "three_months"
  | "custom";

export interface CalendarFiltersState {
  search: string;
  sport: SportType | "all";
  periodPreset: PeriodPreset;
  customDateFrom: string;
  customDateTo: string;
  distance: string;
  location: string;
}

export const defaultCalendarFilters = (): CalendarFiltersState => ({
  search: "",
  sport: "all",
  periodPreset: "this_month",
  customDateFrom: "",
  customDateTo: "",
  distance: "",
  location: "",
});

export function eventTouchesWeekend(ev: Event): boolean {
  const s = parseISODate(ev.date_start.slice(0, 10));
  const e = ev.date_end
    ? parseISODate(ev.date_end.slice(0, 10))
    : new Date(s);
  for (let t = new Date(s); t <= e; t.setDate(t.getDate() + 1)) {
    const w = t.getDay();
    if (w === 0 || w === 6) return true;
  }
  return false;
}

export function eventMatchesDistance(ev: Event, dist: string): boolean {
  if (!dist) return true;
  const regs = ev.registrations;
  if (!regs?.length) return false;
  return regs.some((r) =>
    (r.distances || []).some((d) => d === dist)
  );
}

export function applyCalendarFilters(
  events: Event[],
  filters: CalendarFiltersState,
  options?: { weekendsOnly?: boolean }
): Event[] {
  let out = events;
  const q = filters.search.trim().toLowerCase();
  if (q) {
    out = out.filter(
      (ev) =>
        ev.name.toLowerCase().includes(q) ||
        ev.location.toLowerCase().includes(q)
    );
  }
  if (filters.sport !== "all") {
    out = out.filter((ev) => ev.sport_type === filters.sport);
  }
  if (filters.distance) {
    out = out.filter((ev) => eventMatchesDistance(ev, filters.distance));
  }
  if (filters.location) {
    out = out.filter((ev) => ev.location === filters.location);
  }
  if (options?.weekendsOnly) {
    out = out.filter((ev) => eventTouchesWeekend(ev));
  }
  return out;
}

export function calendarIncludesPastRange(
  dateFromStr: string,
  todayKey: string
): boolean {
  return dateFromStr < todayKey;
}

export function computeFetchRange(
  preset: PeriodPreset,
  viewMonth: Date,
  customFrom: string,
  customTo: string
): {
  date_from: string;
  date_to: string;
  weekendsOnly: boolean;
  showPastCalendar: boolean;
} {
  const today = new Date();
  const todayK = dayKey(today);

  if (preset === "all") {
    const from = addMonths(today, -12);
    const end = endOfMonth(addMonths(today, 24));
    const df = dayKey(from);
    const dt = dayKey(end);
    return {
      date_from: df,
      date_to: dt,
      weekendsOnly: false,
      showPastCalendar: df < todayK,
    };
  }

  if (preset === "weekends") {
    const from = addMonths(today, -6);
    const end = endOfMonth(addMonths(today, 12));
    const df = dayKey(from);
    const dt = dayKey(end);
    return {
      date_from: df,
      date_to: dt,
      weekendsOnly: true,
      showPastCalendar: df < todayK,
    };
  }

  if (preset === "this_month") {
    const m0 = startOfMonth(viewMonth);
    const m1 = endOfMonth(viewMonth);
    const fromD = new Date(m0);
    fromD.setDate(fromD.getDate() - 14);
    const toD = new Date(m1);
    toD.setDate(toD.getDate() + 14);
    const df = dayKey(fromD);
    const dt = dayKey(toD);
    return {
      date_from: df,
      date_to: dt,
      weekendsOnly: false,
      showPastCalendar: df < todayK,
    };
  }

  if (preset === "three_months") {
    const m1 = endOfMonth(addMonths(today, 3));
    const df = todayK;
    const dt = dayKey(m1);
    return {
      date_from: df,
      date_to: dt,
      weekendsOnly: false,
      showPastCalendar: false,
    };
  }

  const df = customFrom && /^\d{4}-\d{2}-\d{2}$/.test(customFrom) ? customFrom : todayK;
  const dt =
    customTo && /^\d{4}-\d{2}-\d{2}$/.test(customTo)
      ? customTo
      : customFrom && /^\d{4}-\d{2}-\d{2}$/.test(customFrom)
        ? customFrom
        : todayK;
  const [a, b] = df <= dt ? [df, dt] : [dt, df];
  return {
    date_from: a,
    date_to: b,
    weekendsOnly: false,
    showPastCalendar: a < todayK,
  };
}
