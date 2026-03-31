import { EventCardFull } from "@/components/EventCardFull";

type Props = {
  params: Promise<{ id: string }> | { id: string };
};

export default async function EventPage({ params }: Props) {
  const p = await Promise.resolve(params);
  return <EventCardFull eventId={p.id} />;
}
