/**
 * @jest-environment jsdom
 */
import type { ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { EventCard } from "@/components/EventCard";
import type { Event, Registration } from "@/lib/types";
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

function renderCard(ui: ReactElement) {
  return render(
    <NextIntlClientProvider locale="ru" messages={ru}>
      {ui}
    </NextIntlClientProvider>
  );
}

function ev(partial: Partial<Event>): Event {
  return {
    id: "1",
    name: "Ironstar",
    date_start: "2026-06-15",
    date_end: "2026-06-17",
    location: "Сочи",
    sport_type: "triathlon",
    url: "https://example.com",
    notes: "Заметка",
    created_by: "u",
    created_at: "2026-01-01T00:00:00",
    ...partial,
  };
}

describe("EventCard", () => {
  test("12: название, локация, дистанция и участники на экране", () => {
    const regs: Registration[] = [
      {
        id: "r1",
        event_id: "1",
        participant_id: "p1",
        distances: ["Olympic"],
        result_time: "2:15:00",
        result_place: "10/100",
        participant_display_name: "Иван",
      },
    ];
    renderCard(<EventCard event={ev({ registrations: regs })} />);
    expect(screen.getByText("Ironstar")).toBeInTheDocument();
    expect(screen.getByText(/Сочи/)).toBeInTheDocument();
    expect(screen.getByText(/Olympic/)).toBeInTheDocument();
    expect(screen.getByText(/Иван/)).toBeInTheDocument();
  });

  test("13: без участников — текст «нет участников»", () => {
    renderCard(<EventCard event={ev({ registrations: undefined })} />);
    expect(screen.getByTestId("event-card-participants")).toHaveTextContent(
      "нет участников"
    );
  });

  test("14: многодневный старт — в блоке даты показан день начала", () => {
    renderCard(<EventCard event={ev({})} />);
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText(/июн/i)).toBeInTheDocument();
  });

  test("15: прошедший старт — пониженная непрозрачность", () => {
    const { container } = renderCard(
      <EventCard
        event={ev({
          date_start: "2020-01-01",
          date_end: "2020-01-01",
        })}
      />
    );
    const card = container.querySelector(".opacity-50");
    expect(card).toBeInTheDocument();
    expect(screen.getByText("завершён")).toBeInTheDocument();
  });
});
