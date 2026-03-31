# #алкардио

## Запуск компонентов

### 1. Бэкенд

```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

### 2. Бот

```bash
cd bot
python3 main.py
```

### 3. Сайт

```bash
cd frontend
npm install
npm run dev
```

Сайт: [http://localhost:3000](http://localhost:3000). API: [http://localhost:8000](http://localhost:8000).

---

## Тесты бэкенда

```bash
cd backend
pip3 install -r requirements-test.txt
python3 -m pytest tests/ -v
```

## Тесты бота (утилиты)

```bash
cd bot
pip3 install -r requirements-test.txt
python3 -m pytest tests/ -v
```

---

## Переменные окружения (локально)

1. Скопируй примеры и подставь свои значения:
   - `backend/.env.example` → `backend/.env`
   - `frontend/.env.local.example` → `frontend/.env.local`
2. Для бота: в `bot/` создай `.env` с `BOT_TOKEN` (от [@BotFather](https://t.me/BotFather)) и при необходимости `API_URL=http://localhost:8000`.
3. После деплоя фронта создай на Vercel переменную `NEXT_PUBLIC_API_URL` (см. ниже); файл `frontend/.env.production` нужен только при локальной сборке `next build` с продакшен-URL.

---

## Деплой (Vercel + Railway)

Идея: **сайт** на [Vercel](https://vercel.com) (бесплатный тариф), **API и Telegram-бот** на [Railway](https://railway.app) (платный по использованию; ориентир — несколько долларов в месяц). База — **SQLite** в файле на диске контейнера Railway (для серьёзной нагрузки позже можно перейти на PostgreSQL).

### Шаг 1: GitHub

1. Зарегистрируйся на [github.com](https://github.com), если аккаунта ещё нет.
2. Создай новый репозиторий: **New repository** → имя, например `alkardio` → **Create**.
3. В терминале из папки проекта:

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/alkardio.git
   git push -u origin main
   ```

   Замени `YOUR_USERNAME` на свой логин GitHub.

### Шаг 2: Railway (бэкенд + бот)

1. Зайди на [railway.app](https://railway.app) → **Sign up** через GitHub.
2. **New Project** → **Deploy from GitHub repo** → выбери репозиторий `alkardio`.
3. Railway должен подхватить **Dockerfile** из `backend/Dockerfile` (контекст сборки — **корень** репозитория; это задано в `railway.toml`).
4. Во вкладке сервиса открой **Variables** и добавь (подставь свои значения, **не публикуй токен бота в открытом доступе**):
   - `BOT_TOKEN` — токен от BotFather;
   - при необходимости `GROUP_CHAT_ID` и другие переменные, которые читает бот;
   - `DATABASE_URL` — например `sqlite:///./starthub.db` (файл в контейнере; при пересоздании тома данные могут обнулиться — для продакшена смотри в сторону PostgreSQL или постоянного тома);
   - `CORS_ORIGINS` — JSON-массив URL фронтенда, например после появления Vercel:
     `["https://your-app.vercel.app"]`
     Для отладки можно временно добавить `http://localhost:3000`.
   - `API_URL` — **публичный URL этого же сервиса Railway** (с `https://`), чтобы бот ходил в API не на `localhost`, а в интернет. Пример: `https://your-project.up.railway.app` (точный домен смотри в **Settings → Networking / Public URL** после деплоя).
5. Нажми **Deploy** и дождись успешной сборки.
6. Скопируй публичный URL API (он понадобится для Vercel и для `API_URL`, если ещё не выставил).

### Шаг 3: Vercel (фронтенд)

1. [vercel.com](https://vercel.com) → вход через GitHub.
2. **Add New… → Project** → **Import** репозиторий `alkardio`.
3. **Root Directory** укажи `frontend` (монорепозиторий).
4. **Environment Variables**:
   - `NEXT_PUBLIC_API_URL` = твой URL Railway API (например `https://your-project.up.railway.app`, **без** завершающего `/`).
5. **Deploy**. Скопируй URL вида `https://....vercel.app`.

### Шаг 4: CORS

Вернись в Railway → **Variables** → обнови `CORS_ORIGINS`, добавив **точный** HTTPS-URL сайта с Vercel (в кавычках в JSON-массиве). Сохрани и при необходимости сделай **Redeploy**.

### Шаг 5: Проверка

- Открой сайт на Vercel — главная и календарь должны грузиться.
- В боте выполни, например, `/list` — данные должны приходить с API.
- Создай старт на сайте и проверь в боте (и наоборот).

### Локальная сборка Docker (по желанию)

Из **корня** репозитория:

```bash
docker build -f backend/Dockerfile -t alkardio .
```

Переменные передай через `-e` или `docker compose` по аналогии с Railway.

---

## Безопасность

- Файлы `.env`, `backend/.env`, `bot/.env`, `frontend/.env.local`, `frontend/.env.production` **не коммить** — они в `.gitignore`.
- Токен бота и секреты храни только в переменных окружения на Railway / в локальных `.env`.
