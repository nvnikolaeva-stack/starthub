# Промпт для Cursor — Шаг 5: Веб-сайт (календарь + карточки стартов)

Скопируй всё содержимое ниже (от линии до линии) и вставь в чат Cursor:

---

Я продолжаю создавать #алкардио. Бэкенд (FastAPI) работает на http://localhost:8000, бот работает. Теперь нужно создать веб-приложение.

ВАЖНО: я не программист. Пиши весь код сам, каждый файл полностью рабочий. На Mac используется python3 и Node.js (уже установлены).

## Задача: создать веб-приложение с календарём и карточками стартов

### Технологии
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui (компоненты)
- Никаких дополнительных UI-библиотек для календаря — написать свой компонент

### Инициализация проекта

В папке `starthub/frontend/` выполни:
```bash
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
```

Потом установи shadcn/ui:
```bash
npx shadcn@latest init
```
(выбери стиль Default, цвет Slate)

Установи компоненты shadcn:
```bash
npx shadcn@latest add button card badge select dialog tooltip
```

### Структура страниц

```
frontend/src/
├── app/
│   ├── layout.tsx          # общий layout с навбаром
│   ├── page.tsx            # главная — календарь
│   ├── event/
│   │   └── [id]/
│   │       └── page.tsx    # карточка старта
│   ├── add/
│   │   └── page.tsx        # форма добавления (Шаг 6, пока заглушка)
│   └── stats/
│       └── page.tsx        # статистика (Шаг 6, пока заглушка)
├── components/
│   ├── Navbar.tsx           # навигация
│   ├── Calendar.tsx         # месячная сетка
│   ├── CalendarDay.tsx      # ячейка одного дня
│   ├── EventCard.tsx        # карточка старта (компактная, для списка)
│   ├── EventCardFull.tsx    # полная карточка (страница старта)
│   ├── FilterBar.tsx        # фильтры над календарём
│   ├── UpcomingEvents.tsx   # список ближайших стартов под календарём
│   └── SportIcon.tsx        # иконки видов спорта
├── lib/
│   ├── api.ts              # функции для запросов к бэкенду
│   └── types.ts            # TypeScript типы
└── styles/
    └── globals.css          # глобальные стили (Tailwind)
```

### lib/types.ts — типы данных

```typescript
export type SportType = "swimming" | "triathlon" | "running" | "cycling" | "other";

export interface Event {
  id: string;
  name: string;
  date_start: string; // ISO date
  date_end: string | null;
  location: string;
  sport_type: SportType;
  url: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  registrations?: Registration[];
}

export interface Participant {
  id: string;
  display_name: string;
  telegram_username: string | null;
}

export interface Registration {
  id: string;
  event_id: string;
  participant_id: string;
  participant?: Participant;
  distances: string[];
  result_time: string | null;
  result_place: string | null;
}

export interface CommunityStats {
  total_events: number;
  total_participants: number;
  most_active_participant: { name: string; count: number } | null;
  popular_sports: { sport: string; count: number }[];
  popular_locations: { location: string; count: number }[];
}
```

### lib/api.ts — API-клиент

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getEvents(params?: {
  sport_type?: string;
  upcoming?: boolean;
  limit?: number;
  period?: string;
  date_from?: string;
  date_to?: string;
}): Promise<Event[]> { ... }

export async function getEvent(id: string): Promise<Event> { ... }

export async function createEvent(data: Partial<Event>): Promise<Event> { ... }

export async function updateEvent(id: string, data: Partial<Event>): Promise<Event> { ... }

export async function deleteEvent(id: string): Promise<void> { ... }

export async function getDistances(sportType: string): Promise<string[]> { ... }

export async function joinEvent(data: {
  event_id: string;
  participant_id: string;
  distances: string[];
}): Promise<Registration> { ... }

export async function createParticipant(data: {
  display_name: string;
}): Promise<Participant> { ... }

export async function getCommunityStats(): Promise<CommunityStats> { ... }

export async function getEventIcal(id: string): Promise<Blob> { ... }
```

Все функции используют fetch(). Обрабатывай ошибки: если API недоступен — показывать "Сервер недоступен".

Добавь файл `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Навбар (Navbar.tsx)

Простая навигация сверху:
- Логотип: "🏃 #алкардио" (ссылка на главную)
- Ссылки: Календарь | Добавить старт | Статистика
- Справа: переключатель языка RU/EN (пока заглушка, просто кнопка)
- Адаптивный: на мобильном — бургер-меню

### Главная страница (page.tsx)

Состоит из трёх блоков:

**Блок 1: Фильтры (FilterBar.tsx)**
- Горизонтальная полоса над календарём
- Фильтр по виду спорта: кнопки-badges (Все | 🏊 Плавание | 🏃 Бег | 🚴 Велогонка | 🔱 Триатлон | 🏅 Прочее)
- Фильтр по участнику: dropdown select (список всех участников)
- Чекбокс "Показать прошедшие"
- Активный фильтр подсвечен

**Блок 2: Календарь (Calendar.tsx)**

Месячная сетка (7 колонок: Пн Вт Ср Чт Пт Сб Вс):

- Навигация: ← [Март 2026] → (кнопки вперёд/назад по месяцам)
- Каждая ячейка = один день
- Выходные (Сб, Вс) — фоновый цвет ячейки светлее/другой оттенок (например light blue или light amber), чтобы выделялись
- Сегодняшний день — обведён рамкой
- Дни с прошедшими стартами — слегка приглушённые (но видимые)

**Индикаторы стартов на ячейках:**
- Если на дату есть старты — показать цветные точки (dots) внизу ячейки
- Цвет точки по виду спорта:
  - Плавание — голубой (#3B8BD4)
  - Бег — зелёный (#27AE60)
  - Велогонка — оранжевый (#F39C12)
  - Триатлон — фиолетовый (#8E44AD)
  - Прочее — серый (#95A5A6)
- Максимум 4 точки видно, если больше — "..." или "+2"
- При наведении (hover) на ячейку — tooltip с названиями стартов:
  ```
  15 июня
  🔱 Ironstar Sochi
  🏃 Parkrun Сочи
  ```
- При клике на ячейку с одним стартом → переход на /event/{id}
- При клике на ячейку с несколькими стартами → показать popup/dropdown со списком, каждый кликабельный

**Мобильная версия:**
- Календарная сетка сжимается (маленькие ячейки, без текста внутри, только точки)
- Под календарём — список стартов выбранного месяца (карточки)
- При тапе на день — скролл к стартам этого дня в списке

**Блок 3: Ближайшие старты (UpcomingEvents.tsx)**

Под календарём — секция "Ближайшие старты" со списком карточек EventCard.

EventCard (компактная карточка):
```
┌─────────────────────────────────────────┐
│ 🔱  Ironstar Sochi                      │
│ 📅 15 — 17 июня 2026 (Сб—Пн)           │
│ 📍 Сочи, Россия                         │
│ 📏 Olympic, Sprint                      │
│ 👥 Алексей, Мария, Петя (3)             │
│                              [Подробнее]│
└─────────────────────────────────────────┘
```

- Иконка вида спорта + цветная полоска слева (по цвету спорта)
- Дата: показывать день недели (Сб, Вс подсвечены)
- Участники: имена через запятую, если больше 3 — "и ещё N"
- Кнопка "Подробнее" → переход на /event/{id}
- Прошедшие старты — полупрозрачные (opacity 0.6)

### Страница старта (/event/[id]/page.tsx)

Полная карточка EventCardFull:

```
┌────────────────────────────────────────────┐
│ 🔱 ТРИАТЛОН                                │
│                                            │
│ Ironstar Sochi 2026                        │
│                                            │
│ 📅  15 — 17 июня 2026 (Сб — Пн, 3 дня)    │
│ 📍  Сочи, Россия                           │
│ 📏  Olympic, Sprint                        │
│ 🔗  ironstar.com                           │
│ 📝  Нужен гидрокостюм                      │
│                                            │
│ 👥 Участники (3)                           │
│ ┌────────────────────────────────────────┐  │
│ │ Алексей (@alexrun)                     │  │
│ │   Olympic — ⏱ 2:15:30 — 🥇 15/120     │  │
│ │ Мария                                  │  │
│ │   Sprint — результат не указан         │  │
│ │ Петя (@petya)                          │  │
│ │   Olympic — результат не указан        │  │
│ └────────────────────────────────────────┘  │
│                                            │
│ [📅 Добавить в календарь] [✏️ Редактировать]│
│ [👥 Я тоже еду!]          [🗑 Удалить]     │
└────────────────────────────────────────────┘
```

**Кнопка "Добавить в календарь":**
- Скачивает .ics файл через API (GET /api/v1/events/{id}/ical)
- Создаёт ссылку для скачивания: `<a href="..." download="event.ics">`

**Кнопка "Я тоже еду!":**
- Открывает dialog/modal:
  - Ввести имя (текстовое поле)
  - Выбрать дистанцию (chips из предустановленных + свободный ввод)
  - Кнопка "Записаться"
- При сохранении: создаёт participant + registration через API
- Обновляет список участников на странице

**Кнопка "Редактировать":**
- Открывает dialog/modal с формой редактирования (все поля предзаполнены)
- При сохранении: PUT /api/v1/events/{id}
- Обновляет карточку

**Кнопка "Удалить":**
- Confirmation dialog: "Удалить старт? На него записано N участников."
- При подтверждении: DELETE /api/v1/events/{id}
- Redirect на главную

### SportIcon.tsx — иконки

Компонент, возвращающий эмодзи или SVG-иконку по типу спорта:
- swimming → 🏊
- running → 🏃
- cycling → 🚴
- triathlon → 🔱
- other → 🏅

### Адаптивность (responsive)

ВСЁ должно хорошо выглядеть на мобильном (375px ширина):
- Навбар: бургер-меню
- Календарь: компактная сетка (числа без текста)
- Карточки: полная ширина, стэк
- Фильтры: горизонтальный скролл
- Модальные окна: полноэкранные на мобильном

### Запуск

```bash
cd frontend
npm install
npm run dev
```

Сайт должен запуститься на http://localhost:3000

Добавь в README.md инструкции по запуску всех трёх компонентов:
```
# Запуск #алкардио

## 1. Бэкенд
cd backend
python3 -m uvicorn app.main:app --reload --port 8000

## 2. Бот
cd bot
python3 main.py

## 3. Сайт
cd frontend
npm run dev
```

### CORS

Убедись что в бэкенде (backend/app/main.py) CORS разрешает запросы с http://localhost:3000:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Проверка

После создания:
1. `npm run dev` запускается без ошибок
2. http://localhost:3000 открывается
3. Календарь показывает текущий месяц
4. Если есть старты в базе — они отображаются точками на календаре
5. Клик на точку → переход на страницу старта
6. Страница старта показывает всю информацию
7. На мобильном (сузь браузер) всё выглядит нормально

Создай ВСЕ файлы. Каждый полностью рабочий.

---
