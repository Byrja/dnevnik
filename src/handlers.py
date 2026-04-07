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
    ALTERNATIVE_HINT_PROMPT_RU,
    ALTERNATIVE_PROMPT_RU,
    CANCEL_HINT_RU,
    CARD_DONE_TEMPLATE_RU,
    CRISIS_SUPPORT_RU,
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
    EXPORT_USAGE_RU,
    MENU_RU,
    ONBOARDING_1_RU,
    ONBOARDING_2_RU,
    ONBOARDING_3_RU,
    REMINDER_NUDGE_RU,
    REMINDER_STATE_TEMPLATE_RU,
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


def _contains_crisis_signal(text: str) -> bool:
    s = (text or "").lower()
    markers = [
        "хочу умер",
        "не хочу жить",
        "поконч",
        "суиц",
        "причинить себе вред",
        "навредить себе",
        "убить себя",
        "умереть",
    ]
    return any(m in s for m in markers)


async def _handle_crisis(update: Update, context: ContextTypes.DEFAULT_TYPE, source_text: str) -> int:
    if update.effective_user:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO entries (tg_user_id, thought_text, emotion_label)
            VALUES (?, ?, ?)
            """,
            (update.effective_user.id, source_text[:500], "CRISIS_SIGNAL"),
        )
        conn.commit()
        conn.close()

    context.user_data.pop("draft_entry", None)
    if update.message:
        await update.message.reply_text(CRISIS_SUPPORT_RU)
    return ConversationHandler.END


async def _send_main_menu(msg) -> None:
    keyboard = ReplyKeyboardMarkup(
        [["Новая мысль", "История"], ["Настройки"]],
        resize_keyboard=True,
    )
    await msg.reply_text(MENU_RU, reply_markup=keyboard)


async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        context.user_data.pop("draft_entry", None)
        await update.message.reply_text("Ок, остановила текущий разбор.")
        await _send_main_menu(update.message)
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    if _user_exists(user.id):
        await update.message.reply_text(START_RU)
        await _send_main_menu(update.message)
        return

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Согласен", callback_data="consent_accept")]]
    )
    await update.message.reply_text(DISCLAIMER_RU, reply_markup=keyboard)


async def _send_onboarding(chat_message) -> None:
    await chat_message.reply_text(ONBOARDING_1_RU)
    await chat_message.reply_text(ONBOARDING_2_RU)
    await chat_message.reply_text(ONBOARDING_3_RU)


async def consent_accept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    _save_user_with_default_settings(update)

    await query.edit_message_text("✅ Согласие сохранено.")
    await query.message.reply_text(START_RU)
    await _send_onboarding(query.message)
    await _send_main_menu(query.message)


async def show_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await _send_onboarding(update.message)


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


async def set_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    args = context.args or []
    conn = get_conn()
    cur = conn.cursor()

    if args and args[0].lower() in {"on", "off"}:
        enabled = 1 if args[0].lower() == "on" else 0
        cur.execute(
            "UPDATE settings SET reminders_enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE tg_user_id = ?",
            (enabled, update.effective_user.id),
        )
        conn.commit()

    cur.execute("SELECT reminders_enabled FROM settings WHERE tg_user_id = ?", (update.effective_user.id,))
    row = cur.fetchone()
    conn.close()

    state = "ON" if (row and int(row[0]) == 1) else "OFF"
    await update.message.reply_text(REMINDER_STATE_TEMPLATE_RU.format(state=state))


async def send_daily_nudges(context: ContextTypes.DEFAULT_TYPE) -> None:
    app = context.application
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.tg_user_id
        FROM settings s
        WHERE COALESCE(s.reminders_enabled, 1) = 1
          AND NOT EXISTS (
              SELECT 1 FROM entries e
              WHERE e.tg_user_id = s.tg_user_id
                AND datetime(e.created_at) >= datetime('now', '-24 hours')
          )
        """
    )
    users = [r[0] for r in cur.fetchall()]
    conn.close()

    for tg_user_id in users:
        try:
            await app.bot.send_message(chat_id=tg_user_id, text=REMINDER_NUDGE_RU)
        except Exception:
            continue


async def export_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    fmt = (context.args[0].lower() if context.args else "").strip()
    if fmt not in {"txt", "json"}:
        await update.message.reply_text(EXPORT_USAGE_RU)
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT created_at, thought_text, emotion_label, intensity_before, distortion,
               evidence_for, evidence_against, alternative_thought, intensity_after
        FROM entries
        WHERE tg_user_id = ?
        ORDER BY id DESC
        LIMIT 200
        """,
        (update.effective_user.id,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Нет данных для экспорта.")
        return

    from io import BytesIO
    import json

    if fmt == "json":
        payload = []
        for r in rows:
            payload.append(
                {
                    "created_at": r[0],
                    "thought_text": r[1],
                    "emotion_label": r[2],
                    "intensity_before": r[3],
                    "distortion": r[4],
                    "evidence_for": r[5],
                    "evidence_against": r[6],
                    "alternative_thought": r[7],
                    "intensity_after": r[8],
                }
            )
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        bio = BytesIO(data)
        bio.name = "clarity_export.json"
        await update.message.reply_document(document=bio, filename="clarity_export.json")
        return

    lines = ["Clarity export (txt)"]
    for i, r in enumerate(rows, 1):
        delta = "—"
        if isinstance(r[3], int) and isinstance(r[8], int):
            delta = r[3] - r[8]
        lines.append(
            f"\n[{i}] {r[0]}\n"
            f"Мысль: {r[1] or '—'}\n"
            f"Эмоция: {r[2] or '—'}\n"
            f"До/После: {r[3] if r[3] is not None else '—'}/{r[8] if r[8] is not None else '—'} (Δ {delta})\n"
            f"Искажение: {r[4] or '—'}\n"
            f"За: {r[5] or '—'}\n"
            f"Против: {r[6] or '—'}\n"
            f"Альтернатива: {r[7] or '—'}"
        )

    data = "\n".join(lines).encode("utf-8")
    bio = BytesIO(data)
    bio.name = "clarity_export.txt"
    await update.message.reply_document(document=bio, filename="clarity_export.txt")


async def new_thought_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    tone = _get_tone(update.effective_user.id)
    await update.message.reply_text(f"Шаг 1/8\n{_tone_text(tone, 'thought_prompt')}\n\n{CANCEL_HINT_RU}")
    return WAIT_THOUGHT


async def receive_thought_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.effective_user:
        return ConversationHandler.END

    thought_text = (update.message.text or "").strip()
    if _contains_crisis_signal(thought_text):
        return await _handle_crisis(update, context, thought_text)
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
    await update.message.reply_text(f"Шаг 2/8\n{EMOTION_PROMPT_RU}", reply_markup=emotion_keyboard)
    return WAIT_EMOTION


async def receive_emotion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END
    emotion = (update.message.text or "").strip()
    if _contains_crisis_signal(emotion):
        return await _handle_crisis(update, context, emotion)
    if not emotion:
        await update.message.reply_text("Выбери эмоцию кнопкой или введи текстом.")
        return WAIT_EMOTION

    draft = context.user_data.get("draft_entry", {})
    draft["emotion_label"] = emotion
    context.user_data["draft_entry"] = draft

    await update.message.reply_text(EMOTION_SAVED_RU)
    await update.message.reply_text(f"Шаг 3/8\n{INTENSITY_PROMPT_RU}")
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
    await update.message.reply_text(f"Шаг 4/8\n{DISTORTION_PROMPT_RU}", reply_markup=distortion_keyboard)
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
    await update.message.reply_text(f"Шаг 5/8\n{EVIDENCE_FOR_PROMPT_RU}")
    return WAIT_EVIDENCE_FOR


async def receive_evidence_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    evidence_for = (update.message.text or "").strip()
    if _contains_crisis_signal(evidence_for):
        return await _handle_crisis(update, context, evidence_for)
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

    await update.message.reply_text(f"Шаг 6/8\n{EVIDENCE_AGAINST_PROMPT_RU}")
    return WAIT_EVIDENCE_AGAINST


def _alternative_hint_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Что бы я сказал другу?", callback_data="alt_hint:friend")],
            [InlineKeyboardButton("Факты против страха", callback_data="alt_hint:facts")],
            [InlineKeyboardButton("Мягкая реалистичная версия", callback_data="alt_hint:balanced")],
        ]
    )


def _alternative_hint_text(kind: str, thought: str) -> str:
    thought = (thought or "эту мысль").strip()
    if kind == "friend":
        return f"Если бы друг сказал: «{thought}», я бы ответил: «Ты не обязан верить первой тревожной мысли. Давай опираться на факты и на то, что реально в твоём контроле прямо сейчас»."
    if kind == "facts":
        return "Проверь: какие 2–3 факта прямо сейчас не подтверждают худший сценарий? Собери их и сформулируй более точную мысль."
    return "Более реалистичная формулировка: «Да, сейчас мне непросто. Но это временно, и у меня есть шаги, которые помогут стабилизироваться»."


async def receive_evidence_against(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    evidence_against = (update.message.text or "").strip()
    if _contains_crisis_signal(evidence_against):
        return await _handle_crisis(update, context, evidence_against)
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
    await update.message.reply_text(f"Шаг 7/8\n{ALTERNATIVE_PROMPT_RU}")
    await update.message.reply_text(ALTERNATIVE_HINT_PROMPT_RU, reply_markup=_alternative_hint_keyboard())
    return WAIT_ALTERNATIVE_THOUGHT


def _next_step_recommendation(delta: int, after: int, distortion: str) -> str:
    d = (distortion or "").lower()
    if after >= 75:
        return "Сделай паузу 10 минут: вода + дыхание 4-6 + короткая прогулка. Потом повтори карточку ещё раз."
    if "катастроф" in d or "предсказ" in d:
        return "Проверь прогноз: выпиши 3 факта, которые НЕ подтверждают худший сценарий."
    if "должен" in d:
        return "Замени «я должен» на «я выбираю/могу» и сформулируй более мягкий стандарт к себе."
    if delta >= 25:
        return "Отличная динамика. Зафиксируй формулировку альтернативной мысли и вернись к ней вечером."
    if delta >= 10:
        return "Хороший сдвиг. Повтори цикл позже сегодня, если накал снова вырастет."
    return "Сдвиг пока небольшой — это нормально. Попробуй конкретизировать факты «за/против» и сделать второй проход."


async def _finalize_with_after_intensity(update: Update, context: ContextTypes.DEFAULT_TYPE, after: int) -> int:
    draft = context.user_data.get("draft_entry", {})
    entry_id = draft.get("entry_id")
    if not entry_id:
        return ConversationHandler.END

    before = int(draft.get("intensity_before", 0))
    distortion = draft.get("distortion", "")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE entries SET intensity_after = ? WHERE id = ?", (after, entry_id))
    conn.commit()
    conn.close()

    delta = before - after
    next_step = _next_step_recommendation(delta=delta, after=after, distortion=distortion)
    if update.message:
        await update.message.reply_text(
            CARD_DONE_TEMPLATE_RU.format(before=before, after=after, delta=delta, next_step=next_step)
        )

    context.user_data.pop("draft_entry", None)
    return ConversationHandler.END


async def receive_alternative_thought(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    alt = (update.message.text or "").strip()
    if _contains_crisis_signal(alt):
        return await _handle_crisis(update, context, alt)

    draft = context.user_data.get("draft_entry", {})
    # Если подсказка уже вставила альтернативную мысль, пользователь может сразу ввести число 0-100
    if alt.isdigit() and draft.get("alternative_thought"):
        value = int(alt)
        if 0 <= value <= 100:
            return await _finalize_with_after_intensity(update, context, value)

    if len(alt) < 3:
        await update.message.reply_text("Слишком коротко. Напиши хотя бы 3 символа.")
        return WAIT_ALTERNATIVE_THOUGHT

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

    await update.message.reply_text(f"Шаг 8/8\n{INTENSITY_AFTER_PROMPT_RU}")
    return WAIT_INTENSITY_AFTER


async def apply_alternative_hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    draft = context.user_data.get("draft_entry", {})
    thought = draft.get("thought_text", "")
    kind = (query.data or "alt_hint:balanced").split(":", 1)[1]
    hint_text = _alternative_hint_text(kind, thought)

    entry_id = draft.get("entry_id")
    if not entry_id:
        await query.message.reply_text("Не нашла активную запись. Нажми «Новая мысль» и начни заново.")
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE entries SET alternative_thought = ? WHERE id = ?", (hint_text, entry_id))
    conn.commit()
    conn.close()

    draft["alternative_thought"] = hint_text
    context.user_data["draft_entry"] = draft

    await query.message.reply_text(f"Подсказка:\n{hint_text}")
    await query.message.reply_text(f"Шаг 8/8\n{INTENSITY_AFTER_PROMPT_RU}")


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

    return await _finalize_with_after_intensity(update, context, after)


def _parse_history_filters(text: str) -> tuple[str | None, str | None, int]:
    # Примеры:
    # /history
    # /history emotion=Тревога
    # /history distortion=Катастрофизация days=7
    # /history emotion=Тревога distortion=Чтение_мыслей days=30
    emotion = None
    distortion = None
    days = 30
    for part in (text or "").split()[1:]:
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        v = v.replace("_", " ").strip()
        if k == "emotion" and v:
            emotion = v
        elif k == "distortion" and v:
            distortion = v
        elif k == "days" and v.isdigit():
            days = max(1, min(365, int(v)))
    return emotion, distortion, days


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    emotion, distortion, days = _parse_history_filters(update.message.text or "")

    query = (
        """
        SELECT created_at, thought_text, emotion_label, intensity_before, intensity_after, distortion
        FROM entries
        WHERE tg_user_id = ?
          AND datetime(created_at) >= datetime('now', ?)
        """
    )
    params = [update.effective_user.id, f"-{days} days"]

    if emotion:
        query += " AND emotion_label = ?"
        params.append(emotion)
    if distortion:
        query += " AND distortion = ?"
        params.append(distortion)

    query += " ORDER BY id DESC LIMIT 10"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("По этому фильтру записей нет. Попробуй /history или увеличь days=.")
        return

    filter_line = f"Фильтр: days={days}"
    if emotion:
        filter_line += f", emotion={emotion}"
    if distortion:
        filter_line += f", distortion={distortion}"

    lines = ["🗂 Последние 10 карточек:", filter_line]
    for i, r in enumerate(rows, 1):
        thought = (r[1] or "").replace("\n", " ").strip()
        if len(thought) > 48:
            thought = thought[:48] + "…"
        emo = r[2] or "—"
        before = r[3] if r[3] is not None else "—"
        after = r[4] if r[4] is not None else "—"
        dist = r[5] or "—"
        delta = "—"
        if isinstance(before, int) and isinstance(after, int):
            delta = before - after
        lines.append(f"{i}) {emo} | {before}→{after} | Δ {delta} | {dist} | {thought}")

    lines.append("\nПримеры: /history emotion=Тревога | /history distortion=Катастрофизация days=7")
    await update.message.reply_text("\n".join(lines))
