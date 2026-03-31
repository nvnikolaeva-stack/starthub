import { ApiError, getDistances, getEvent, getEvents } from "@/lib/api";

describe("API client", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  test("1: getEvents возвращает массив из ответа", async () => {
    const two = [
      { id: "1", name: "A", date_start: "2026-03-29", date_end: null },
      { id: "2", name: "B", date_start: "2026-03-30", date_end: null },
    ];
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => two,
    }) as unknown as typeof fetch;

    const res = await getEvents();
    expect(res).toHaveLength(2);
    expect(res[0].name).toBe("A");
  });

  test("2: getEvents передаёт sport_type в query", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => [],
    }) as unknown as typeof fetch;

    await getEvents({ sport_type: "running" });
    expect(global.fetch).toHaveBeenCalled();
    const url = (global.fetch as jest.Mock).mock.calls[0][0] as string;
    expect(url).toContain("sport_type=running");
  });

  test("3: getEvent запрашивает URL с id", async () => {
    const ev = {
      id: "abc-123",
      name: "Test",
      date_start: "2026-03-29",
      date_end: null,
      location: "X",
      sport_type: "running",
      url: null,
      notes: null,
      created_by: "u",
      created_at: "2026-01-01T00:00:00",
    };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ev,
    }) as unknown as typeof fetch;

    const res = await getEvent("abc-123");
    expect(res.id).toBe("abc-123");
    const url = (global.fetch as jest.Mock).mock.calls[0][0] as string;
    expect(url).toContain("/api/v1/events/abc-123");
  });

  test("4: при сетевой ошибке fetch getEvents бросает обработанную ApiError", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("network down"));
    let err: unknown;
    try {
      await getEvents();
    } catch (e) {
      err = e;
    }
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).message).toBe("Сервер недоступен");
  });

  test("5: getDistances для triathlon", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({
        distances: ["Sprint", "Olympic", "Half Ironman"],
      }),
    }) as unknown as typeof fetch;

    const d = await getDistances("triathlon");
    expect(d).toEqual(["Sprint", "Olympic", "Half Ironman"]);
  });
});
