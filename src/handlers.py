from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from db import get_conn
from state import WAIT_DISTORTION, WAIT_EMOTION, WAIT_INTENSITY_BEFORE, WAIT_THOUGHT
from texts import (
    DISCLAIMER_RU,
    DISTORTION_PROMPT_RU,
    DISTORTION_SAVED_RU,
    EMOTION_PROMPT_RU,
    EMOTION_SAVED_RU,
    EMOTION_STEP_DONE_RU,
    INTENSITY_PROMPT_RU,
    MENU_RU,
    START_RU,
    THOUGHT_PROMPT_RU,
    THOUGHT_SAVED_RU,
)


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


async def new_thought_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END
    await update.message.reply_text(THOUGHT_PROMPT_RU)
    return WAIT_THOUGHT


async def receive_thought_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.effective_user:
        return ConversationHandler.END

    thought_text = (update.message.text or "").strip()
    if len(thought_text) < 3:
        await update.message.reply_text("Слишком коротко. Напиши хотя бы 3 символа.")
        return WAIT_THOUGHT

    context.user_data["draft_entry"] = {
        "tg_user_id": update.effective_user.id,
        "thought_text": thought_text,
    }

    emotion_keyboard = ReplyKeyboardMarkup(
        [["Тревога", "Грусть", "Злость"], ["Стыд", "Вина", "Раздражение"], ["Страх", "Пустота", "Другое"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(THOUGHT_SAVED_RU)
    await update.message.reply_text(EMOTION_PROMPT_RU, reply_markup=emotion_keyboard)
    return WAIT_EMOTION


async def receive_emotion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END
    emotion = (update.message.text or "").strip()
    if not emotion:
        await update.message.reply_text("Выбери эмоцию кнопкой или введи текстом.")
        return WAIT_EMOTION

    draft = context.user_data.get("draft_entry", {})
    draft["emotion_label"] = emotion
    context.user_data["draft_entry"] = draft

    await update.message.reply_text(EMOTION_SAVED_RU)
    await update.message.reply_text(INTENSITY_PROMPT_RU)
    return WAIT_INTENSITY_BEFORE


async def receive_intensity_before(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.effective_user:
        return ConversationHandler.END

    raw = (update.message.text or "").strip()
    if not raw.isdigit():
        await update.message.reply_text("Нужно число от 0 до 100.")
        return WAIT_INTENSITY_BEFORE

    value = int(raw)
    if value < 0 or value > 100:
        await update.message.reply_text("Только диапазон 0–100.")
        return WAIT_INTENSITY_BEFORE

    draft = context.user_data.get("draft_entry")
    if not draft or not draft.get("thought_text"):
        await update.message.reply_text("Черновик не найден. Нажми «Новая мысль» и начни заново.")
        return ConversationHandler.END

    draft["intensity_before"] = value
    context.user_data["draft_entry"] = draft

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO entries (tg_user_id, thought_text, emotion_label, intensity_before)
        VALUES (?, ?, ?, ?)
        """,
        (
            update.effective_user.id,
            draft.get("thought_text"),
            draft.get("emotion_label"),
            draft.get("intensity_before"),
        ),
    )
    entry_id = cur.lastrowid
    conn.commit()
    conn.close()

    draft["entry_id"] = entry_id
    context.user_data["draft_entry"] = draft

    distortion_keyboard = ReplyKeyboardMarkup(
        [
            ["Катастрофизация", "Чтение мыслей"],
            ["Черно-белое мышление", "Обесценивание позитивного"],
            ["Сверхобобщение", "Персонализация"],
            ["Эмоц. обоснование", "Долженствование"],
            ["Навешивание ярлыков", "Предсказание будущего"],
            ["Другое"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(EMOTION_STEP_DONE_RU)
    await update.message.reply_text(DISTORTION_PROMPT_RU, reply_markup=distortion_keyboard)
    return WAIT_DISTORTION


async def receive_distortion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    distortion = (update.message.text or "").strip()
    if not distortion:
        await update.message.reply_text("Выбери искажение кнопкой или введи текстом.")
        return WAIT_DISTORTION

    draft = context.user_data.get("draft_entry", {})
    entry_id = draft.get("entry_id")
    if not entry_id:
        await update.message.reply_text("Не нашла активную запись. Нажми «Новая мысль» и начни заново.")
        return ConversationHandler.END

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE entries SET distortion = ? WHERE id = ?", (distortion, entry_id))
    conn.commit()
    conn.close()

    draft["distortion"] = distortion
    context.user_data["draft_entry"] = draft

    await update.message.reply_text(DISTORTION_SAVED_RU)
    return ConversationHandler.END
