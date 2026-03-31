"use client";

import type { Event } from "@/lib/types";
import { EventCard } from "@/components/EventCard";
import { useTranslations } from "next-intl";

export function UpcomingEvents({ events }: { events: Event[] }) {
  const t = useTranslations("calendar");

  if (!events.length) {
    return (
      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold text-slate-900">
          {t("upcoming")}
        </h2>
        <p className="text-sm text-slate-600">{t("noEventsInSelection")}</p>
      </section>
    );
  }
  return (
    <section className="mt-8">
      <h2 className="mb-3 text-lg font-semibold text-slate-900">
        {t("upcoming")}
      </h2>
      <div className="flex flex-col gap-3">
        {events.map((e) => (
          <EventCard key={e.id} event={e} />
        ))}
      </div>
    </section>
  );
}
