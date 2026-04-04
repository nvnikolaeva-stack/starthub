import { Suspense } from "react";
import { EventCardFull } from "@/components/EventCardFull";

type Props = {
  params: Promise<{ id: string }> | { id: string };
};

export default async function EventPage({ params }: Props) {
  const p = await Promise.resolve(params);
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl px-4 py-10 text-slate-600">
          Загрузка…
        </div>
      }
    >
      <EventCardFull eventId={p.id} />
    </Suspense>
  );
}
