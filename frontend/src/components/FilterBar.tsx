"use client";

import type { SportType } from "@/lib/types";
import type { CalendarFiltersState, PeriodPreset } from "@/lib/calendarFilters";
import { monthTitle } from "@/lib/dates";
import { Search } from "lucide-react";
import { useTranslations } from "next-intl";
import { useMemo } from "react";
import { cn } from "@/lib/utils";

const SPORTS: (SportType | "all")[] = [
  "all",
  "swimming",
  "running",
  "cycling",
  "triathlon",
  "other",
];

function isSameMonth(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth();
}

const fieldClass =
  "h-10 rounded-[var(--radius-md)] border border-solid border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm leading-none text-[var(--color-text)]";

function Chip({
  label,
  onRemove,
}: {
  label: string;
  onRemove: () => void;
}) {
  return (
    <span className="inline-flex min-h-9 max-w-[min(100%,280px)] shrink-0 items-center gap-1 rounded-[var(--radius-full)] border border-[var(--color-border)] bg-[var(--color-surface-tinted)] px-2.5 py-1 text-xs font-medium text-[var(--color-text)]">
      <span className="truncate">{label}</span>
      <button
        type="button"
        className="flex h-9 min-h-9 w-9 min-w-9 shrink-0 items-center justify-center rounded-full hover:bg-[var(--color-surface-hover)]"
        aria-label="Remove"
        onClick={onRemove}
      >
        ✕
      </button>
    </span>
  );
}

export function FilterBar({
  filters,
  onFiltersChange,
  viewMonth,
  onViewMonthChange,
  distanceOptions,
  locations,
  onResetAll,
}: {
  filters: CalendarFiltersState;
  onFiltersChange: (p: Partial<CalendarFiltersState>) => void;
  viewMonth: Date;
  onViewMonthChange: (d: Date) => void;
  distanceOptions: string[];
  locations: string[];
  onResetAll: () => void;
}) {
  const t = useTranslations("filters");
  const tf = useTranslations("filters");

  const offMonth =
    filters.periodPreset === "this_month" &&
    !isSameMonth(viewMonth, new Date());

  const { activeCount, hasActive } = useMemo(() => {
    let n = 0;
    if (filters.search.trim()) n++;
    if (filters.sport !== "all") n++;
    if (filters.periodPreset !== "this_month") n++;
    if (offMonth) n++;
    if (filters.distance) n++;
    if (filters.location) n++;
    return { activeCount: n, hasActive: n > 0 };
  }, [filters, offMonth]);

  const sportLabel = (s: SportType | "all") =>
    s === "all" ? t("all") : tf(s);

  const periodChipLabel = (p: PeriodPreset): string => {
    switch (p) {
      case "all":
        return t("periodAll");
      case "weekends":
        return t("periodWeekends");
      case "this_month":
        return monthTitle(viewMonth);
      case "three_months":
        return t("periodThreeMonths");
      case "custom": {
        const a = filters.customDateFrom || "…";
        const b = filters.customDateTo || a;
        return `${a}–${b}`;
      }
    }
  };

  return (
    <div className="mb-3 rounded-[var(--radius-lg)] border border-solid border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <div className="flex flex-col gap-3 md:flex-row md:flex-wrap md:items-center md:gap-3">
        {/* Search — full width on mobile; desktop min width + grow */}
        <div className="relative w-full min-w-0 md:min-w-[200px] md:flex-1">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-placeholder)]"
            aria-hidden
          />
          <input
            type="search"
            value={filters.search}
            onChange={(e) => onFiltersChange({ search: e.target.value })}
            placeholder={t("searchPlaceholder")}
            className={cn(
              fieldClass,
              "w-full min-w-0 py-0 pl-9 pr-3 placeholder:text-[var(--color-text-placeholder)]"
            )}
          />
        </div>

        {/* Secondary filters — horizontal scroll on mobile; one row with gap-3 on desktop */}
        <div className="flex w-full min-w-0 flex-nowrap gap-3 overflow-x-auto pb-0.5 [-webkit-overflow-scrolling:touch] [scrollbar-width:thin] md:contents md:w-auto md:overflow-visible">
          <select
            className={cn(
              fieldClass,
              "min-w-[120px] shrink-0 py-0 md:min-w-[120px]"
            )}
            value={filters.sport}
            onChange={(e) =>
              onFiltersChange({
                sport: e.target.value as SportType | "all",
              })
            }
            aria-label={t("sportLabel")}
          >
            {SPORTS.map((s) => (
              <option key={s} value={s}>
                {sportLabel(s)}
              </option>
            ))}
          </select>

          <select
            className={cn(
              fieldClass,
              "min-w-[120px] shrink-0 py-0 md:min-w-[140px]"
            )}
            value={filters.periodPreset}
            onChange={(e) =>
              onFiltersChange({
                periodPreset: e.target.value as PeriodPreset,
              })
            }
            aria-label={t("periodLabel")}
          >
            <option value="all">{t("periodAll")}</option>
            <option value="weekends">{t("periodWeekends")}</option>
            <option value="this_month">{t("periodThisMonth")}</option>
            <option value="three_months">{t("periodThreeMonths")}</option>
            <option value="custom">{t("periodCustom")}</option>
          </select>

          {filters.periodPreset === "custom" ? (
            <div className="flex shrink-0 items-center gap-2">
              <input
                type="date"
                value={filters.customDateFrom}
                onChange={(e) =>
                  onFiltersChange({ customDateFrom: e.target.value })
                }
                className={cn(fieldClass, "min-w-[9.5rem] py-0")}
                aria-label={t("customDateFrom")}
              />
              <span className="shrink-0 text-[var(--color-text-muted)]">
                —
              </span>
              <input
                type="date"
                value={filters.customDateTo}
                onChange={(e) =>
                  onFiltersChange({ customDateTo: e.target.value })
                }
                className={cn(fieldClass, "min-w-[9.5rem] py-0")}
                aria-label={t("customDateTo")}
              />
            </div>
          ) : null}

          <select
            className={cn(
              fieldClass,
              "min-w-[120px] shrink-0 py-0 md:min-w-[120px]"
            )}
            value={filters.distance}
            onChange={(e) => onFiltersChange({ distance: e.target.value })}
            aria-label={t("distanceLabel")}
          >
            <option value="">{t("distanceAll")}</option>
            {distanceOptions.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          <select
            className={cn(
              fieldClass,
              "min-w-[120px] shrink-0 py-0 md:min-w-[120px]"
            )}
            value={filters.location}
            onChange={(e) => onFiltersChange({ location: e.target.value })}
            aria-label={t("locationLabel")}
          >
            <option value="">{t("locationAll")}</option>
            {locations.map((loc) => (
              <option key={loc} value={loc}>
                {loc}
              </option>
            ))}
          </select>
        </div>

        {hasActive ? (
          <button
            type="button"
            className="h-10 shrink-0 self-start rounded-[var(--radius-md)] px-3 text-sm font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] md:self-center"
            onClick={onResetAll}
          >
            {t("reset")}
          </button>
        ) : null}
      </div>

      {hasActive ? (
        <div className="mt-3 flex items-center gap-2 border-t border-solid border-[var(--color-border)] pt-3">
          <div className="flex min-w-0 flex-1 gap-2 overflow-x-auto py-0.5 [scrollbar-width:thin]">
            {filters.search.trim() ? (
              <Chip
                label={`${t("searchChip")}: ${filters.search.trim()}`}
                onRemove={() => onFiltersChange({ search: "" })}
              />
            ) : null}
            {filters.sport !== "all" ? (
              <Chip
                label={sportLabel(filters.sport)}
                onRemove={() => onFiltersChange({ sport: "all" })}
              />
            ) : null}
            {offMonth ? (
              <Chip
                label={monthTitle(viewMonth)}
                onRemove={() => onViewMonthChange(new Date())}
              />
            ) : null}
            {filters.periodPreset !== "this_month" ? (
              <Chip
                label={periodChipLabel(filters.periodPreset)}
                onRemove={() =>
                  onFiltersChange({
                    periodPreset: "this_month",
                    customDateFrom: "",
                    customDateTo: "",
                  })
                }
              />
            ) : null}
            {filters.distance ? (
              <Chip
                label={filters.distance}
                onRemove={() => onFiltersChange({ distance: "" })}
              />
            ) : null}
            {filters.location ? (
              <Chip
                label={filters.location}
                onRemove={() => onFiltersChange({ location: "" })}
              />
            ) : null}
          </div>
          <button
            type="button"
            className="h-10 shrink-0 px-1 text-sm font-medium text-[var(--color-info)]"
            onClick={onResetAll}
          >
            {t("resetAll")}
          </button>
        </div>
      ) : null}
    </div>
  );
}
