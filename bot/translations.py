"""Переводы бота RU/EN. Язык по умолчанию из Telegram; /lang фиксирует выбор в памяти."""

from __future__ import annotations

from typing import Any

USER_LANG: dict[int, str] = {}

RU: dict[str, str] = {
    "welcome": "Привет! Я #алкардио — бот для отслеживания спортивных стартов.",
    "help_full": (
        "#алкардио — бот для отслеживания спортивных стартов.\n\n"
        "📋 Управление стартами:\n"
        "/add — Добавить новый старт\n"
        "/edit — Редактировать старт\n"
        "/delete — Удалить старт\n\n"
        "📅 Просмотр:\n"
        "/list — Ближайшие старты\n"
        "/join — Присоединиться к старту\n\n"
        "🏅 Результаты и статистика:\n"
        "/result — Внести результат после старта\n"
        "/stats — Статистика (личная и командная)\n\n"
        "📲 Экспорт:\n"
        "/ical — Скачать .ics файл для календаря\n\n"
        "⏰ Напоминания:\n"
        "Бот автоматически напоминает в каждой группе за день до старта.\n"
        "Просто добавь бота в группу — он начнёт работать!\n\n"
        "🌐 Язык:\n"
        "/lang — Выбрать русский или English\n\n"
        "💡 В личке ты видишь старты из всех своих групп.\n"
        "В группе — только старты этой группы.\n\n"
        "⚙️ Отладка:\n"
        "/chatid — Узнать ID группового чата\n\n"
        "💡 Также можно написать «добавь старт» вместо /add"
    ),
    "lang_choose": "🌐 Выберите язык / Choose language:",
    "lang_set_ru": "Язык: русский",
    "lang_set_en": "Language: English",
    "participant_default": "Участник",
    "event_default": "Старт",
    "event_word": "старт",
    "generic_error": "Что-то пошло не так, попробуй позже",
    "api_error_user": "⚠️ Что-то пошло не так. Попробуй позже.",
    "date_prompt_short": "📅 Когда старт? Укажи дату:",
    "date_unparseable": (
        "❌ Не удалось распознать дату. Попробуй так: "
        "15 июня, 03.03.2025 или завтра"
    ),
    "dash": "—",
    "preview_title": "📋 <b>Новый старт:</b>\n\n",
    "distance_other": "+ своя",
    "extras_empty": "👥 Участники:\n(пока никого)",
    "extras_header": "👥 Участники:\n",
    "recognize_ok": "📅 Распознано: {when}. Верно?",
    "date_past_body": (
        "📅 Распознано: {when}.\n"
        "⚠️ Эта дата уже прошла.\n"
        "Всё равно использовать?"
    ),
    "year_doubt": "⚠️ Год {year} — это точно? Может быть, вы имели в виду {hint}?",
    "year_far": (
        "⚠️ Распознан {year} год — это очень далеко. "
        "Проверь ввод и попробуй ещё раз."
    ),
    "nav_back": "◀️ Назад",
    "nav_cancel": "❌ Отмена",
    "cancel_break_yes": "Да, прервать",
    "cancel_break_no": "Нет, продолжить",
    "cancel_flow_prompt": "Прервать заполнение? Все данные будут потеряны.",
    "canceled": "Отменено.",
    "yes": "Да",
    "no": "Нет",
    "skip": "Пропустить",
    "save": "✅ Сохранить",
    "edit": "✏️ Редактировать",
    "done_check": "Готово ✓",
    "done_plain": "Готово",
    "next_keep": "▶️ Далее (оставить как есть)",
    "sport_swimming": "🏊 Плавание",
    "sport_running": "🏃 Бег",
    "sport_cycling": "🚴 Велогонка",
    "sport_triathlon": "🔱 Триатлон",
    "sport_other": "Прочее",
    "edit_back_preview": "◀️ Назад к превью",
    "field_sport": "Вид спорта",
    "field_name": "Название",
    "field_date": "Дата",
    "field_location": "Локация",
    "field_distance": "Дистанция",
    "field_url": "Ссылка",
    "field_notes": "Заметки",
    "field_participants_btn": "👥 Участники",
    "date_past_ok": "✅ Да, использовать",
    "date_past_redo": "✏️ Ввести другую дату",
    "year_ok_yes": "Да, верно",
    "year_ok_no": "Нет, ввести заново",
    "date_confirm_yes": "✅ Да",
    "date_confirm_redo": "✏️ Ввести заново",
    "multi_enter_end_date": "Ввести дату окончания",
    "duration_confirm_yes": "✅ Да",
    "duration_confirm_edit": "✏️ Изменить",
    "extra_add_participant": "➕ Добавить участника",
    "extra_back_manage": "◀️ Назад",
    "list_period_weekend": "Выходные",
    "list_period_month": "Месяц",
    "list_period_3months": "3 месяца",
    "list_period_all": "Все",
    "list_all_types": "Все виды",
    "list_all_types_sel": "✓ Все виды",
    "join_cancel": "Отмена",
    "join_cancel_x": "❌ Отмена",
    "edit_back_list": "◀️ Назад к списку",
    "edit_dist_keep": "Оставить как есть",
    "delete_yes": "🗑 Да, удалить",
    "delete_no": "◀️ Нет, отмена",
    "stats_mine": "Моя статистика",
    "stats_team": "Статистика команды",
    "result_redo": "✏️ Изменить",
    "group_chat_fallback": "Чат {id}",
    "choose_sport": "Выбери вид спорта:",
    "enter_name": "Введи название старта:",
    "similar_join_btn": "📌 {name} — присоед.",
    "similar_create_new": "Нет, создать новый старт",
    "similar_title_name": "📌 Похожие старты:",
    "similar_title_date": "📅 На эту дату уже есть старты:",
    "similar_footer": "Хотите присоединиться к одному из них?",
    "similar_participants_n": "{n} уч.",
    "dup409_join": "➡️ Присоединиться к этому старту",
    "dup409_force": "Всё равно создать дубликат",
    "dup409_prompt": (
        "⚠️ Старт с таким названием и датой уже существует. "
        "Присоединиться к существующему или создать дубликат?"
    ),
    "current_value_prompt": "Текущее значение: {value}. Введи новое или нажми «Далее» чтобы оставить.",
    "enter_location": "Город / Локация:",
    "choose_distance": "Выбери дистанцию:",
    "enter_distance_comma": "Введи дистанцию (можно несколько через запятую):",
    "pick_target_group": "Для какой группы создаём старт?",
    "add_private_only": (
        'Добавление стартов доступно только в личных сообщениях: '
        '<a href="https://t.me/{bot}">написать боту</a>'
    ),
    "first_step": "Это первый шаг",
    "enter_end_date_cap": "Введи дату окончания (не больше чем на 7 дней после начала):",
    "multi_day_ask": "Старт длится несколько дней?",
    "how_many_days": "Сколько дней длится старт?",
    "enter_link": "Ссылка на событие (или «Пропустить»):",
    "extra_ask": "Добавить ещё участников? (кроме тебя)",
    "notes_current": "Текущее значение заметок: {value}. Введи новое или «Пропустить».",
    "need_name_first": "Сначала введи название",
    "need_location_first": "Сначала введи локацию",
    "sport_updated": "Вид спорта обновлён.",
    "sport_chosen": "Вид спорта выбран.",
    "error_generic": "Ошибка",
    "one_day_goto_loc": "Один день — переходим к локации.",
    "enter_end_date_free": "Введи дату окончания (любой формат, не больше чем на 7 дней после начала):",
    "reply_with_date": "Напиши дату ответом на это сообщение:",
    "goto_location": "Переходим к локации.",
    "end_before_start": "Дата окончания не раньше даты начала. Введи снова:",
    "end_max_week": "Не больше 7 дней после начала. Введи снова:",
    "session_stale_add": "Сессия устарела, начни с /add",
    "start_with_add": "Начни с команды /add.",
    "pick_error": "Ошибка выбора",
    "ok_type_distance": "Ок, введи дистанцию текстом.",
    "comma_dist_hint": "Можно несколько через запятую:",
    "pick_distances_first": "Сначала выбери дистанции",
    "dist_saved": "Дистанции сохранены.",
    "dist_added_line": "✅ {name} добавлена. Выбери ещё или нажми Готово:",
    "dist_added_short": "✅ Добавлено. Выбери ещё или нажми Готово:",
    "enter_participant_name": "Введи имя участника:",
    "enter_notes": "Заметки (или «Пропустить»):",
    "participant_added_more": "Участник добавлен. Добавить ещё?",
    "remove_confirm": "Убрать «{name}»?",
    "event_saved": "✅ Старт сохранён!",
    "what_to_change": "Что изменить?",
    "current_sport_pick": "Текущий вид спорта: <b>{cur}</b>\nВыбери вид спорта:",
    "current_name_enter": "Текущее название: <b>{nm}</b>\nВведи новое название:",
    "current_date_enter": "Текущая дата: <b>{d}</b>\n{prompt}",
    "current_dists": "Текущие дистанции: <b>{dists}</b>",
    "current_url_enter": "Текущая ссылка: <b>{cur}</b>\nНовая ссылка (или «Пропустить»):",
    "url_not_set": "не указана",
    "current_notes_enter": "Текущие заметки: <b>{cur}</b>\nНовые заметки (или «Пропустить»):",
    "notes_not_set": "не указаны",
    "duration_confirm_line": "📅 {rng} ({days}). Верно?",
    "extra_add_more_btn": "Добавить ещё",
    "upcoming_title": "<b>Ближайшие старты</b>\n\n",
    "no_events_filter": "Пока нет стартов по выбранным фильтрам.",
    "people_none_short": "👥 пока никого",
    "list_api_error": "Что-то пошло не так, попробуй позже",
    "join_choose_dist": "Выбери дистанцию:",
    "join_enter_dist": "Введи дистанцию (можно несколько через запятую):",
    "need_one_distance": "Нужно указать хотя бы одну дистанцию.",
    "already_joined": "Ты уже записан на этот старт",
    "joined_ok": "✅ Ты записан на {name}!",
    "no_upcoming": "Сейчас нет ближайших стартов.",
    "join_load_fail": "Не удалось загрузить старт",
    "join_ok_type_dist": "Ок, введи дистанцию текстом.",
    "join_pick_header": "📋 Выбери старт:",
    "join_already_registered_dists": (
        "✅ Ты уже записан на этот старт! Твои дистанции: {dists}"
    ),
    "join_dist_added_pick": (
        "✅ {name} добавлена. Выбери ещё дистанцию или нажми Готово:"
    ),
    "join_dist_added_more": (
        "✅ Добавлено. Выбери ещё дистанцию или нажми Готово:"
    ),
    "delete_no_events": "Нет ближайших стартов.",
    "delete_which": "Какой старт удалить?",
    "delete_confirm": (
        "Удалить <b>{title}</b>?\n"
        "Это действие нельзя отменить."
    ),
    "delete_warn": (
        "⚠️ Удалить старт «{title}»?\n"
        "👥 Записей на старт: {count}\n"
        "Это действие нельзя отменить."
    ),
    "event_deleted": "✅ Старт удалён.",
    "delete_canceled": "Удаление отменено.",
    "edit_no_events": "Нет ближайших стартов для редактирования.",
    "edit_no_events_short": "Нет ближайших стартов.",
    "enter_new_name": "Введи новое название:",
    "new_location": "Новая локация:",
    "new_url": "Новая ссылка (или отправь «-» чтобы убрать):",
    "new_notes": "Новые заметки (или «-» чтобы очистить):",
    "what_change": "Что изменить?",
    "join_first": "Запись на старт не найдена — сначала /join.",
    "pick_your_dist": "Выбери дистанции (свою запись):",
    "enter_dists_comma": "Введи дистанции текстом (через запятую):",
    "comma_values": "Можно несколько значений:",
    "service_down": "Сервис недоступен",
    "update_dists_ask": "Обновить дистанции?",
    "reg_not_found": "Запись не найдена.",
    "pick_new_dists": "Выбери новые дистанции:",
    "enter_dists_text": "Введи дистанции текстом:",
    "comma_sep": "Через запятую:",
    "check_input": "Проверь ввод и попробуй ещё раз.",
    "enter_dist_text": "Введи дистанцию текстом:",
    "need_one_dist": "Нужна хотя бы одна дистанция",
    "edit_which_event": "📋 Какой старт редактировать?",
    "edit_card_header": "📋 <b>Старт</b>\n\n",
    "edit_regs_more": "\n… и ещё {n}",
    "session_stale_edit": "Сессия устарела. Начни с /edit",
    "edit_new_date_label": "📅 Новая дата начала:",
    "edit_sport_dist_warning": (
        "⚠️ Выбранные дистанции могут не подходить для нового вида спорта. "
        "Обновить дистанции?"
    ),
    "edit_dist_pick_done": "✅ {name} добавлена. Выбери ещё или Готово:",
    "edit_dist_added_flow": "✅ Добавлено. Выбери ещё или нажми Готово:",
    "stats_empty": "У тебя пока нет стартов. Добавь первый через /add!",
    "stats_header": "📊 Статистика: {who}",
    "stats_events_count": "🏁 Стартов: {n}",
    "stats_by_sport": "По видам спорта:",
    "stats_popular": "Популярные виды спорта:",
    "stats_which_prompt": "📊 Какую статистику показать?",
    "stats_team_header_line": "📊 Статистика команды",
    "stats_team_total_events": "🏁 Всего стартов: {n}",
    "stats_team_total_people": "👥 Участников: {n}",
    "stats_team_most_active": "🏆 Самый активный: {name} ({count} стартов)",
    "stats_popular_locations": "📍 Популярные локации:",
    "stats_you_anon": "ты",
    "stats_personal_header": "🏅 Личные рекорды:",
    "stats_places_header": "📍 Занятые места:",
    "testreminder_ok": (
        "✅ Проверка напоминаний выполнена. "
        "Сообщения уйдут во все зарегистрированные группы."
    ),
    "chatid_group_only": (
        "Эта команда работает только в групповых чатах. "
        "Добавь меня в группу и напиши /chatid там."
    ),
    "result_no_past": "У тебя нет завершённых стартов.",
    "result_pick_event": "Выбери старт для результата:",
    "result_reg_missing": "Запись не найдена",
    "result_which_distance": "Для какой дистанции вносим результат?",
    "result_time_prompt": "Какое время на финише? (например 2:15:30 или 1ч 45мин)",
    "result_time_short": "Какое время на финише?",
    "result_bad_pick": "Неверный выбор",
    "result_session_error": "Ошибка сессии",
    "result_place_prompt": "🥇 Какое место? (например 15/120)",
    "result_block": (
        "🏅 <b>Результат:</b>\n"
        "📌 {name} — {dist}\n"
        "⏱ {time}\n"
        "🥇 {place}"
    ),
    "result_saved_ok": "✅ Результат сохранён! 🎉",
    "result_header_dist": "🏅 {name} — {dist}\n\n",
    "ical_all_my": "📅 Все мои старты",
    "ical_caption": (
        "📅 Файл для Google Calendar / Apple Calendar. "
        "Открой его, чтобы добавить в свой календарь."
    ),
    "ical_event_url": "🔗 Ссылка на событие: {url}",
    "ical_all_caption": "📅 Все твои будущие старты. Открой в календаре.",
    "ical_pick": "Выбери старт для календаря:",
    "ical_uploading": "Загружаю файл…",
    "ical_open_hint": "Открой его, чтобы добавить в свой календарь.",
    "ical_all_building": "Собираю все твои старты…",
    "ical_no_profile": "Профиль не найден. Запишись на старты через /join.",
    "reminder_tomorrow": "🏁 Завтра старт!\n\n",
    "reminder_people": "👥 Стартуют:\n",
    "reminder_no_reg": "• (пока никто не записан)",
    "reminder_luck": "Удачи! 💪",
    "reminder_result_intro": "🏅 Как прошёл {name}?\n\n",
    "reminder_waiting": "👥 Ждём результаты:\n",
    "reminder_use_result": "Используйте /result чтобы добавить время и место 📊",
}

EN: dict[str, str] = {
    "welcome": "Hi! I'm #alkardio — a bot for tracking sports events.",
    "help_full": (
        "#alkardio — track your team's race calendar.\n\n"
        "📋 Events:\n"
        "/add — Add a new event\n"
        "/edit — Edit an event\n"
        "/delete — Delete an event\n\n"
        "📅 Browse:\n"
        "/list — Upcoming events\n"
        "/join — Join an event\n\n"
        "🏅 Results & stats:\n"
        "/result — Log your result after a race\n"
        "/stats — Personal and team stats\n\n"
        "📲 Export:\n"
        "/ical — Download an .ics file\n\n"
        "⏰ Reminders:\n"
        "The bot sends group reminders one day before each event.\n"
        "Add the bot to a group — it starts working automatically.\n\n"
        "🌐 Language:\n"
        "/lang — Russian or English\n\n"
        "💡 In private chat you see events from all your groups.\n"
        "In a group — only that group's events.\n\n"
        "⚙️ Debug:\n"
        "/chatid — Get the group chat ID\n\n"
        "💡 You can also text “add” instead of /add"
    ),
    "lang_choose": "🌐 Выберите язык / Choose language:",
    "lang_set_ru": "Язык: русский",
    "lang_set_en": "Language: English",
    "participant_default": "Participant",
    "event_default": "Event",
    "event_word": "event",
    "generic_error": "Something went wrong. Try again later.",
    "api_error_user": "⚠️ Something went wrong. Try again later.",
    "date_prompt_short": "📅 When is the event? Enter the date:",
    "date_unparseable": (
        "❌ Could not parse the date. Try e.g. "
        "June 15, 03/15/2025 or tomorrow"
    ),
    "dash": "—",
    "preview_title": "📋 <b>New event:</b>\n\n",
    "distance_other": "+ custom",
    "extras_empty": "👥 Participants:\n(none yet)",
    "extras_header": "👥 Participants:\n",
    "recognize_ok": "📅 Recognized: {when}. Correct?",
    "date_past_body": (
        "📅 Recognized: {when}.\n"
        "⚠️ This date is in the past.\n"
        "Use it anyway?"
    ),
    "year_doubt": "⚠️ Year {year} — is that right? Did you mean {hint}?",
    "year_far": (
        "⚠️ Year {year} looks too far ahead. "
        "Check your input and try again."
    ),
    "nav_back": "◀️ Back",
    "nav_cancel": "❌ Cancel",
    "cancel_break_yes": "Yes, abort",
    "cancel_break_no": "No, continue",
    "cancel_flow_prompt": "Abort? All entered data will be lost.",
    "canceled": "Canceled.",
    "yes": "Yes",
    "no": "No",
    "skip": "Skip",
    "save": "✅ Save",
    "edit": "✏️ Edit",
    "done_check": "Done ✓",
    "done_plain": "Done",
    "next_keep": "▶️ Next (keep current)",
    "sport_swimming": "🏊 Swimming",
    "sport_running": "🏃 Running",
    "sport_cycling": "🚴 Cycling",
    "sport_triathlon": "🔱 Triathlon",
    "sport_other": "Other",
    "edit_back_preview": "◀️ Back to preview",
    "field_sport": "Sport type",
    "field_name": "Name",
    "field_date": "Date",
    "field_location": "Location",
    "field_distance": "Distance",
    "field_url": "Link",
    "field_notes": "Notes",
    "field_participants_btn": "👥 Participants",
    "date_past_ok": "✅ Yes, use it",
    "date_past_redo": "✏️ Enter another date",
    "year_ok_yes": "Yes, correct",
    "year_ok_no": "No, re-enter",
    "date_confirm_yes": "✅ Yes",
    "date_confirm_redo": "✏️ Re-enter",
    "multi_enter_end_date": "Enter end date",
    "duration_confirm_yes": "✅ Yes",
    "duration_confirm_edit": "✏️ Change",
    "extra_add_participant": "➕ Add participant",
    "extra_back_manage": "◀️ Back",
    "list_period_weekend": "Weekend",
    "list_period_month": "Month",
    "list_period_3months": "3 months",
    "list_period_all": "All",
    "list_all_types": "All sports",
    "list_all_types_sel": "✓ All sports",
    "join_cancel": "Cancel",
    "join_cancel_x": "❌ Cancel",
    "edit_back_list": "◀️ Back to list",
    "edit_dist_keep": "Keep as is",
    "delete_yes": "🗑 Yes, delete",
    "delete_no": "◀️ No, cancel",
    "stats_mine": "My stats",
    "stats_team": "Team stats",
    "result_redo": "✏️ Edit",
    "group_chat_fallback": "Chat {id}",
    "choose_sport": "Choose sport type:",
    "enter_name": "Enter event name:",
    "similar_join_btn": "📌 {name} — join",
    "similar_create_new": "No, create a new event",
    "similar_title_name": "📌 Similar events:",
    "similar_title_date": "📅 There are already events on this date:",
    "similar_footer": "Do you want to join one of them?",
    "similar_participants_n": "{n} ppl",
    "dup409_join": "➡️ Join the existing event",
    "dup409_force": "Create duplicate anyway",
    "dup409_prompt": (
        "⚠️ An event with this name and date already exists. "
        "Join it or create a duplicate?"
    ),
    "current_value_prompt": "Current: {value}. Enter a new one or tap “Next” to keep it.",
    "enter_location": "City / location:",
    "choose_distance": "Choose distance:",
    "enter_distance_comma": "Enter distance(s), comma-separated:",
    "pick_target_group": "Which group is this event for?",
    "add_private_only": (
        "Adding events works only in private chat: "
        '<a href="https://t.me/{bot}">message the bot</a>'
    ),
    "first_step": "This is the first step",
    "enter_end_date_cap": "Enter end date (at most 7 days after start):",
    "multi_day_ask": "Multi-day event?",
    "how_many_days": "How many days?",
    "enter_link": "Event link (or “Skip”):",
    "extra_ask": "Add more participants (besides you)?",
    "notes_current": "Current notes: {value}. Enter new or “Skip”.",
    "need_name_first": "Enter the name first",
    "need_location_first": "Enter the location first",
    "sport_updated": "Sport type updated.",
    "sport_chosen": "Sport type selected.",
    "error_generic": "Error",
    "one_day_goto_loc": "Single day — going to location.",
    "enter_end_date_free": "Enter end date (any format, max 7 days after start):",
    "reply_with_date": "Reply to this message with the date:",
    "goto_location": "Going to location.",
    "end_before_start": "End date cannot be before start. Try again:",
    "end_max_week": "At most 7 days after start. Try again:",
    "session_stale_add": "Session expired. Start with /add",
    "start_with_add": "Start with /add.",
    "pick_error": "Invalid selection",
    "ok_type_distance": "OK, type the distance as text.",
    "comma_dist_hint": "You can use commas:",
    "pick_distances_first": "Pick at least one distance first",
    "dist_saved": "Distances saved.",
    "dist_added_line": "✅ {name} added. Pick more or tap Done:",
    "dist_added_short": "✅ Added. Pick more or tap Done:",
    "enter_participant_name": "Participant name:",
    "enter_notes": "Notes (or “Skip”):",
    "participant_added_more": "Participant added. Add another?",
    "remove_confirm": "Remove «{name}»?",
    "event_saved": "✅ Event saved!",
    "what_to_change": "What do you want to change?",
    "current_sport_pick": "Current sport: <b>{cur}</b>\nChoose sport:",
    "current_name_enter": "Current name: <b>{nm}</b>\nEnter new name:",
    "current_date_enter": "Current date: <b>{d}</b>\n{prompt}",
    "current_dists": "Current distances: <b>{dists}</b>",
    "current_url_enter": "Current link: <b>{cur}</b>\nNew link (or “Skip”):",
    "url_not_set": "not set",
    "current_notes_enter": "Current notes: <b>{cur}</b>\nNew notes (or “Skip”):",
    "notes_not_set": "none",
    "duration_confirm_line": "📅 {rng} ({days}). Correct?",
    "extra_add_more_btn": "Add more",
    "upcoming_title": "<b>Upcoming events</b>\n\n",
    "no_events_filter": "No events for these filters.",
    "people_none_short": "👥 no one yet",
    "list_api_error": "Something went wrong. Try again later.",
    "join_choose_dist": "Choose distance:",
    "join_enter_dist": "Enter distance(s), comma-separated:",
    "need_one_distance": "Enter at least one distance.",
    "already_joined": "You're already registered for this event.",
    "joined_ok": "✅ You've joined {name}!",
    "no_upcoming": "No upcoming events right now.",
    "join_load_fail": "Could not load the event",
    "join_ok_type_dist": "OK, type the distance as text.",
    "join_pick_header": "📋 Pick an event:",
    "join_already_registered_dists": (
        "✅ You're already registered! Your distances: {dists}"
    ),
    "join_dist_added_pick": (
        "✅ {name} added. Pick another distance or tap Done:"
    ),
    "join_dist_added_more": "✅ Added. Pick another distance or tap Done:",
    "delete_no_events": "No upcoming events.",
    "delete_which": "Which event to delete?",
    "delete_confirm": (
        "Delete <b>{title}</b>?\n"
        "This cannot be undone."
    ),
    "delete_warn": (
        "⚠️ Delete event «{title}»?\n"
        "👥 Registrations: {count}\n"
        "This cannot be undone."
    ),
    "event_deleted": "✅ Event deleted.",
    "delete_canceled": "Deletion canceled.",
    "edit_no_events": "No upcoming events to edit.",
    "edit_no_events_short": "No upcoming events.",
    "enter_new_name": "Enter new name:",
    "new_location": "New location:",
    "new_url": "New link (or send “-” to clear):",
    "new_notes": "New notes (or “-” to clear):",
    "what_change": "What to change?",
    "join_first": "No registration — use /join first.",
    "pick_your_dist": "Choose distances (your entry):",
    "enter_dists_comma": "Type distances (comma-separated):",
    "comma_values": "Multiple values allowed:",
    "service_down": "Service unavailable",
    "update_dists_ask": "Update distances?",
    "reg_not_found": "Registration not found.",
    "pick_new_dists": "Choose new distances:",
    "enter_dists_text": "Type distances:",
    "comma_sep": "Comma-separated:",
    "check_input": "Check your input and try again.",
    "enter_dist_text": "Type distance as text:",
    "need_one_dist": "At least one distance required",
    "edit_which_event": "📋 Which event to edit?",
    "edit_card_header": "📋 <b>Event</b>\n\n",
    "edit_regs_more": "\n… and {n} more",
    "session_stale_edit": "Session expired. Start with /edit",
    "edit_new_date_label": "📅 New start date:",
    "edit_sport_dist_warning": (
        "⚠️ Your distances may not fit the new sport. "
        "Update distances?"
    ),
    "edit_dist_pick_done": "✅ {name} added. Pick more or Done:",
    "edit_dist_added_flow": "✅ Added. Pick more or tap Done:",
    "stats_empty": "No events yet. Add one with /add!",
    "stats_header": "📊 Stats: {who}",
    "stats_events_count": "🏁 Events: {n}",
    "stats_by_sport": "By sport:",
    "stats_popular": "Popular sports:",
    "stats_which_prompt": "📊 Which stats to show?",
    "stats_team_header_line": "📊 Team statistics",
    "stats_team_total_events": "🏁 Total events: {n}",
    "stats_team_total_people": "👥 Participants: {n}",
    "stats_team_most_active": "🏆 Most active: {name} ({count} events)",
    "stats_popular_locations": "📍 Popular locations:",
    "stats_you_anon": "you",
    "stats_personal_header": "🏅 Personal records:",
    "stats_places_header": "📍 Placings:",
    "testreminder_ok": (
        "✅ Reminder check done. Messages go to all registered groups."
    ),
    "chatid_group_only": (
        "This command only works in groups. "
        "Add me to a group and send /chatid there."
    ),
    "result_no_past": "You have no finished events yet.",
    "result_pick_event": "Pick an event for your result:",
    "result_reg_missing": "Registration not found",
    "result_which_distance": "Which distance is this result for?",
    "result_time_prompt": "Finish time? (e.g. 2:15:30 or 1h 45m)",
    "result_time_short": "Finish time?",
    "result_bad_pick": "Invalid choice",
    "result_session_error": "Session error",
    "result_place_prompt": "🥇 Placing? (e.g. 15/120)",
    "result_block": (
        "🏅 <b>Result:</b>\n"
        "📌 {name} — {dist}\n"
        "⏱ {time}\n"
        "🥇 {place}"
    ),
    "result_saved_ok": "✅ Result saved! 🎉",
    "result_header_dist": "🏅 {name} — {dist}\n\n",
    "ical_all_my": "📅 All my events",
    "ical_caption": (
        "📅 Calendar file for Google / Apple Calendar. "
        "Open it to add to your calendar."
    ),
    "ical_event_url": "🔗 Event link: {url}",
    "ical_all_caption": "📅 All your upcoming events. Open in your calendar app.",
    "ical_pick": "Pick an event for the calendar:",
    "ical_uploading": "Uploading file…",
    "ical_open_hint": "Open it to add to your calendar.",
    "ical_all_building": "Gathering all your events…",
    "ical_no_profile": "Profile not found. Join events with /join.",
    "reminder_tomorrow": "🏁 Event tomorrow!\n\n",
    "reminder_people": "👥 Participants:\n",
    "reminder_no_reg": "• (no registrations yet)",
    "reminder_luck": "Good luck! 💪",
    "reminder_result_intro": "🏅 How was {name}?\n\n",
    "reminder_waiting": "👥 Waiting for results:\n",
    "reminder_use_result": "Use /result to add time and placing 📊",
}

TRANSLATIONS: dict[str, dict[str, str]] = {"ru": RU, "en": EN}


def user_locale(user_id: int | None, language_code: str | None) -> str:
    if user_id is None:
        return "ru"
    saved = USER_LANG.get(user_id)
    if saved in ("ru", "en"):
        return saved
    if language_code and str(language_code).lower().startswith("ru"):
        return "ru"
    return "en"


def set_user_locale(user_id: int, lang: str) -> None:
    USER_LANG[user_id] = "ru" if lang.startswith("ru") else "en"


def t(lang: str, key: str, **kwargs: Any) -> str:
    bundle = TRANSLATIONS.get(lang) or TRANSLATIONS["ru"]
    raw = bundle.get(key)
    if raw is None:
        raw = TRANSLATIONS["ru"].get(key, key)
    if kwargs:
        try:
            return raw.format(**kwargs)
        except (KeyError, ValueError):
            return raw
    return raw
