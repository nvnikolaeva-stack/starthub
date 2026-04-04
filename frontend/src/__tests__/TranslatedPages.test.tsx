/**
 * @jest-environment jsdom
 */
import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { HomeCalendar } from "@/components/HomeCalendar";
import { AddEventForm } from "@/components/AddEventForm";
import { StatsPageContent } from "@/components/StatsPageContent";
import ru from "@/messages/ru.json";

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
    total_events: 2,
    total_participants: 1,
    most_active_participant: {
      display_name: "Runner",
      registrations_count: 2,
    },
    popular_sports: [{ sport_type: "running", count: 2 }],
    popular_locations: [{ location: "City", count: 1 }],
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
      expect(sportSelect).toBeInTheDocument();
      expect(screen.getByPlaceholderText("Поиск...")).toBeInTheDocument();
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
});
