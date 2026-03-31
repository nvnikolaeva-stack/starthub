/**
 * @jest-environment jsdom
 */
import type { ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { FilterBar } from "@/components/FilterBar";
import { defaultCalendarFilters } from "@/lib/calendarFilters";
import ru from "@/messages/ru.json";

function renderFilterBar(ui: ReactElement) {
  return render(
    <NextIntlClientProvider locale="ru" messages={ru}>
      {ui}
    </NextIntlClientProvider>
  );
}

const viewJune = new Date(2026, 5, 1);

const baseProps = {
  filters: defaultCalendarFilters(),
  onFiltersChange: () => {},
  viewMonth: viewJune,
  onViewMonthChange: () => {},
  distanceOptions: ["5K", "10K"],
  locations: ["Москва"],
  onResetAll: () => {},
};

describe("FilterBar", () => {
  test("16: в селекте спорта есть виды спорта", () => {
    renderFilterBar(<FilterBar {...baseProps} />);
    const sport = screen.getByLabelText("Спорт");
    expect(sport).toBeInTheDocument();
    const opts = [...(sport as HTMLSelectElement).options].map((o) => o.text);
    expect(opts.some((x) => /Плавание/.test(x))).toBe(true);
    expect(opts.some((x) => /Бег/.test(x))).toBe(true);
  });

  test("17: смена спорта вызывает onFiltersChange с running", async () => {
    const user = userEvent.setup();
    const onFiltersChange = jest.fn();
    renderFilterBar(
      <FilterBar {...baseProps} onFiltersChange={onFiltersChange} />
    );
    await user.selectOptions(screen.getByLabelText("Спорт"), "running");
    expect(onFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({ sport: "running" })
    );
  });

  test("18: выбранный спорт в селекте", () => {
    renderFilterBar(
      <FilterBar
        {...baseProps}
        filters={{ ...defaultCalendarFilters(), sport: "running" }}
      />
    );
    expect(screen.getByLabelText("Спорт")).toHaveValue("running");
  });
});
