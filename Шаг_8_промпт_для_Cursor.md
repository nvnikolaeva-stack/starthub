# Промпт для Cursor — Шаг 8: Деплой в интернет

Скопируй всё содержимое ниже (от линии до линии) и вставь в чат Cursor:

---

Нужно задеплоить #алкардио чтобы он работал в интернете, а не только на моём компьютере.

ВАЖНО: я не программист. Пиши пошаговые инструкции, объясняй каждое действие.

## Архитектура деплоя

- **Фронтенд (Next.js)** → Vercel (бесплатно)
- **Бэкенд (FastAPI) + Бот (aiogram)** → Railway (~$5/мес)
- **База данных** → SQLite на Railway (или PostgreSQL если нужно)

---

### ЧАСТЬ 1: Подготовка к деплою

#### 1.1 Переменные окружения

Создай файл `backend/.env`:
```
DATABASE_URL=sqlite:///./starthub.db
CORS_ORIGINS=["https://YOUR-VERCEL-URL.vercel.app","http://localhost:3000"]
```

Обнови `backend/app/database.py` — загружать DATABASE_URL из переменных окружения:
```python
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./starthub.db")
```

Обнови `backend/app/main.py` — загружать CORS_ORIGINS из переменных окружения:
```python
import os
import json
origins = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:3000"]'))
app.add_middleware(CORSMiddleware, allow_origins=origins, ...)
```

Обнови `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Создай `frontend/.env.production`:
```
NEXT_PUBLIC_API_URL=https://YOUR-RAILWAY-URL.up.railway.app
```

#### 1.2 Dockerfile для бэкенда + бота

Создай `backend/Dockerfile`:
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Копируем бэкенд
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Копируем бота
COPY bot/requirements.txt ./bot/
RUN pip install --no-cache-dir -r bot/requirements.txt

# Копируем код
COPY backend/ ./backend/
COPY bot/ ./bot/

# Скрипт запуска обоих процессов
COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
```

Создай `start.sh` в корне проекта:
```bash
#!/bin/bash

# Запускаем бэкенд в фоне
cd /app/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Запускаем бота
cd /app/bot
python main.py
```

Создай `.dockerignore`:
```
__pycache__
*.pyc
.env
*.db
node_modules
.next
frontend/
.git
```

#### 1.3 Конфиг для Railway

Создай `railway.toml` в корне проекта:
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "./start.sh"
healthcheckPath = "/api/v1/events"
restartPolicyType = "ON_FAILURE"
```

Создай `Procfile` в корне (альтернатива, если Railway не поддержит Dockerfile):
```
web: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: cd bot && python main.py
```

#### 1.4 Подготовка фронтенда для Vercel

В `frontend/next.config.ts` (или .js) добавь:
```typescript
const nextConfig = {
  output: 'standalone',
  // ... остальные настройки
}
```

Создай `frontend/vercel.json`:
```json
{
  "framework": "nextjs"
}
```

---

### ЧАСТЬ 2: Пошаговая инструкция деплоя (для README.md)

Добавь в README.md секцию "Деплой":

```markdown
## Деплой

### Шаг 1: GitHub

1. Создай аккаунт на github.com (если нет)
2. Создай новый репозиторий: github.com/new → имя "starthub" → Create
3. В терминале (из папки starthub):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/starthub.git
   git push -u origin main
   ```

### Шаг 2: Railway (бэкенд + бот)

1. Зайди на railway.app → Sign up с GitHub
2. New Project → Deploy from GitHub repo → выбери starthub
3. В Settings:
   - Root Directory: оставь пустым (корень)
   - Build Command: (Railway подхватит Dockerfile)
4. В Variables добавь:
   - BOT_TOKEN=8618334899:AAEOsQhOBb9waQ7RNrAjcWgfhPGScLN6Lg8
   - GROUP_CHAT_ID=-5102289323
   - DATABASE_URL=sqlite:///./starthub.db
   - CORS_ORIGINS=["https://YOUR-VERCEL-URL.vercel.app"]
   - API_URL=https://YOUR-RAILWAY-URL.up.railway.app
5. Deploy → дождись зелёного статуса
6. Скопируй URL из Settings → Domains (например starthub-production.up.railway.app)

### Шаг 3: Vercel (фронтенд)

1. Зайди на vercel.com → Sign up с GitHub
2. Import Project → выбери starthub
3. Framework: Next.js
4. Root Directory: frontend
5. Environment Variables:
   - NEXT_PUBLIC_API_URL=https://YOUR-RAILWAY-URL.up.railway.app
6. Deploy → дождись
7. Скопируй URL (например starthub.vercel.app)

### Шаг 4: Обновить CORS

Вернись в Railway → Variables → обнови CORS_ORIGINS с реальным URL Vercel:
```
CORS_ORIGINS=["https://starthub.vercel.app"]
```
Redeploy.

### Шаг 5: Проверка

- Открой https://starthub.vercel.app — сайт работает
- Напиши боту /list — данные подтягиваются
- Создай старт на сайте — он виден в боте
- Создай старт в боте — он виден на сайте
```

---

### ЧАСТЬ 3: Обнови bot/.env и config

Бот должен уметь работать с API по URL из переменной окружения (а не только localhost):

В bot/config.py убедись что API_URL загружается из .env:
```python
API_URL = os.getenv("API_URL", "http://localhost:8000")
```

В bot/api_client.py убедись что base_url берётся из config, а не захардкожен.

---

### ЧАСТЬ 4: .gitignore

Обнови `.gitignore` в корне проекта:
```
# Python
__pycache__/
*.pyc
*.pyo
*.db
.env

# Node
node_modules/
.next/
out/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Env files
bot/.env
backend/.env
frontend/.env.local
frontend/.env.production
```

ВАЖНО: .env файлы НЕ должны попадать в git (в них секреты).

---

### Проверка

1. git status — нет .env файлов и __pycache__
2. Все переменные окружения загружаются из .env / переменных Railway
3. CORS настроен правильно
4. Dockerfile собирается без ошибок
5. start.sh запускает бэкенд и бота одновременно

Создай/обнови все файлы.

---
