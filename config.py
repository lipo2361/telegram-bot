import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in environment variables")

