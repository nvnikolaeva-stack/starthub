const WD_SHORT = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];

const MONTHS_GEN = [
  "",
  "января",
  "февраля",
  "марта",
  "апреля",
  "мая",
  "июня",
  "июля",
  "августа",
  "сентября",
  "октября",
  "ноября",
  "декабря",
];

/** Локальная дата из YYYY-MM-DD без сдвига из-за UTC */
export function parseISODate(s: string): Date {
  const [y, m, d] = s.slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** Календарный день в локальном поясе — только год-месяц-день (не UTC.toISOString) */
export function dayKey(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function weekdayShort(d: Date): string {
  return WD_SHORT[d.getDay()];
}

export function isWeekend(d: Date): boolean {
  const day = d.getDay();
  return day === 0 || day === 6;
}

export function formatDayMonth(d: Date): string {
  return `${d.getDate()} ${MONTHS_GEN[d.getMonth() + 1]}`;
}

export function formatDayMonthYear(d: Date): string {
  return `${d.getDate()} ${MONTHS_GEN[d.getMonth() + 1]} ${d.getFullYear()}`;
}

/** Даты карточки без дней недели — дни недели рендерятся отдельно с подсветкой Сб/Вс */
export function formatEventCardDateOnly(
  startIso: string,
  endIso: string | null
): string {
  const a = parseISODate(startIso);
  const b = endIso ? parseISODate(endIso) : a;
  const same = startIso.slice(0, 10) === (endIso || startIso).slice(0, 10);
  if (same) {
    return formatDayMonthYear(a);
  }
  if (a.getFullYear() === b.getFullYear()) {
    if (a.getMonth() === b.getMonth()) {
      return `${a.getDate()} — ${formatDayMonthYear(b)}`;
    }
    return `${formatDayMonth(a)} — ${formatDayMonthYear(b)}`;
  }
  return `${formatDayMonthYear(a)} — ${formatDayMonthYear(b)}`;
}

export function formatEventRange(
  startIso: string,
  endIso: string | null
): string {
  const a = parseISODate(startIso);
  const b = endIso ? parseISODate(endIso) : a;
  const same = startIso.slice(0, 10) === (endIso || startIso).slice(0, 10);
  if (same) {
    return `${formatDayMonthYear(a)} (${weekdayShort(a)})`;
  }
  const wdA = weekdayShort(a);
  const wdB = weekdayShort(b);
  const days =
    Math.round((b.getTime() - a.getTime()) / (24 * 60 * 60 * 1000)) + 1;
  return `${formatDayMonth(a)} — ${formatDayMonthYear(b)} (${wdA} — ${wdB}, ${days} дн.)`;
}

export function monthTitle(d: Date): string {
  const months = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
  ];
  return `${months[d.getMonth()]} ${d.getFullYear()}`;
}

export function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

export function endOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0);
}

export function addMonths(d: Date, n: number): Date {
  return new Date(d.getFullYear(), d.getMonth() + n, 1);
}

/** Понедельник = первая колонка (0), вернуть дни до первого дня месяца с пн */
export function calendarGridMonth(view: Date): (Date | null)[] {
  const first = startOfMonth(view);
  const last = endOfMonth(view);
  let pad = first.getDay() - 1;
  if (pad < 0) pad = 6;
  const cells: (Date | null)[] = [];
  for (let i = 0; i < pad; i++) cells.push(null);
  for (let day = 1; day <= last.getDate(); day++) {
    cells.push(new Date(view.getFullYear(), view.getMonth(), day));
  }
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}

export function eventOverlapsDay(
  ev: { date_start: string; date_end: string | null },
  day: Date
): boolean {
  const key = dayKey(day);
  const s = ev.date_start.slice(0, 10);
  const e = (ev.date_end || ev.date_start).slice(0, 10);
  return key >= s && key <= e;
}

/** Старт пересекается с календарным месяцем view (любой день месяца) */
export function eventInCalendarMonth(
  ev: { date_start: string; date_end: string | null },
  view: Date
): boolean {
  const first = startOfMonth(view);
  const last = endOfMonth(view);
  const s = ev.date_start.slice(0, 10);
  const e = (ev.date_end || ev.date_start).slice(0, 10);
  const fk = dayKey(first);
  const lk = dayKey(last);
  return !(e < fk || s > lk);
}

const LOCALE_EN = "en-GB";
const LOCALE_RU = "ru-RU";

/** Короткий день недели для карточек (ru — как раньше, en — Intl). */
export function weekdayShortLocalized(d: Date, locale: string): string {
  if (locale === "en") {
    return new Intl.DateTimeFormat(LOCALE_EN, { weekday: "short" }).format(d);
  }
  return weekdayShort(d);
}

/** Только даты карточки (без дня недели в скобках). */
export function formatEventCardDateOnlyLocalized(
  startIso: string,
  endIso: string | null,
  locale: string
): string {
  if (locale !== "en") {
    return formatEventCardDateOnly(startIso, endIso);
  }
  const a = parseISODate(startIso);
  const b = endIso ? parseISODate(endIso) : a;
  const opts: Intl.DateTimeFormatOptions = {
    day: "numeric",
    month: "long",
    year: "numeric",
  };
  const same =
    startIso.slice(0, 10) === (endIso || startIso).slice(0, 10);
  if (same) {
    return new Intl.DateTimeFormat(LOCALE_EN, opts).format(a);
  }
  if (a.getFullYear() === b.getFullYear()) {
    if (a.getMonth() === b.getMonth()) {
      return `${a.getDate()} — ${new Intl.DateTimeFormat(LOCALE_EN, opts).format(b)}`;
    }
    return `${new Intl.DateTimeFormat(LOCALE_EN, { day: "numeric", month: "long" }).format(a)} — ${new Intl.DateTimeFormat(LOCALE_EN, opts).format(b)}`;
  }
  return `${new Intl.DateTimeFormat(LOCALE_EN, opts).format(a)} — ${new Intl.DateTimeFormat(LOCALE_EN, opts).format(b)}`;
}

/** Диапазон с днями недели (как formatEventRange для ru). */
export function formatEventRangeLocalized(
  startIso: string,
  endIso: string | null,
  locale: string
): string {
  if (locale !== "en") {
    return formatEventRange(startIso, endIso);
  }
  const a = parseISODate(startIso);
  const b = endIso ? parseISODate(endIso) : a;
  const same =
    startIso.slice(0, 10) === (endIso || startIso).slice(0, 10);
  const wd = (x: Date) => weekdayShortLocalized(x, "en");
  if (same) {
    return `${new Intl.DateTimeFormat(LOCALE_EN, { day: "numeric", month: "long", year: "numeric" }).format(a)} (${wd(a)})`;
  }
  const days =
    Math.round((b.getTime() - a.getTime()) / (24 * 60 * 60 * 1000)) + 1;
  return `${new Intl.DateTimeFormat(LOCALE_EN, { day: "numeric", month: "long" }).format(a)} — ${new Intl.DateTimeFormat(LOCALE_EN, { day: "numeric", month: "long", year: "numeric" }).format(b)} (${wd(a)} — ${wd(b)}, ${days} d)`;
}

export function formatDayMonthYearLocalized(d: Date, locale: string): string {
  if (locale === "en") {
    return new Intl.DateTimeFormat(LOCALE_EN, {
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(d);
  }
  return formatDayMonthYear(d);
}

export function formatDayMonthLocalized(d: Date, locale: string): string {
  if (locale === "en") {
    return new Intl.DateTimeFormat(LOCALE_EN, {
      day: "numeric",
      month: "long",
    }).format(d);
  }
  return formatDayMonth(d);
}

/** Короткое название месяца (для блока даты на карточке). */
export function monthShortLabelLocalized(d: Date, locale: string): string {
  if (locale === "en") {
    return new Intl.DateTimeFormat("en-GB", { month: "short" }).format(d);
  }
  return MONTHS_GEN[d.getMonth() + 1].slice(0, 3);
}

/** Короткая дата для строки списка: «29 мар» / «29 Mar». */
export function formatCompactDayMonthLocalized(d: Date, locale: string): string {
  if (locale === "en") {
    return new Intl.DateTimeFormat(LOCALE_EN, {
      day: "numeric",
      month: "short",
    }).format(d);
  }
  return `${d.getDate()} ${MONTHS_GEN[d.getMonth() + 1].slice(0, 3)}`;
}
