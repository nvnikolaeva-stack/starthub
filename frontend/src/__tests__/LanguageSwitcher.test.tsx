/**
 * @jest-environment jsdom
 */
import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { Navbar } from "@/components/Navbar";
import { HomeCalendar } from "@/components/HomeCalendar";
import ru from "@/messages/ru.json";

jest.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    refresh: jest.fn(),
  }),
}));

jest.mock("@/hooks/use-is-mobile", () => ({
  useIsMobile: () => false,
}));

jest.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {},
  getEvents: jest.fn().mockResolvedValue([]),
  getEvent: jest.fn(),
  getDistances: jest.fn().mockResolvedValue([]),
  listParticipants: jest.fn().mockResolvedValue([]),
}));

describe("Navbar / локаль", () => {
  test("нет кнопки переключения EN/RU", () => {
    render(
      <NextIntlClientProvider locale="ru" messages={ru}>
        <Navbar />
      </NextIntlClientProvider>
    );
    expect(screen.queryByRole("button", { name: /english/i })).toBeNull();
    expect(screen.queryByText("EN")).toBeNull();
  });

  test("язык по умолчанию ru — заголовок календаря по-русски", async () => {
    render(
      <NextIntlClientProvider locale="ru" messages={ru}>
        <HomeCalendar />
      </NextIntlClientProvider>
    );
    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "Календарь стартов",
      })
    ).toBeInTheDocument();
    expect(screen.queryByText("Event calendar")).not.toBeInTheDocument();
  });
});
