/**
 * @jest-environment jsdom
 */
import type { ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { Calendar } from "@/components/Calendar";
import type { Event } from "@/lib/types";
import ru from "@/messages/ru.json";

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

jest.mock("@/hooks/use-is-mobile", () => ({
  useIsMobile: () => false,
}));

function renderCalendar(ui: ReactElement) {
  return render(
    <NextIntlClientProvider locale="ru" messages={ru}>
      {ui}
    </NextIntlClientProvider>
  );
}

function baseEvent(overrides: Partial<Event>): Event {
  return {
    id: "e1",
    name: "Test",
    date_start: "2026-03-29",
    date_end: null,
    location: "Moscow",
    sport_type: "running",
    url: null,
    notes: null,
    created_by: "bot",
    created_at: "2026-01-01T12:00:00",
    ...overrides,
  };
}

describe("Calendar", () => {
  const noop = () => {};
  const noopSelect = () => {};

  test("6: рендерит заголовок месяца и строку дней Пн–Вс", () => {
    const view = new Date(2026, 5, 1);
    const { container } = renderCalendar(
      <Calendar
        view={view}
        onViewChange={noop}
        events={[]}
        showPast
        selectedDayKey={null}
        onSelectDay={noopSelect}
      />
    );
    expect(
      screen.getByRole("heading", { name: "июнь 2026 г." })
    ).toBeInTheDocument();
    const weekHeader = container.querySelector(".mb-1");
    const hdr = weekHeader?.textContent ?? "";
    for (const w of ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]) {
      expect(hdr).toContain(w);
    }
  });

  test("7: mini-pill на дате со стартом (29 марта, локальный день)", () => {
    const view = new Date(2026, 2, 1);
    const events = [baseEvent({})];
    renderCalendar(
      <Calendar
        view={view}
        onViewChange={noop}
        events={events}
        showPast
        selectedDayKey={null}
        onSelectDay={noopSelect}
      />
    );
    expect(screen.getByTestId("calendar-event-pill-e1")).toBeInTheDocument();
  });

  test("7b: многодневный старт — pill на каждый день диапазона", () => {
    const view = new Date(2026, 5, 1);
    const events = [
      baseEvent({
        id: "multi",
        name: "Long",
        date_start: "2026-06-15",
        date_end: "2026-06-17",
      }),
    ];
    renderCalendar(
      <Calendar
        view={view}
        onViewChange={noop}
        events={events}
        showPast
        selectedDayKey={null}
        onSelectDay={noopSelect}
      />
    );
    for (const day of ["2026-06-15", "2026-06-16", "2026-06-17"]) {
      const cell = screen.getByTestId(`calendar-cell-${day}`);
      expect(
        cell.querySelector('[data-testid="calendar-event-pill-multi"]')
      ).toBeTruthy();
    }
  });

  test("8: нет pill на пустую дату при старте на 29-м", () => {
    const view = new Date(2026, 2, 1);
    const events = [baseEvent({})];
    renderCalendar(
      <Calendar
        view={view}
        onViewChange={noop}
        events={events}
        showPast
        selectedDayKey={null}
        onSelectDay={noopSelect}
      />
    );
    const cell = screen.getByTestId("calendar-cell-2026-03-10");
    expect(cell.querySelector('[data-testid^="calendar-event-pill"]')).toBeNull();
  });

  test("9: выходные с фоном surface-tinted (суббота)", () => {
    const view = new Date(2026, 2, 1);
    renderCalendar(
      <Calendar
        view={view}
        onViewChange={noop}
        events={[]}
        showPast
        selectedDayKey={null}
        onSelectDay={noopSelect}
      />
    );
    const sat = screen.getByTestId("calendar-cell-2026-03-07");
    expect(sat.className).toMatch(/surface-tinted/);
  });

  test("10: смена месяца по стрелке", async () => {
    const user = userEvent.setup();
    const view = new Date(2026, 2, 1);
    const onViewChange = jest.fn();
    renderCalendar(
      <Calendar
        view={view}
        onViewChange={onViewChange}
        events={[]}
        showPast
        selectedDayKey={null}
        onSelectDay={noopSelect}
      />
    );
    await user.click(screen.getByRole("button", { name: "Следующий месяц" }));
    expect(onViewChange).toHaveBeenCalled();
    const next = onViewChange.mock.calls[0][0] as Date;
    expect(next.getFullYear()).toBe(2026);
    expect(next.getMonth()).toBe(3);
  });

  test("11: сегодняшний день с рамкой primary", () => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date(2026, 2, 15, 12, 0, 0));
    const view = new Date(2026, 2, 1);
    renderCalendar(
      <Calendar
        view={view}
        onViewChange={noop}
        events={[]}
        showPast
        selectedDayKey={null}
        onSelectDay={noopSelect}
      />
    );
    const cell = screen.getByTestId("calendar-cell-2026-03-15");
    expect(cell.className).toMatch(/border-\[var\(--color-primary\)\]/);
    jest.useRealTimers();
  });
});
