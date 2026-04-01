import os
import subprocess
import sys
import threading


def run_bot():
    """Запускает бота в отдельном потоке"""
    bot_dir = os.path.join(os.path.dirname(__file__), "..", "bot")
    subprocess.run([sys.executable, "main.py"], cwd=bot_dir)


if __name__ == "__main__":
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Запускаем API в основном потоке
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
