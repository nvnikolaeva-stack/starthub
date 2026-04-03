import type {
  CommunityStats,
  Event,
  Participant,
  ParticipantDetail,
  ParticipantStats,
  Registration,
  SimilarEventsResponse,
} from "./types";

const API_URL =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public body?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    let msg = "Сервер недоступен";
    let parsed: unknown;
    try {
      const t = await res.text();
      if (t) {
        try {
          parsed = JSON.parse(t) as unknown;
          if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
            const o = parsed as Record<string, unknown>;
            if (typeof o.message === "string") msg = o.message;
            else if (typeof o.detail === "string") msg = o.detail;
          }
        } catch {
          msg = t.slice(0, 200);
        }
      }
    } catch {
      /* ignore */
    }
    throw new ApiError(msg, res.status, parsed);
  }
  if (res.headers.get("content-type")?.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return res.text() as Promise<T>;
}

/** Lists events. Does not send group_id / for_telegram_id (web shows all public events). */
export async function getEvents(params?: {
  sport_type?: string;
  upcoming?: boolean;
  limit?: number;
  period?: string;
  date_from?: string;
  date_to?: string;
}): Promise<Event[]> {
  const q = new URLSearchParams();
  if (params?.sport_type) q.set("sport_type", params.sport_type);
  if (params?.upcoming !== undefined)
    q.set("upcoming", String(params.upcoming));
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.period) q.set("period", params.period);
  if (params?.date_from) q.set("date_from", params.date_from);
  if (params?.date_to) q.set("date_to", params.date_to);
  const url = `${API_URL}/api/v1/events${q.toString() ? `?${q}` : ""}`;
  try {
    const res = await fetch(url, { cache: "no-store" });
    return await handle<Event[]>(res);
  } catch (e) {
    if (e instanceof ApiError) throw e;
    throw new ApiError("Сервер недоступен");
  }
}

export async function getEvent(id: string): Promise<Event> {
  try {
    const res = await fetch(`${API_URL}/api/v1/events/${id}`, {
      cache: "no-store",
    });
    if (res.status === 404) {
      throw new ApiError("Старт не найден", 404);
    }
    return await handle<Event>(res);
  } catch (e) {
    if (e instanceof ApiError) throw e;
    throw new ApiError("Сервер недоступен");
  }
}

export async function createEvent(
  data: Record<string, unknown>,
  options?: { forceDuplicate?: boolean }
): Promise<Event> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (options?.forceDuplicate) headers["X-Force-Create"] = "true";
  const res = await fetch(`${API_URL}/api/v1/events`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  return handle<Event>(res);
}

export async function searchSimilarEvents(params: {
  name?: string;
  date?: string;
}): Promise<SimilarEventsResponse> {
  const q = new URLSearchParams();
  if (params.name?.trim()) q.set("name", params.name.trim());
  if (params.date) q.set("date", params.date);
  if (!q.toString()) {
    return { exact_matches: [], date_matches: [] };
  }
  const res = await fetch(
    `${API_URL}/api/v1/events/search/similar?${q}`,
    { cache: "no-store" }
  );
  return handle<SimilarEventsResponse>(res);
}

export async function updateEvent(
  id: string,
  data: Record<string, unknown>
): Promise<Event> {
  const res = await fetch(`${API_URL}/api/v1/events/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handle<Event>(res);
}

export async function deleteEvent(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/v1/events/${id}`, {
    method: "DELETE",
  });
  await handle<void>(res);
}

export async function getDistances(sportType: string): Promise<string[]> {
  const res = await fetch(`${API_URL}/api/v1/distances/${sportType}`, {
    cache: "no-store",
  });
  const j = await handle<{ distances: string[] }>(res);
  return j.distances || [];
}

export async function listParticipants(): Promise<Participant[]> {
  const res = await fetch(`${API_URL}/api/v1/participants`, {
    cache: "no-store",
  });
  return handle<Participant[]>(res);
}

export async function getParticipant(id: string): Promise<ParticipantDetail> {
  const res = await fetch(`${API_URL}/api/v1/participants/${id}`, {
    cache: "no-store",
  });
  return handle<ParticipantDetail>(res);
}

export async function getParticipantStats(
  id: string
): Promise<ParticipantStats> {
  const res = await fetch(`${API_URL}/api/v1/stats/participant/${id}`, {
    cache: "no-store",
  });
  return handle<ParticipantStats>(res);
}

export async function createParticipant(data: {
  display_name: string;
}): Promise<Participant> {
  const res = await fetch(`${API_URL}/api/v1/participants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handle<Participant>(res);
}

export async function createRegistration(data: {
  event_id: string;
  participant_id: string;
  distances: string[];
}): Promise<Registration> {
  const res = await fetch(`${API_URL}/api/v1/registrations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_id: data.event_id,
      participant_id: data.participant_id,
      distances: data.distances,
    }),
  });
  return handle<Registration>(res);
}

export async function getCommunityStats(): Promise<CommunityStats> {
  const res = await fetch(`${API_URL}/api/v1/stats/community`, {
    cache: "no-store",
  });
  return handle<CommunityStats>(res);
}

export async function getEventIcal(id: string): Promise<Blob> {
  const res = await fetch(`${API_URL}/api/v1/events/${id}/ical`, {
    cache: "no-store",
    method: "GET",
    headers: { Accept: "text/calendar,*/*" },
  });
  if (!res.ok) throw new ApiError("Не удалось скачать .ics", res.status);
  return res.blob();
}

export { API_URL };
