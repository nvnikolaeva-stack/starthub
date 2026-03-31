/**
 * @jest-environment jsdom
 */
import ru from "@/messages/ru.json";
import en from "@/messages/en.json";

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

/** Собирает «пути» вида a.b.c для всех строковых листьев. */
function leafStringPaths(
  obj: Record<string, unknown>,
  prefix = ""
): Map<string, string> {
  const out = new Map<string, string>();
  for (const [k, v] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${k}` : k;
    if (isPlainObject(v)) {
      const nested = leafStringPaths(v, path);
      nested.forEach((val, p) => out.set(p, val));
    } else if (typeof v === "string") {
      out.set(path, v);
    }
  }
  return out;
}

/** Не участвуют в доле «должны отличаться» (одинаковый бренд, числа и т.п.). */
function shouldExcludeFromComparable(path: string, ruVal: string, enVal: string): boolean {
  if (path === "nav.brand" || path.endsWith(".brand")) return true;
  if (ruVal.trim().length === 0 || enVal.trim().length === 0) return true;
  if (/^[\d\s.\-–—/:]*$/.test(ruVal) && /^[\d\s.\-–—/:]*$/.test(enVal)) return true;
  return false;
}

describe("i18n messages", () => {
  test("1: ru.json парсится и содержит обязательные разделы", () => {
    expect(isPlainObject(ru)).toBe(true);
    for (const key of REQUIRED_TOP_KEYS) {
      expect(ru).toHaveProperty(key);
      expect(isPlainObject(ru[key as keyof typeof ru] as unknown)).toBe(true);
    }
  });

  test("2: en.json парсится и содержит обязательные разделы", () => {
    expect(isPlainObject(en)).toBe(true);
    for (const key of REQUIRED_TOP_KEYS) {
      expect(en).toHaveProperty(key);
      expect(isPlainObject(en[key as keyof typeof en] as unknown)).toBe(true);
    }
  });

  test("3: все ключи из ru есть в en", () => {
    const ruPaths = leafStringPaths(ru as unknown as Record<string, unknown>);
    const enPaths = leafStringPaths(en as unknown as Record<string, unknown>);
    const missing: string[] = [];
    for (const path of ruPaths.keys()) {
      if (!enPaths.has(path)) missing.push(path);
    }
    expect(missing).toEqual([]);
  });

  test("4: все ключи из en есть в ru", () => {
    const ruPaths = leafStringPaths(ru as unknown as Record<string, unknown>);
    const enPaths = leafStringPaths(en as unknown as Record<string, unknown>);
    const missing: string[] = [];
    for (const path of enPaths.keys()) {
      if (!ruPaths.has(path)) missing.push(path);
    }
    expect(missing).toEqual([]);
  });

  test("5: в en нет пустых строк", () => {
    const enPaths = leafStringPaths(en as unknown as Record<string, unknown>);
    const empty: string[] = [];
    for (const [path, val] of enPaths) {
      if (typeof val === "string" && val.trim() === "") empty.push(path);
    }
    expect(empty).toEqual([]);
  });

  test("6: английские строки в основном не копипаста с русского (≥80% отличаются)", () => {
    const ruPaths = leafStringPaths(ru as unknown as Record<string, unknown>);
    const enPaths = leafStringPaths(en as unknown as Record<string, unknown>);
    let comparable = 0;
    let same = 0;
    for (const [path, ruVal] of ruPaths) {
      const enVal = enPaths.get(path);
      if (enVal === undefined) continue;
      if (shouldExcludeFromComparable(path, ruVal, enVal)) continue;
      comparable += 1;
      if (ruVal === enVal) same += 1;
    }
    expect(comparable).toBeGreaterThan(10);
    const diffRatio = (comparable - same) / comparable;
    expect(diffRatio).toBeGreaterThanOrEqual(0.8);
  });
});
