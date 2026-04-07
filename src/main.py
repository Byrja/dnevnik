import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from db import init_db
from handlers import consent_accept, start


def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(consent_accept, pattern="^consent_accept$"))
    return app


if __name__ == "__main__":
    load_dotenv()
    init_db()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    application = build_app(token)
    application.run_polling(allowed_updates=Update.ALL_TYPES)
