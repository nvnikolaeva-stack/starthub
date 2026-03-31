import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
