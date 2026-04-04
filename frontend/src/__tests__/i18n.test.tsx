/**
 * @jest-environment jsdom
 */
import ru from "@/messages/ru.json";

const REQUIRED_TOP_KEYS = [
  "nav",
  "calendar",
  "filters",
  "event",
  "addForm",
  "stats",
  "join",
  "common",
] as const;

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

describe("i18n messages", () => {
  test("ru.json парсится и содержит обязательные разделы", () => {
    expect(isPlainObject(ru)).toBe(true);
    for (const key of REQUIRED_TOP_KEYS) {
      expect(ru).toHaveProperty(key);
      expect(isPlainObject(ru[key as keyof typeof ru] as unknown)).toBe(true);
    }
  });
});
