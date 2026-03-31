/**
 * @jest-environment jsdom
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { Navbar } from "@/components/Navbar";
import { HomeCalendar } from "@/components/HomeCalendar";
import ru from "@/messages/ru.json";
import en from "@/messages/en.json";

const mockRefresh = jest.fn();

jest.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    refresh: mockRefresh,
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

describe("LanguageSwitcher / Navbar", () => {
  beforeEach(() => {
    mockRefresh.mockClear();
    document.cookie = "";
  });

  test("7: в навбаре видна кнопка смены языка (RU или EN)", () => {
    render(
      <NextIntlClientProvider locale="ru" messages={ru}>
        <Navbar />
      </NextIntlClientProvider>
    );
    const langBtn = screen.getByRole("button", { name: /english/i });
    expect(langBtn).toHaveTextContent("EN");
  });

  test("8: после клика и смены локали текст кнопки меняется EN → RU", async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <NextIntlClientProvider locale="ru" messages={ru}>
        <Navbar />
      </NextIntlClientProvider>
    );
    expect(screen.getByRole("button", { name: /english/i })).toHaveTextContent(
      "EN"
    );
    await user.click(screen.getByRole("button", { name: /english/i }));
    expect(mockRefresh).toHaveBeenCalled();
    rerender(
      <NextIntlClientProvider locale="en" messages={en}>
        <Navbar />
      </NextIntlClientProvider>
    );
    expect(screen.getByRole("button", { name: /русский/i })).toHaveTextContent(
      "RU"
    );
  });

  test("9: язык по умолчанию ru — заголовок календаря по-русски", async () => {
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
