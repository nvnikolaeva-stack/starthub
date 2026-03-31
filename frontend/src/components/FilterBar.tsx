"use client";

import type { SportType } from "@/lib/types";
import type { CalendarFiltersState, PeriodPreset } from "@/lib/calendarFilters";
import { Dialog } from "@/components/ui/dialog";
import { monthTitle } from "@/lib/dates";
import { Search } from "lucide-react";
import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";
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

function selectClass(
  short?: boolean,
  variant: "desktop" | "sheet" = "desktop"
) {
  return cn(
    variant === "sheet" ? "min-h-11" : "h-9",
    "rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-sm text-[var(--color-text)]",
    short ? "max-w-[10rem]" : "min-w-[7rem]"
  );
}

function FilterFields({
  filters,
  onFiltersChange,
  distanceOptions,
  locations,
  variant,
}: {
  filters: CalendarFiltersState;
  onFiltersChange: (p: Partial<CalendarFiltersState>) => void;
  distanceOptions: string[];
  locations: string[];
  variant: "desktop" | "sheet";
}) {
  const t = useTranslations("filters");
  const tf = useTranslations("filters");

  const sportLabel = (s: SportType | "all") =>
    s === "all" ? t("all") : tf(s);

  return (
    <div
      className={cn(
        "flex flex-col gap-3",
        variant === "desktop" && "lg:flex-row lg:flex-wrap lg:items-center"
      )}
    >
      <div
        className={cn(
          "relative flex min-w-0 flex-1",
          variant === "sheet" && "w-full"
        )}
      >
        <Search
          className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-placeholder)]"
          aria-hidden
        />
        <input
          type="search"
          value={filters.search}
          onChange={(e) => onFiltersChange({ search: e.target.value })}
          placeholder={t("searchPlaceholder")}
          className={cn(
            "w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] py-1 pl-9 pr-3 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)]",
            variant === "sheet" ? "min-h-11" : "h-9"
          )}
        />
      </div>

      <select
        className={selectClass(false, variant)}
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
        className={selectClass(false, variant)}
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
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="date"
            value={filters.customDateFrom}
            onChange={(e) =>
              onFiltersChange({ customDateFrom: e.target.value })
            }
            className={selectClass(false, variant)}
            aria-label={t("customDateFrom")}
          />
          <span className="text-[var(--color-text-muted)]">—</span>
          <input
            type="date"
            value={filters.customDateTo}
            onChange={(e) =>
              onFiltersChange({ customDateTo: e.target.value })
            }
            className={selectClass(false, variant)}
            aria-label={t("customDateTo")}
          />
        </div>
      ) : null}

      <select
        className={selectClass(true, variant)}
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
        className={selectClass(true, variant)}
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
  const [sheetOpen, setSheetOpen] = useState(false);

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
    <div className="sticky top-14 z-30 -mx-4 mb-3 border-b border-[var(--color-border)] bg-[var(--color-surface)]/95 px-4 py-2 backdrop-blur">
      <div className="hidden lg:flex lg:flex-wrap lg:items-center lg:gap-2">
        <FilterFields
          filters={filters}
          onFiltersChange={onFiltersChange}
          distanceOptions={distanceOptions}
          locations={locations}
          variant="desktop"
        />
        {hasActive ? (
          <button
            type="button"
            className="min-h-11 shrink-0 rounded-[var(--radius-md)] px-3 text-sm font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)]"
            onClick={onResetAll}
          >
            {t("reset")}
          </button>
        ) : null}
      </div>

      <div className="flex items-center gap-2 lg:hidden">
        <button
          type="button"
          className="flex min-h-11 flex-1 items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-tinted)] px-3 text-sm font-medium text-[var(--color-text)]"
          onClick={() => setSheetOpen(true)}
        >
          <span>{t("filtersButtonLabel")}</span>
          {activeCount > 0 ? (
            <span className="min-w-[1.35rem] rounded-full bg-[var(--color-accent)] px-1.5 py-0.5 text-center text-xs font-semibold tabular-nums text-[var(--color-accent-text)]">
              {activeCount}
            </span>
          ) : null}
        </button>
        {hasActive ? (
          <button
            type="button"
            className="min-h-11 shrink-0 px-3 text-sm font-medium text-[var(--color-info)]"
            onClick={onResetAll}
          >
            {t("resetAll")}
          </button>
        ) : null}
      </div>

      <Dialog
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        title={t("filtersSheetTitle")}
        className="sm:max-w-lg"
      >
        <FilterFields
          filters={filters}
          onFiltersChange={onFiltersChange}
          distanceOptions={distanceOptions}
          locations={locations}
          variant="sheet"
        />
        <div className="mt-4 flex justify-end gap-2 border-t border-[var(--color-border)] pt-3">
          <button
            type="button"
            className="min-h-11 rounded-[var(--radius-md)] px-4 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-surface-hover)]"
            onClick={() => setSheetOpen(false)}
          >
            {t("done")}
          </button>
        </div>
      </Dialog>

      {hasActive ? (
        <div className="mt-2 flex items-center gap-2 border-t border-[var(--color-border)] pt-2">
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
            className="min-h-11 shrink-0 px-1 text-sm font-medium text-[var(--color-info)]"
            onClick={onResetAll}
          >
            {t("resetAll")}
          </button>
        </div>
      ) : null}
    </div>
  );
}
