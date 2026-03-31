# Промпт для Cursor — Шаг 7: Два языка (RU + EN)

Скопируй всё содержимое ниже (от линии до линии) и вставь в чат Cursor:

---

В #алкардио нужно добавить поддержку двух языков: русский (по умолчанию) и английский.

ВАЖНО: я не программист. Пиши весь код сам, каждый файл полностью рабочий. Редактируй существующие файлы.

## Задача: добавить i18n на сайт и в бота

---

### ЧАСТЬ 1: Сайт (Next.js)

Используй библиотеку `next-intl`. Установи:
```bash
cd frontend
npm install next-intl
```

#### Структура переводов

Создай папку `frontend/src/messages/`:

```
messages/
├── ru.json
└── en.json
```

**ru.json:**
```json
{
  "nav": {
    "calendar": "Календарь",
    "addEvent": "Добавить старт",
    "stats": "Статистика"
  },
  "calendar": {
    "title": "Календарь стартов",
    "upcoming": "Ближайшие старты",
    "noEvents": "Нет стартов",
    "showPast": "Показать прошедшие",
    "details": "Подробнее",
    "weekdays": {
      "mon": "Пн", "tue": "Вт", "wed": "Ср",
      "thu": "Чт", "fri": "Пт", "sat": "Сб", "sun": "Вс"
    }
  },
  "filters": {
    "all": "Все",
    "swimming": "Плавание",
    "running": "Бег",
    "cycling": "Велогонка",
    "triathlon": "Триатлон",
    "other": "Прочее",
    "participant": "Участник"
  },
  "event": {
    "date": "Дата",
    "location": "Локация",
    "distance": "Дистанция",
    "participants": "Участники",
    "results": "Результаты",
    "time": "Время",
    "place": "Место",
    "noResult": "результат не указан",
    "link": "Ссылка",
    "notes": "Заметки",
    "addToCalendar": "Добавить в календарь",
    "joinEvent": "Я тоже еду!",
    "edit": "Редактировать",
    "delete": "Удалить",
    "confirmDelete": "Удалить старт? На него записано {count} участников.",
    "deleted": "Старт удалён",
    "notFound": "Старт не найден"
  },
  "addForm": {
    "title": "Добавить старт",
    "sportType": "Вид спорта",
    "name": "Название старта",
    "dateStart": "Дата начала",
    "dateEnd": "Дата окончания",
    "multiDay": "Многодневный",
    "days": "Количество дней",
    "locationLabel": "Город / Локация",
    "distanceLabel": "Дистанция",
    "addCustom": "Другое",
    "urlLabel": "Ссылка на событие",
    "participantsLabel": "Участники",
    "addParticipant": "Добавить",
    "notesLabel": "Заметки",
    "save": "Сохранить старт",
    "clear": "Очистить форму",
    "saved": "Старт сохранён!",
    "preview": "Превью"
  },
  "stats": {
    "title": "Статистика",
    "team": "Команда",
    "participants": "Участники",
    "totalEvents": "Всего стартов",
    "totalParticipants": "Участников",
    "mostActive": "Самый активный",
    "events": "стартов",
    "bySport": "По видам спорта",
    "popularLocations": "Популярные локации",
    "personalRecords": "Личные рекорды",
    "recentPlaces": "Последние места",
    "noEvents": "Пока нет стартов",
    "more": "Подробнее"
  },
  "join": {
    "title": "Присоединиться к старту",
    "yourName": "Ваше имя",
    "selectDistance": "Выберите дистанцию",
    "submit": "Записаться",
    "success": "Вы записаны!"
  },
  "common": {
    "cancel": "Отмена",
    "confirm": "Подтвердить",
    "back": "Назад",
    "serverError": "Сервер недоступен"
  }
}
```

**en.json:** — создай аналогичный файл с английскими переводами. Переведи ВСЕ строки.

#### Настройка next-intl

1. Создай `frontend/src/i18n/request.ts` — конфигурация next-intl
2. Обнови `frontend/src/app/layout.tsx` — обернуть в NextIntlClientProvider
3. Язык определяется из cookie или localStorage (по умолчанию "ru")
4. Переключатель языка в Navbar.tsx — кнопка RU/EN, при клике меняет язык и перезагружает переводы

#### Замени все захардкоженные строки

Пройди по ВСЕМ компонентам и замени русский текст на вызовы `useTranslations()`:

```typescript
import { useTranslations } from 'next-intl';

function Calendar() {
  const t = useTranslations('calendar');
  return <h1>{t('title')}</h1>;  // вместо "Календарь стартов"
}
```

Компоненты для обновления:
- Navbar.tsx
- Calendar.tsx
- CalendarDay.tsx
- EventCard.tsx
- EventCardFull.tsx
- FilterBar.tsx
- UpcomingEvents.tsx
- add/page.tsx
- stats/page.tsx
- event/[id]/page.tsx

---

### ЧАСТЬ 2: Бот (Telegram)

Добавь команду `/lang` для смены языка бота.

1. Создай `bot/handlers/lang.py`
2. Создай `bot/translations.py` — словарь переводов

```python
TRANSLATIONS = {
    "ru": {
        "welcome": "🏃 Привет! Я #алкардио — бот для отслеживания спортивных стартов.",
        "choose_sport": "Выбери вид спорта:",
        "enter_name": "Введи название старта:",
        "enter_date": "📅 Когда старт? Укажи дату:",
        "enter_location": "Город / Локация:",
        "choose_distance": "Выбери дистанцию:",
        "enter_link": "Ссылка на событие (или нажми Пропустить):",
        "add_participants": "Добавить ещё участников?",
        "enter_notes": "Заметки (или нажми Пропустить):",
        "save": "✅ Сохранить",
        "edit": "✏️ Редактировать",
        "cancel": "❌ Отмена",
        "back": "◀️ Назад",
        "skip": "Пропустить",
        "done": "Готово ✓",
        "yes": "Да",
        "no": "Нет",
        "event_saved": "✅ Старт сохранён!",
        "no_events": "Пока нет запланированных стартов.",
        "already_joined": "Ты уже записан на этот старт!",
        "joined": "✅ Ты записан на {name}!",
        # ... добавь все строки которые бот отправляет
    },
    "en": {
        "welcome": "🏃 Hi! I'm #alkardio — a bot for tracking sports events.",
        "choose_sport": "Choose sport type:",
        "enter_name": "Enter event name:",
        "enter_date": "📅 When is the event? Enter date:",
        "enter_location": "City / Location:",
        "choose_distance": "Choose distance:",
        "enter_link": "Event link (or press Skip):",
        "add_participants": "Add more participants?",
        "enter_notes": "Notes (or press Skip):",
        "save": "✅ Save",
        "edit": "✏️ Edit",
        "cancel": "❌ Cancel",
        "back": "◀️ Back",
        "skip": "Skip",
        "done": "Done ✓",
        "yes": "Yes",
        "no": "No",
        "event_saved": "✅ Event saved!",
        "no_events": "No upcoming events yet.",
        "already_joined": "You're already registered for this event!",
        "joined": "✅ You've joined {name}!",
        # ... добавь все строки
    }
}
```

3. Язык пользователя сохраняется в памяти (dict: telegram_id → lang). По умолчанию — определяется из Telegram (message.from_user.language_code): если "ru" → русский, иначе → английский.

4. Команда `/lang`:
   ```
   🌐 Выберите язык / Choose language:
   [🇷🇺 Русский] [🇬🇧 English]
   ```

5. Замени ВСЕ захардкоженные строки во ВСЕХ хэндлерах на вызовы из translations.

6. Добавь `/lang` в меню бота и в /help.

---

### Проверка

1. Сайт: переключи на EN → все тексты на английском, переключи обратно → русский
2. Бот: /lang → English → /add → все сообщения на английском
3. Бот: /lang → Русский → всё на русском
4. Навбар: кнопка RU/EN работает
5. Формы, фильтры, карточки — всё переведено

---
