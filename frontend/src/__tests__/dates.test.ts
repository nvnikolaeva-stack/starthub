import { dayKey, eventOverlapsDay, parseISODate } from "@/lib/dates";

describe("dates (локальный календарь без UTC-сдвига)", () => {
  test("dayKey для локальной даты совпадает с YYYY-MM-DD ячейки", () => {
    const d = new Date(2026, 2, 29);
    expect(dayKey(d)).toBe("2026-03-29");
  });

  test("parseISODate не сдвигает день", () => {
    const d = parseISODate("2026-03-29");
    expect(d.getFullYear()).toBe(2026);
    expect(d.getMonth()).toBe(2);
    expect(d.getDate()).toBe(29);
  });

  test("eventOverlapsDay: старт 29-го попадает в ячейку 29 марта", () => {
    const ev = {
      date_start: "2026-03-29",
      date_end: null,
    };
    const cell = new Date(2026, 2, 29);
    expect(eventOverlapsDay(ev, cell)).toBe(true);
  });

  test("eventOverlapsDay: многодневный диапазон покрывает середину", () => {
    const ev = { date_start: "2026-06-15", date_end: "2026-06-17" };
    expect(eventOverlapsDay(ev, new Date(2026, 5, 16))).toBe(true);
  });
});
