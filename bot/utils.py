from __future__ import annotations

import html
import logging
import re
from datetime import date, datetime
from typing import Any

import dateparser

log = logging.getLogger(__name__)

WD_RU = [
    "понедельник",
    "вторник",
    "среда",
    "четверг",
    "пятница",
    "суббота",
    "воскресенье",
]

MONTH_GEN_RU = [
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
]


RU_SPORT_TITLE = {
    "swimming": "🏊 Плавание",
    "running": "🏃 Бег",
    "cycling": "🚴 Велогонка",
    "triathlon": "🔱 Триатлон",
    "other": "🏅 Прочее",
}

_SPORT_TITLE_KEY = {
    "swimming": "sport_swimming",
    "running": "sport_running",
    "cycling": "sport_cycling",
    "triathlon": "sport_triathlon",
    "other": "sport_other",
}


def sport_title_line(sport_type: str, locale: str) -> str:
    from translations import t

    k = _SPORT_TITLE_KEY.get(sport_type)
    if k:
        return t(locale, k)
    return sport_type

LIST_SPORT_EMOJI = {
    "swimming": "🏊",
    "running": "🏃",
    "cycling": "🚴",
    "triathlon": "🔱",
    "other": "🏅",
}


def sport_line_emoji(sport_type: str) -> str:
    return LIST_SPORT_EMOJI.get(sport_type, "🏁")


def format_date_ru(d: date | str) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return d.strftime("%d.%m.%Y")


def parse_user_date(text: str) -> date | None:
    """
    Парсит дату из пользовательского ввода.
    ПРИОРИТЕТ: сначала ручной парсинг (regex), потом dateparser.
    """
    raw = (text or "").strip()
    if not raw:
        return None
    today = date.today()

    match = re.match(r"^(\d{1,2})[./\-\s]+(\d{1,2})[./\-\s]+(\d{4})$", raw)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        try:
            return date(year, month, day)
        except ValueError:
            return None

    match = re.match(r"^(\d{1,2})[./\-\s]+(\d{1,2})[./\-\s]+(\d{2})$", raw)
    if match:
        day, month, year_short = int(match.group(1)), int(match.group(2)), int(match.group(3))
        year = 2000 + year_short
        try:
            return date(year, month, day)
        except ValueError:
            return None

    match = re.match(r"^(\d{1,2})[./\-\s]+(\d{1,2})$", raw)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        year = today.year
        try:
            return date(year, month, day)
        except ValueError:
            return None

    match = re.match(r"^\d{1,4}$", raw)
    if match:
        num = int(match.group())
        if num > 31:
            return None

    try:
        parsed = dateparser.parse(
            raw,
            languages=["ru", "en"],
            settings={
                "DATE_ORDER": "DMY",
                "PREFER_DATES_FROM": "future",
                "RELATIVE_BASE": datetime.now(),
            },
        )
    except Exception:
        log.exception("dateparser.parse")
        return None
    if parsed is None:
        return None
    if isinstance(parsed, datetime):
        return parsed.date()
    if isinstance(parsed, date):
        return parsed
    return None


def parse_flexible_date(text: str) -> date | None:
    """Обратная совместимость: делегирует в parse_user_date."""
    return parse_user_date(text)


def suggested_year_for_extreme(d: date) -> int:
    """Подсказка года при выходе за допустимый диапазон."""
    today = date.today()
    lo, hi = 2020, today.year + 2
    if d.year < lo:
        return lo
    if d.year > hi:
        return hi
    return d.year


def date_needs_extreme_year_confirm(d: date) -> bool:
    today = date.today()
    return d.year < 2020 or d.year > today.year + 2


def format_date_long_ru(d: date) -> str:
    return f"{d.day} {MONTH_GEN_RU[d.month]} {d.year} ({WD_RU[d.weekday()]})"


EN_MONTH_SHORT = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def format_date_long_display(d: date, locale: str) -> str:
    if locale == "ru":
        return format_date_long_ru(d)
    return f"{d.day} {EN_MONTH_SHORT[d.month - 1]} {d.year}"


def format_date_recognized_prompt(d: date) -> str:
    return f"📅 Распознано: {format_date_long_ru(d)}. Верно?"


def format_date_recognized_prompt_locale(d: date, locale: str) -> str:
    from translations import t

    return t(locale, "recognize_ok", when=format_date_long_display(d, locale))


def format_date_past_confirm_prompt(d: date) -> str:
    """Одно сообщение: распознавание + предупреждение о прошедшей дате."""
    return (
        f"📅 Распознано: {format_date_long_ru(d)}.\n"
        f"⚠️ Эта дата уже прошла.\n"
        f"Всё равно использовать?"
    )


def format_date_past_confirm_prompt_locale(d: date, locale: str) -> str:
    from translations import t

    return t(
        locale,
        "date_past_body",
        when=format_date_long_display(d, locale),
    )


DATE_PROMPT_SHORT = "📅 Когда старт? Укажи дату:"

DATE_UNPARSEABLE = (
    "❌ Не удалось распознать дату. Попробуй так: "
    "15 июня, 03.03.2025 или завтра"
)

DATE_PARSE_HELP = DATE_UNPARSEABLE

DATE_INVALID = "Некорректная дата"

OTHER_SENTINEL = "__OTHER__"


def build_distance_options(all_presets: list[str], selected: list[str]) -> list[str]:
    sel_set = set(selected)
    rem = [x for x in all_presets if x not in sel_set]
    if not all_presets:
        return []
    return rem + [OTHER_SENTINEL]


def distance_option_caption(opt: str, locale: str = "ru") -> str:
    from translations import t

    return t(locale, "distance_other") if opt == OTHER_SENTINEL else (opt[:40] if opt else "")


def format_range_short_dm(ds: date, de: date) -> str:
    return f"{ds.strftime('%d.%m')} — {de.strftime('%d.%m.%Y')}"


def plural_days_ru(n: int) -> str:
    n = int(n)
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} день"
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return f"{n} дня"
    return f"{n} дней"


def plural_days_locale(n: int, locale: str) -> str:
    if locale == "ru":
        return plural_days_ru(n)
    return f"{int(n)} days"


def filter_preset_distances(labels: list[str]) -> list[str]:
    skip = {"other", "прочее", "другое"}
    out: list[str] = []
    for x in labels:
        if str(x).strip().lower() in skip:
            continue
        out.append(x)
    return out


def user_created_by(user: Any, locale: str = "ru") -> str:
    from translations import t

    name = (user.full_name or "").strip() or t(locale, "participant_default")
    un = user.username
    if un:
        return f"{name} (@{un})"
    return f"{name} (tg:{user.id})"


def build_preview_text(data: dict[str, Any], locale: str = "ru") -> str:
    from translations import t

    sport = data.get("sport_type", "")
    sport_title = sport_title_line(str(sport), locale)
    name = html.escape(str(data.get("name", "")))
    ds = data.get("date_start")
    de = data.get("date_end")
    if isinstance(ds, str):
        ds = date.fromisoformat(ds)
    if isinstance(de, str):
        de = date.fromisoformat(de)
    if de:
        dates = f"{format_date_ru(ds)} — {format_date_ru(de)}"
    else:
        dates = format_date_ru(ds)
    loc = html.escape(str(data.get("location", "")))
    dists = data.get("distances") or []
    dist_s = html.escape(", ".join(str(d) for d in dists)) if dists else t(locale, "dash")
    url = html.escape((data.get("url") or "").strip() or t(locale, "dash"))
    extras = data.get("extra_names") or []
    if extras:
        people = html.escape(", ".join(str(x) for x in extras))
    else:
        people = t(locale, "dash")
    notes = html.escape((data.get("notes") or "").strip() or t(locale, "dash"))

    return (
        t(locale, "preview_title")
        + f"{sport_title}\n"
        + f"📌 {name}\n"
        + f"📅 {dates}\n"
        + f"📍 {loc}\n"
        + f"📏 {dist_s}\n"
        + f"🔗 {url}\n"
        + f"👥 {people}\n"
        + f"📝 {notes}"
    )


def generic_api_error(locale: str = "ru") -> str:
    from translations import t

    return t(locale, "generic_error")


def api_error_user(locale: str = "ru") -> str:
    from translations import t

    return t(locale, "api_error_user")
