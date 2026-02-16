import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

APP_URL = os.getenv("APP_URL")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{APP_URL}{WEBHOOK_PATH}" if APP_URL else None

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")
if not APP_URL:
    raise ValueError("APP_URL not set")


