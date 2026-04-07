import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from db import init_db
from handlers import (
    consent_accept,
    new_thought_entry,
    receive_distortion,
    receive_emotion,
    receive_intensity_before,
    receive_thought_text,
    start,
)
from state import WAIT_DISTORTION, WAIT_EMOTION, WAIT_INTENSITY_BEFORE, WAIT_THOUGHT


def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(consent_accept, pattern="^consent_accept$"))

    thought_flow = ConversationHandler(
        entry_points=[
            CommandHandler("new", new_thought_entry),
            MessageHandler(filters.Regex(r"^Новая мысль$"), new_thought_entry),
        ],
        states={
            WAIT_THOUGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_thought_text)],
            WAIT_EMOTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_emotion)],
            WAIT_INTENSITY_BEFORE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_intensity_before)
            ],
            WAIT_DISTORTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_distortion)],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    app.add_handler(thought_flow)
    return app


if __name__ == "__main__":
    load_dotenv()
    init_db()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    application = build_app(token)
    application.run_polling(allowed_updates=Update.ALL_TYPES)
