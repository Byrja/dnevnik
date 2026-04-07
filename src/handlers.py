from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from db import get_conn
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
from texts import (
    ALTERNATIVE_PROMPT_RU,
    CARD_DONE_TEMPLATE_RU,
    DISCLAIMER_RU,
    DISTORTION_PROMPT_RU,
    DISTORTION_SAVED_RU,
    EMOTION_PROMPT_RU,
    EMOTION_SAVED_RU,
    EMOTION_STEP_DONE_RU,
    EVIDENCE_AGAINST_PROMPT_RU,
    EVIDENCE_FOR_PROMPT_RU,
    EVIDENCE_STEP_DONE_RU,
    INTENSITY_AFTER_PROMPT_RU,
    INTENSITY_PROMPT_RU,
    MENU_RU,
    SETTINGS_PROMPT_RU,
    SETTINGS_SAVED_TEMPLATE_RU,
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


def _get_tone(tg_user_id: int) -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT tone FROM settings WHERE tg_user_id = ?", (tg_user_id,))
    row = cur.fetchone()
    conn.close()
    return (row[0] if row else "warm") or "warm"


def _tone_text(tone: str, key: str) -> str:
    tone_map = {
        "thought_prompt": {
            "warm": THOUGHT_PROMPT_RU,
            "neutral": "Введите исходную мысль (1–2 предложения).",
        },
        "thought_saved": {
            "warm": THOUGHT_SAVED_RU,
            "neutral": "Мысль сохранена. Выберите эмоцию.",
        },
    }
    return tone_map.get(key, {}).get(tone, tone_map.get(key, {}).get("warm", ""))


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


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Тёплый", callback_data="tone:warm")],
            [InlineKeyboardButton("Нейтральный", callback_data="tone:neutral")],
        ]
    )
    await update.message.reply_text(SETTINGS_PROMPT_RU, reply_markup=kb)


async def set_tone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not update.effective_user:
        return
    await query.answer()

    _, tone = (query.data or "tone:warm").split(":", 1)
    if tone not in {"warm", "neutral"}:
        tone = "warm"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE settings SET tone = ?, updated_at = CURRENT_TIMESTAMP WHERE tg_user_id = ?",
        (tone, update.effective_user.id),
    )
    conn.commit()
    conn.close()

    label = "тёплый" if tone == "warm" else "нейтральный"
    await query.edit_message_text(SETTINGS_SAVED_TEMPLATE_RU.format(tone_label=label))


async def new_thought_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    tone = _get_tone(update.effective_user.id)
    await update.message.reply_text(_tone_text(tone, "thought_prompt"))
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
    tone = _get_tone(update.effective_user.id)
    await update.message.reply_text(_tone_text(tone, "thought_saved"))
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
    await update.message.reply_text(EVIDENCE_FOR_PROMPT_RU)
    return WAIT_EVIDENCE_FOR


async def receive_evidence_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    evidence_for = (update.message.text or "").strip()
    if len(evidence_for) < 3:
        await update.message.reply_text("Слишком коротко. Напиши хотя бы 3 символа.")
        return WAIT_EVIDENCE_FOR

    draft = context.user_data.get("draft_entry", {})
    entry_id = draft.get("entry_id")
    if not entry_id:
        await update.message.reply_text("Не нашла активную запись. Нажми «Новая мысль» и начни заново.")
        return ConversationHandler.END

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE entries SET evidence_for = ? WHERE id = ?", (evidence_for, entry_id))
    conn.commit()
    conn.close()

    draft["evidence_for"] = evidence_for
    context.user_data["draft_entry"] = draft

    await update.message.reply_text(EVIDENCE_AGAINST_PROMPT_RU)
    return WAIT_EVIDENCE_AGAINST


async def receive_evidence_against(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    evidence_against = (update.message.text or "").strip()
    if len(evidence_against) < 3:
        await update.message.reply_text("Слишком коротко. Напиши хотя бы 3 символа.")
        return WAIT_EVIDENCE_AGAINST

    draft = context.user_data.get("draft_entry", {})
    entry_id = draft.get("entry_id")
    if not entry_id:
        await update.message.reply_text("Не нашла активную запись. Нажми «Новая мысль» и начни заново.")
        return ConversationHandler.END

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE entries SET evidence_against = ? WHERE id = ?", (evidence_against, entry_id))
    conn.commit()
    conn.close()

    draft["evidence_against"] = evidence_against
    context.user_data["draft_entry"] = draft

    await update.message.reply_text(EVIDENCE_STEP_DONE_RU)
    await update.message.reply_text(ALTERNATIVE_PROMPT_RU)
    return WAIT_ALTERNATIVE_THOUGHT


async def receive_alternative_thought(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    alt = (update.message.text or "").strip()
    if len(alt) < 3:
        await update.message.reply_text("Слишком коротко. Напиши хотя бы 3 символа.")
        return WAIT_ALTERNATIVE_THOUGHT

    draft = context.user_data.get("draft_entry", {})
    entry_id = draft.get("entry_id")
    if not entry_id:
        await update.message.reply_text("Не нашла активную запись. Нажми «Новая мысль» и начни заново.")
        return ConversationHandler.END

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE entries SET alternative_thought = ? WHERE id = ?", (alt, entry_id))
    conn.commit()
    conn.close()

    draft["alternative_thought"] = alt
    context.user_data["draft_entry"] = draft

    await update.message.reply_text(INTENSITY_AFTER_PROMPT_RU)
    return WAIT_INTENSITY_AFTER


async def receive_intensity_after(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    raw = (update.message.text or "").strip()
    if not raw.isdigit():
        await update.message.reply_text("Нужно число от 0 до 100.")
        return WAIT_INTENSITY_AFTER

    after = int(raw)
    if after < 0 or after > 100:
        await update.message.reply_text("Только диапазон 0–100.")
        return WAIT_INTENSITY_AFTER

    draft = context.user_data.get("draft_entry", {})
    entry_id = draft.get("entry_id")
    if not entry_id:
        await update.message.reply_text("Не нашла активную запись. Нажми «Новая мысль» и начни заново.")
        return ConversationHandler.END

    before = int(draft.get("intensity_before", 0))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE entries SET intensity_after = ? WHERE id = ?", (after, entry_id))
    conn.commit()
    conn.close()

    delta = before - after
    await update.message.reply_text(
        CARD_DONE_TEMPLATE_RU.format(before=before, after=after, delta=delta)
    )

    context.user_data.pop("draft_entry", None)
    return ConversationHandler.END


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT created_at, thought_text, emotion_label, intensity_before, intensity_after
        FROM entries
        WHERE tg_user_id = ?
        ORDER BY id DESC
        LIMIT 10
        """,
        (update.effective_user.id,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Пока нет завершённых карточек. Нажми «Новая мысль» и сделай первый разбор.")
        return

    lines = ["🗂 Последние 10 карточек:"]
    for i, r in enumerate(rows, 1):
        thought = (r[1] or "").replace("\n", " ").strip()
        if len(thought) > 48:
            thought = thought[:48] + "…"
        emo = r[2] or "—"
        before = r[3] if r[3] is not None else "—"
        after = r[4] if r[4] is not None else "—"
        delta = "—"
        if isinstance(before, int) and isinstance(after, int):
            delta = before - after
        lines.append(f"{i}) {emo} | {before}→{after} | Δ {delta} | {thought}")

    await update.message.reply_text("\n".join(lines))
