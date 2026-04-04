/**
 * @jest-environment jsdom
 */
import type { ReactElement } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { EventCardFull } from "@/components/EventCardFull";
import ru from "@/messages/ru.json";

function renderFull(ui: ReactElement) {
  return render(
    <NextIntlClientProvider locale="ru" messages={ru}>
      {ui}
    </NextIntlClientProvider>
  );
}

const push = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push,
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}));

describe("EventCardFull (страница старта)", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  test("19: полная информация о старте и участниках", async () => {
    const payload = {
      id: "id-1",
      name: "Ironstar Sochi",
      date_start: "2026-06-15",
      date_end: "2026-06-17",
      location: "Сочи",
      sport_type: "triathlon",
      url: "https://ironstar.com",
      notes: "Гидро",
      created_by: "bot",
      created_at: "2026-01-01T00:00:00",
      registrations: [
        {
          id: "r1",
          event_id: "id-1",
          participant_id: "p1",
          distances: ["Olympic"],
          result_time: "2:15:30",
          result_place: "15/120",
          participant_display_name: "Алексей",
          participant_telegram_username: "alexrun",
        },
      ],
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => payload,
    }) as unknown as typeof fetch;

    renderFull(<EventCardFull eventId="id-1" />);

    await waitFor(() => {
      expect(screen.getByText("Ironstar Sochi")).toBeInTheDocument();
    });
    expect(screen.getByText(/Сочи/)).toBeInTheDocument();
    expect(screen.getByText(/Алексей/)).toBeInTheDocument();
    expect(screen.getByText(/2:15:30/)).toBeInTheDocument();
    expect(screen.getByText(/15\/120/)).toBeInTheDocument();
  });

  test("20: кнопки действий видны", async () => {
    const payload = {
      id: "id-2",
      name: "X",
      date_start: "2026-06-01",
      date_end: null,
      location: "L",
      sport_type: "running",
      url: null,
      notes: null,
      created_by: "b",
      created_at: "2026-01-01T00:00:00",
      registrations: [],
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => payload,
    }) as unknown as typeof fetch;

    renderFull(<EventCardFull eventId="id-2" />);

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Добавить в календарь/ })).toBeInTheDocument()
    );
    expect(screen.getByRole("button", { name: /Я тоже еду/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Редактировать/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Удалить/ })).toBeInTheDocument();
  });

  test("21: 404 — сообщение «Старт не найден»", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      headers: new Headers(),
      text: async () => "gone",
    }) as unknown as typeof fetch;

    renderFull(<EventCardFull eventId="missing" />);

    await waitFor(() => {
      expect(screen.getByText("Старт не найден")).toBeInTheDocument();
    });
  });
});
