"use client";

import type { Event } from "@/lib/types";
import {
  dayKey,
  monthShortLabelLocalized,
  parseISODate,
  weekdayShortLocalized,
} from "@/lib/dates";
import { SPORT_CARD_DATE, SPORT_DOT } from "@/lib/sport";
import { participantNamesPreview } from "@/components/CalendarDay";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { ChevronRight } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useIsMobile } from "@/hooks/use-is-mobile";

function eventDistances(ev: Event): string {
  const regs = ev.registrations;
  if (!regs?.length) return "";
  const set = new Set<string>();
  for (const r of regs) {
    for (const d of r.distances || []) {
      if (d) set.add(d);
    }
  }
  return [...set].join(", ");
}

type Props = {
  event: Event;
  /** Desktop: открыть боковую панель вместо полного перехода */
  enableQuickView?: boolean;
  onQuickView?: (event: Event) => void;
};

export function EventCard({
  event,
  enableQuickView = false,
  onQuickView,
}: Props) {
  const locale = useLocale();
  const t = useTranslations("event");
  const tf = useTranslations("filters");
  const isMobile = useIsMobile();
  const today = dayKey(new Date());
  const end = (event.date_end || event.date_start).slice(0, 10);
  const isPast = end < today;

  const start = parseISODate(event.date_start.slice(0, 10));
  const dateStyle = SPORT_CARD_DATE[event.sport_type];
  const regs = event.registrations;
  const count = regs?.length ?? 0;

  const namesStr = participantNamesPreview(event, 3, {
    defaultParticipant: t("defaultParticipant"),
    andMore: (n) => t("participantsAndMore", { count: n }),
  });

  const dist = eventDistances(event);
  const sportLabel = tf(event.sport_type);
  const metaParts = [event.location, dist, sportLabel].filter(Boolean);
  const meta = metaParts.join(" · ");

  const tertiary =
    count > 0
      ? [namesStr, t("participantsCountInline", { count })].filter(Boolean).join(" · ")
      : t("noParticipantsShort");

  const quick =
    enableQuickView &&
    onQuickView &&
    !isMobile &&
    event.id !== "preview";

  return (
    <Link
      href={`/event/${event.id}`}
      onClick={(e) => {
        if (quick) {
          e.preventDefault();
          onQuickView(event);
        }
      }}
      className={cn(
        "card relative group flex min-h-11 gap-3 overflow-hidden py-2 pl-3 pr-2 no-underline transition-colors sm:min-h-[72px]",
        "hover:bg-[var(--color-surface-hover)]",
        isPast && "opacity-50"
      )}
      data-testid={`event-card-${event.id}`}
    >
      <span
        className="absolute bottom-0 left-0 top-0 w-[3px] rounded-sm"
        style={{ background: SPORT_DOT[event.sport_type] }}
        aria-hidden
      />
      <div
        className="flex w-[48px] shrink-0 flex-col items-center justify-center rounded-[var(--radius-sm)] px-1.5 py-1 text-center leading-tight"
        style={{
          background: dateStyle.bg,
          color: dateStyle.text,
        }}
      >
        <span className="text-[17px] font-medium leading-none">
          {start.getDate()}
        </span>
        <span className="mt-0.5 text-[11px] font-medium">
          {monthShortLabelLocalized(start, locale)}
        </span>
        <span className="text-[10px] font-medium opacity-90">
          {weekdayShortLocalized(start, locale)}
        </span>
      </div>
      <div className="flex min-w-0 flex-1 flex-col justify-center gap-0.5 pr-6">
        <div className="flex items-start justify-between gap-2">
          <h3
            className="truncate text-base font-medium leading-snug text-[var(--color-text)]"
            style={{ fontWeight: 500 }}
          >
            {event.name}
          </h3>
          {isPast ? (
            <span className="shrink-0 rounded-[var(--radius-full)] bg-[var(--color-surface-tinted)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-text-muted)]">
              {t("completed")}
            </span>
          ) : null}
        </div>
        <p className="truncate text-sm text-[var(--color-text-secondary)]">
          {meta}
        </p>
        <p
          className="truncate text-[13px] text-[var(--color-text-muted)]"
          data-testid="event-card-participants"
        >
          {tertiary}
        </p>
      </div>
      <ChevronRight
        className="absolute right-2 top-1/2 h-5 w-5 -translate-y-1/2 text-[var(--color-text-placeholder)] group-hover:text-[var(--color-text-secondary)]"
        aria-hidden
      />
    </Link>
  );
}
