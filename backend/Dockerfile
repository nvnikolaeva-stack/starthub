# Build context: корень репозитория (см. railway.toml).
FROM python:3.13-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY bot/requirements.txt ./bot/
RUN pip install --no-cache-dir -r bot/requirements.txt

COPY backend/ ./backend/
COPY bot/ ./bot/

COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
