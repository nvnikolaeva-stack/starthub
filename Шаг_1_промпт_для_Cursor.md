# Промпт для Cursor — Шаг 1: Каркас проекта + База данных + API

Скопируй всё содержимое ниже (от линии до линии) и вставь в чат Cursor:

---

Я создаю приложение #алкардио — Telegram-бот + веб-сайт для группы спортсменов-любителей (до 20 человек), которые отслеживают свои спортивные старты (бег, триатлон, плавание, велогонки).

ВАЖНО: я не программист. Пиши весь код сам, не пропускай шаги, не говори "добавьте сами". Каждый файл должен быть полностью готов к запуску.

На Mac, Python вызывается через `python3` и `pip3`. Используй это везде.

## Задача: создай каркас проекта с базой данных и API

### 1. Структура папок

Создай монорепозиторий со следующей структурой:

```
starthub/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI приложение
│   │   ├── database.py          # подключение к SQLite
│   │   ├── models.py            # SQLAlchemy модели
│   │   ├── schemas.py           # Pydantic схемы
│   │   ├── crud.py              # CRUD операции
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── events.py        # эндпоинты стартов
│   │       ├── participants.py  # эндпоинты участников
│   │       ├── registrations.py # эндпоинты регистраций
│   │       └── stats.py         # эндпоинты статистики
│   ├── requirements.txt
│   └── alembic/                 # миграции (настрой alembic init)
├── bot/
│   ├── __init__.py
│   ├── main.py                  # точка входа бота (пока пустой, с заглушкой)
│   └── requirements.txt
├── frontend/                    # пока пустая папка, создай только её
├── .gitignore
└── README.md
```

### 2. База данных — три таблицы

Используй SQLite через SQLAlchemy (async не нужен, используй синхронный вариант для простоты). Файл базы: `backend/starthub.db`

**Таблица events (старты):**
- id: UUID, primary key, генерируется автоматически
- name: string, обязательное (название старта, например "Ironstar Sochi")
- date_start: date, обязательное
- date_end: date, nullable (для многодневных стартов, максимум +7 дней от date_start)
- location: string, обязательное (город/страна)
- sport_type: string, обязательное, одно из: "swimming", "triathlon", "running", "cycling", "other"
- url: string, nullable (ссылка на событие)
- notes: string, nullable (свободное поле для заметок)
- created_by: string, обязательное (кто создал)
- created_at: datetime, автоматически

**Таблица participants (участники):**
- id: UUID, primary key
- display_name: string, обязательное
- telegram_id: integer, nullable, unique
- telegram_username: string, nullable
- normalized_name: string, обязательное (lowercase, trimmed — для поиска дубликатов)
- created_at: datetime, автоматически

**Таблица registrations (кто на какой старт записан):**
- id: UUID, primary key
- event_id: UUID, foreign key → events.id, cascade delete
- participant_id: UUID, foreign key → participants.id
- distances: JSON (массив строк, например ["Olympic", "Sprint"])
- result_time: string, nullable (свободный ввод, например "2:15:30")
- result_place: string, nullable (свободный ввод, например "15/120 overall")
- created_at: datetime, автоматически
- unique constraint на (event_id, participant_id) — один человек не может записаться дважды на один старт

### 3. Справочник дистанций

Создай константы в отдельном месте (например в models.py или отдельном файле constants.py):

```python
SPORT_TYPES = ["swimming", "triathlon", "running", "cycling", "other"]

DISTANCES = {
    "triathlon": ["Sprint", "Olympic", "Half Ironman (70.3)", "Ironman (140.6)", "Other"],
    "running": ["5K", "10K", "Half Marathon", "Marathon", "Ultra", "Fun Run", "Backyard", "Beer Mile", "Other"],
    "swimming": [],  # свободный ввод
    "cycling": [],   # свободный ввод
    "other": [],     # свободный ввод
}
```

### 4. API эндпоинты (FastAPI)

Все эндпоинты с префиксом `/api/v1/`

**Старты (events):**
- `GET /api/v1/events` — список стартов. Query-параметры:
  - sport_type (фильтр по виду спорта)
  - upcoming (bool) — только будущие
  - limit (int, default 5)
  - period ("weekend", "month", "3months", "all")
- `GET /api/v1/events/{id}` — один старт со всеми участниками и результатами
- `POST /api/v1/events` — создать старт. Валидация: date_end не больше date_start + 7 дней
- `PUT /api/v1/events/{id}` — обновить старт
- `DELETE /api/v1/events/{id}` — удалить старт (каскадно удалит регистрации)

**Участники (participants):**
- `GET /api/v1/participants` — список всех участников
- `GET /api/v1/participants/{id}` — один участник с его стартами
- `POST /api/v1/participants` — создать/найти участника. При создании:
  - normalized_name = display_name.lower().strip()
  - Если есть telegram_id и он совпадает с существующим — вернуть существующего
- `PUT /api/v1/participants/{id}` — обновить

**Регистрации (registrations):**
- `POST /api/v1/registrations` — записать участника на старт (event_id + participant_id + distances)
- `PUT /api/v1/registrations/{id}` — обновить (например добавить результат)
- `DELETE /api/v1/registrations/{id}` — отписаться от старта

**Статистика (stats):**
- `GET /api/v1/stats/participant/{id}` — статистика участника:
  - total_events (всего стартов)
  - events_by_sport (разбивка по видам спорта)
  - personal_records (лучшее время по каждой дистанции)
  - places_history (история занятых мест)
- `GET /api/v1/stats/community` — общая статистика:
  - total_events
  - total_participants
  - most_active_participant
  - popular_sports
  - popular_locations

**Утилиты:**
- `GET /api/v1/distances/{sport_type}` — вернуть список предустановленных дистанций для вида спорта
- `GET /api/v1/events/{id}/ical` — вернуть .ics файл для конкретного старта (Content-Type: text/calendar)

### 5. Настройка запуска

В `requirements.txt` бэкенда добавь:
```
fastapi
uvicorn
sqlalchemy
alembic
pydantic
ics
python-multipart
```

Добавь в README.md инструкцию по запуску:
```bash
cd backend
pip3 install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

После запуска API должно быть доступно на http://localhost:8000
Документация Swagger — на http://localhost:8000/docs

### 6. Проверка

После создания всех файлов:
1. Убедись, что `python3 -m uvicorn app.main:app --reload --port 8000` запускается без ошибок
2. Swagger UI открывается в браузере
3. Можно создать старт через POST /api/v1/events
4. Можно добавить участника через POST /api/v1/participants
5. Можно записать участника на старт через POST /api/v1/registrations

Создай все файлы сейчас. Не пропускай ни одного файла. Каждый файл должен быть полностью рабочим.

---
