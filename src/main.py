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
    admin_ab_action,
    admin_ab_mode,
    apply_alternative_hint,
    cancel_flow,
    choose_intensity_after,
    choose_intensity_before,
    consent_accept,
    distortion_info_action,
    distortion_pick_action,
    export_progress,
    go_menu,
    main_menu_action,
    new_thought_entry,
    receive_alternative_thought,
    receive_distortion,
    receive_emotion,
    receive_evidence_against,
    receive_evidence_for,
    receive_intensity_after,
    receive_intensity_before,
    receive_thought_text,
    send_daily_nudges,
    send_session_timeout_nudges,
    set_followup_reminder,
    set_reminders,
    set_tone,
    show_funnel,
    show_help,
    show_history,
    show_onboarding,
    show_settings,
    show_stats,
    start,
)
from state import (
    WAIT_ALTERNATIVE_THOUGHT,
    WAIT_DISTORTION,
    WAIT_EMOTION,
    WAIT_EVIDENCE_AGAINST,
    WAIT_EVIDENCE_FOR,
    WAIT_INTENSITY_AFTER,
    WAIT_INTENSITY_BEFORE,
    WAIT_THOUGHT,
)


def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", show_help))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("funnel", show_funnel))
    app.add_handler(CommandHandler("admin_ab", admin_ab_mode))
    app.add_handler(CallbackQueryHandler(admin_ab_action, pattern=r"^adminab:(status|test|a|b)$"))
    app.add_handler(CallbackQueryHandler(consent_accept, pattern="^consent_accept$"))
    app.add_handler(CallbackQueryHandler(set_tone, pattern=r"^tone:(warm|neutral)$"))
    app.add_handler(CallbackQueryHandler(apply_alternative_hint, pattern=r"^alt_hint:(friend|facts|balanced|one_line|self_support)$|^alt_ai:(rewrite|back)$"))
    app.add_handler(CallbackQueryHandler(main_menu_action, pattern=r"^menu:(history|stats|settings|help|home)$"))
    app.add_handler(CallbackQueryHandler(set_followup_reminder, pattern=r"^followup:(3h)$"))
    app.add_handler(CommandHandler("history", show_history))
    app.add_handler(CommandHandler("export", export_progress))
    app.add_handler(MessageHandler(filters.Regex(r"^История$"), show_history))
    app.add_handler(CommandHandler("settings", show_settings))
    app.add_handler(CommandHandler("onboarding", show_onboarding))
    app.add_handler(CommandHandler("reminders", set_reminders))
    app.add_handler(MessageHandler(filters.Regex(r"^Настройки$"), show_settings))
    app.add_handler(MessageHandler(filters.Regex(r"^В меню$"), go_menu))

    thought_flow = ConversationHandler(
        entry_points=[
            CommandHandler("new", new_thought_entry),
            MessageHandler(filters.Regex(r"^Новая мысль$"), new_thought_entry),
            CallbackQueryHandler(new_thought_entry, pattern=r"^menu:new$"),
        ],
        states={
            WAIT_THOUGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_thought_text)],
            WAIT_EMOTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_emotion)],
            WAIT_INTENSITY_BEFORE: [
                CallbackQueryHandler(choose_intensity_before, pattern=r"^int_before:(20|40|60|80|100)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_intensity_before)
            ],
            WAIT_DISTORTION: [
                CallbackQueryHandler(distortion_info_action, pattern=r"^dist_info:(back|catastrophizing|mind_reading|black_white|discounting_positive|overgeneralization|personalization|emotional_reasoning|should_statements|labeling|fortune_telling|other)$"),
                CallbackQueryHandler(distortion_pick_action, pattern=r"^dist_pick:(catastrophizing|mind_reading|black_white|discounting_positive|overgeneralization|personalization|emotional_reasoning|should_statements|labeling|fortune_telling|other)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_distortion),
            ],
            WAIT_EVIDENCE_FOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_evidence_for)],
            WAIT_EVIDENCE_AGAINST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_evidence_against)
            ],
            WAIT_ALTERNATIVE_THOUGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_alternative_thought)
            ],
            WAIT_INTENSITY_AFTER: [
                CallbackQueryHandler(choose_intensity_after, pattern=r"^int_after:(20|40|60|80|100)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_intensity_after)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_flow),
            MessageHandler(filters.Regex(r"^(Отмена|В меню)$"), cancel_flow),
        ],
        allow_reentry=True,
    )
    app.add_handler(thought_flow)

    if app.job_queue:
        app.job_queue.run_repeating(send_daily_nudges, interval=3600, first=90, name="daily_nudges")
        app.job_queue.run_repeating(send_session_timeout_nudges, interval=900, first=180, name="session_timeout_nudges")

    return app


if __name__ == "__main__":
    load_dotenv()
    init_db()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    application = build_app(token)
    application.run_polling(allowed_updates=Update.ALL_TYPES)
