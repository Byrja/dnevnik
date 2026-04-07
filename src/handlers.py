from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from db import get_conn
from texts import DISCLAIMER_RU, MENU_RU, START_RU


def _user_exists(tg_user_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE tg_user_id = ?", (tg_user_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def _save_user_with_default_settings(update: Update) -> None:
    user = update.effective_user
    if not user:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO users (tg_user_id, username, first_name)
        VALUES (?, ?, ?)
        """,
        (user.id, user.username, user.first_name),
    )
    cur.execute(
        """
        INSERT OR IGNORE INTO settings (tg_user_id, tone, language)
        VALUES (?, 'warm', 'ru')
        """,
        (user.id,),
    )
    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    if _user_exists(user.id):
        keyboard = ReplyKeyboardMarkup(
            [["Новая мысль", "История"], ["Настройки"]],
            resize_keyboard=True,
        )
        await update.message.reply_text(START_RU)
        await update.message.reply_text(MENU_RU, reply_markup=keyboard)
        return

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Согласен", callback_data="consent_accept")]]
    )
    await update.message.reply_text(DISCLAIMER_RU, reply_markup=keyboard)


async def consent_accept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    _save_user_with_default_settings(update)

    keyboard = ReplyKeyboardMarkup(
        [["Новая мысль", "История"], ["Настройки"]],
        resize_keyboard=True,
    )
    await query.edit_message_text("✅ Согласие сохранено.")
    await query.message.reply_text(START_RU)
    await query.message.reply_text(MENU_RU, reply_markup=keyboard)
