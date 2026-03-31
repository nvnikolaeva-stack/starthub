import { AddEventForm } from "@/components/AddEventForm";

export default async function AddEventPage({
  searchParams,
}: {
  searchParams: Promise<{ date?: string }>;
}) {
  const q = await searchParams;
  return <AddEventForm initialDate={q.date} />;
}
