/**
 * @jest-environment jsdom
 */
import { render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { HomeCalendar } from "@/components/HomeCalendar";
import { AddEventForm } from "@/components/AddEventForm";
import { StatsPageContent } from "@/components/StatsPageContent";
import ru from "@/messages/ru.json";
import en from "@/messages/en.json";

jest.mock("@/hooks/use-is-mobile", () => ({
  useIsMobile: () => false,
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

jest.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {},
  getEvents: jest.fn().mockResolvedValue([]),
  getEvent: jest.fn(),
  listParticipants: jest.fn().mockResolvedValue([]),
  getDistances: jest.fn().mockResolvedValue(["5 km", "10 km"]),
  createEvent: jest.fn(),
  createParticipant: jest.fn(),
  createRegistration: jest.fn(),
  getCommunityStats: jest.fn().mockResolvedValue({
    total_events: 0,
    total_participants: 0,
    most_active_participant: null,
    popular_sports: [],
    popular_locations: [],
  }),
  getParticipantStats: jest.fn(),
  getParticipant: jest.fn(),
}));

describe("TranslatedPages", () => {
  describe("RU", () => {
    test("10: главная — ключевые подписи на русском", async () => {
      render(
        <NextIntlClientProvider locale="ru" messages={ru}>
          <HomeCalendar />
        </NextIntlClientProvider>
      );
      expect(
        await screen.findByRole("heading", { name: "Календарь стартов" })
      ).toBeInTheDocument();
      expect(screen.getByText("Ближайшие старты")).toBeInTheDocument();
      const sportSelect = screen.getByLabelText("Спорт");
      const bar = sportSelect.closest("div.sticky") as HTMLElement;
      expect(within(bar).getByPlaceholderText("Поиск...")).toBeInTheDocument();
      const opts = [...(sportSelect as HTMLSelectElement).options].map((o) => o.text);
      expect(opts.some((x) => /Плавание/.test(x))).toBe(true);
      expect(opts.some((x) => /Бег/.test(x))).toBe(true);
    });

    test("11: форма добавления на русском", async () => {
      render(
        <NextIntlClientProvider locale="ru" messages={ru}>
          <AddEventForm />
        </NextIntlClientProvider>
      );
      expect(
        await screen.findByRole("heading", { name: "Добавить старт" })
      ).toBeInTheDocument();
      expect(screen.getByText("Вид спорта")).toBeInTheDocument();
      expect(screen.getByText("Название старта")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Сохранить старт/ })
      ).toBeInTheDocument();
    });

    test("12: статистика на русском", async () => {
      render(
        <NextIntlClientProvider locale="ru" messages={ru}>
          <StatsPageContent />
        </NextIntlClientProvider>
      );
      expect(
        await screen.findByRole("heading", { name: "Статистика" })
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Команда" })).toBeInTheDocument();
      expect(screen.getAllByText(/Участников/).length).toBeGreaterThan(0);
    });
  });

  describe("EN", () => {
    test("13: главная на английском", async () => {
      render(
        <NextIntlClientProvider locale="en" messages={en}>
          <HomeCalendar />
        </NextIntlClientProvider>
      );
      expect(
        await screen.findByRole("heading", { name: "Event calendar" })
      ).toBeInTheDocument();
      expect(screen.getByText("Upcoming events")).toBeInTheDocument();
      const sportSelect = screen.getByLabelText("Sport");
      const bar = sportSelect.closest("div.sticky") as HTMLElement;
      expect(within(bar).getByPlaceholderText("Search…")).toBeInTheDocument();
      const opts = [...(sportSelect as HTMLSelectElement).options].map((o) => o.text);
      expect(opts.some((x) => /Swimming/i.test(x))).toBe(true);
      expect(opts.some((x) => /Running/i.test(x))).toBe(true);
    });

    test("14: форма на английском", async () => {
      render(
        <NextIntlClientProvider locale="en" messages={en}>
          <AddEventForm />
        </NextIntlClientProvider>
      );
      expect(
        await screen.findByRole("heading", { name: "Add event" })
      ).toBeInTheDocument();
      expect(screen.getByText("Sport type")).toBeInTheDocument();
      expect(screen.getByText("Event name")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Save event/ })
      ).toBeInTheDocument();
    });

    test("15: статистика на английском", async () => {
      render(
        <NextIntlClientProvider locale="en" messages={en}>
          <StatsPageContent />
        </NextIntlClientProvider>
      );
      expect(
        await screen.findByRole("heading", { name: "Statistics" })
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Team" })).toBeInTheDocument();
      expect(screen.getByText(/Participants/)).toBeInTheDocument();
    });
  });

  test("16: на EN-главной нет типичных русских UI-строк (пустые данные API)", async () => {
    render(
      <NextIntlClientProvider locale="en" messages={en}>
        <HomeCalendar />
      </NextIntlClientProvider>
    );
    await screen.findByRole("heading", { name: "Event calendar" });
    const body = document.body.textContent ?? "";
    const forbidden = [
      "Календарь стартов",
      "Ближайшие старты",
      "Плавание",
      "Бег",
      "Добавить старт",
    ];
    for (const frag of forbidden) {
      expect(body).not.toContain(frag);
    }
  });
});
