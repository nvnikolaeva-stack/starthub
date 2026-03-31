"use client";

import type { Event, Registration, SportType } from "@/lib/types";
import {
  eventOverlapsDay,
  dayKey,
  formatDayMonthLocalized,
} from "@/lib/dates";
import { SPORT_DOT } from "@/lib/sport";
import { Tooltip } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useLocale, useTranslations } from "next-intl";

const NAME_MAX = 10;

function truncateName(name: string): string {
  const t = name.trim();
  if (t.length <= NAME_MAX) return t;
  return `${t.slice(0, NAME_MAX)}…`;
}

type Props = {
  date: Date | null;
  todayKey: string;
  events: Event[];
  showPast: boolean;
  selectedDayKey: string | null;
  onSelectDay: (d: Date) => void;
  dayId?: string;
  dimmedPast?: boolean;
  /** Month grid: small cell (day number + sport dot only), ≥44px tap target */
  monthCompact?: boolean;
};

export function participantNamesPreview(
  ev: Event,
  max = 3,
  labels?: {
    defaultParticipant: string;
    andMore: (extra: number) => string;
  }
): string {
  const def = labels?.defaultParticipant ?? "—";
  const regName = (r: Registration) =>
    r.participant_display_name || r.participant?.display_name || def;
  const regs = ev.registrations;
  if (!regs?.length) return "";
  const names = regs.map(regName).filter(Boolean);
  if (names.length <= max) return names.join(", ");
  const head = names.slice(0, max).join(", ");
  if (labels?.andMore) return `${head} ${labels.andMore(names.length - max)}`;
  return `${head} (+${names.length - max})`;
}

export function CalendarDay({
  date,
  todayKey,
  events,
  showPast,
  selectedDayKey,
  onSelectDay,
  dayId,
  dimmedPast,
  monthCompact = false,
}: Props) {
  const locale = useLocale();
  const t = useTranslations("calendar");

  if (!date) {
    return (
      <div
        className={cn(
          "bg-transparent",
          monthCompact ? "min-h-11 sm:min-h-[104px]" : "min-h-[104px] sm:min-h-[112px]"
        )}
      />
    );
  }

  const key = dayKey(date);
  const dayEvents = events.filter((e) => eventOverlapsDay(e, date));
  const isToday = key === todayKey;
  const weekend = date.getDay() === 0 || date.getDay() === 6;
  const isPastDay = key < todayKey;
  const hideCompletely = isPastDay && !showPast;
  const selected = selectedDayKey === key;

  const sorted = [...dayEvents].sort((a, b) =>
    a.date_start.localeCompare(b.date_start)
  );
  const pillEvents = sorted.slice(0, 2);
  const moreCount = sorted.length > 2 ? sorted.length - 2 : 0;

  const tooltipLines = [
    `${formatDayMonthLocalized(date, locale)}`,
    ...sorted.map((e) => `· ${e.name}`),
  ].join("\n");

  if (hideCompletely) {
    return (
      <div
        className={cn(
          "rounded-[var(--radius-md)] border border-transparent",
          monthCompact ? "min-h-11 sm:min-h-[104px]" : "min-h-[104px] sm:min-h-[112px]"
        )}
        aria-hidden
      >
        <span className="sr-only">{formatDayMonthLocalized(date, locale)}</span>
      </div>
    );
  }

  const dotSport = sorted[0]?.sport_type as SportType | undefined;
  const showDot = sorted.length > 0;

  if (monthCompact) {
    return (
      <Tooltip content={tooltipLines}>
        <button
          type="button"
          id={dayId}
          data-testid={`calendar-cell-${key}`}
          onClick={() => onSelectDay(date)}
          className={cn(
            "flex min-h-11 w-full flex-col items-center justify-center gap-0.5 rounded-[var(--radius-md)] border px-0.5 py-1 text-center transition-colors",
            weekend && "bg-[var(--color-surface-tinted)]",
            !weekend && "bg-[var(--color-surface)]",
            isToday && "border-2 border-[var(--color-primary)]",
            selected &&
              !isToday &&
              "border-2 border-[var(--color-primary)] bg-[var(--color-surface-tinted)]",
            selected && isToday && "bg-[var(--color-surface-tinted)]",
            !isToday && !selected && "border border-[var(--color-border)]",
            dimmedPast && "opacity-50",
            "cursor-pointer hover:border-[var(--color-border-hover)]"
          )}
        >
          <span className="text-[13px] font-medium leading-none text-[var(--color-text)]">
            {date.getDate()}
          </span>
          <span
            className="h-1.5 w-1.5 shrink-0 rounded-full"
            style={{
              background: showDot
                ? SPORT_DOT[dotSport ?? "other"]
                : "transparent",
            }}
            aria-hidden
          />
        </button>
      </Tooltip>
    );
  }

  return (
    <Tooltip content={tooltipLines}>
      <button
        type="button"
        id={dayId}
        data-testid={`calendar-cell-${key}`}
        onClick={() => onSelectDay(date)}
        className={cn(
          "flex min-h-[104px] w-full flex-col rounded-[var(--radius-md)] border p-1.5 text-left transition-colors sm:min-h-[112px]",
          weekend && "bg-[var(--color-surface-tinted)]",
          !weekend && "bg-[var(--color-surface)]",
          isToday && "border-2 border-[var(--color-primary)]",
          selected &&
            !isToday &&
            "border-2 border-[var(--color-primary)] bg-[var(--color-surface-tinted)]",
          selected && isToday && "bg-[var(--color-surface-tinted)]",
          !isToday && !selected && "border border-[var(--color-border)]",
          dimmedPast && "opacity-50",
          "cursor-pointer hover:border-[var(--color-border-hover)]"
        )}
      >
        <span
          className="text-[15px] font-medium leading-tight text-[var(--color-text)]"
          style={{ fontWeight: 500 }}
        >
          {date.getDate()}
        </span>
        <div className="mt-1 flex min-h-0 flex-1 flex-col gap-0.5 overflow-hidden">
          {pillEvents.map((ev, i) => (
            <div
              key={`${ev.id}-${i}`}
              data-testid={`calendar-event-pill-${ev.id}`}
              className="flex h-5 w-full min-w-0 max-w-full items-center overflow-hidden rounded bg-[var(--color-bg)] text-[11px] text-[var(--color-text)]"
            >
              <span
                className="h-full w-[3px] shrink-0 rounded-sm"
                style={{ background: SPORT_DOT[ev.sport_type as SportType] }}
                aria-hidden
              />
              <span className="min-w-0 flex-1 truncate pl-1 pr-1">
                {truncateName(ev.name)}
              </span>
            </div>
          ))}
          {moreCount > 0 ? (
            <span className="pl-0.5 text-[10px] font-medium text-[var(--color-text-muted)]">
              {t("detailMoreCount", { count: moreCount })}
            </span>
          ) : null}
        </div>
      </button>
    </Tooltip>
  );
}
