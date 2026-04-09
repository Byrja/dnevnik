import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from db import get_conn
from logger import log_error, log_update
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
    HELP_RU,
    INTENSITY_AFTER_PROMPT_RU,
    INTENSITY_PROMPT_RU,
    EXPORT_USAGE_RU,
    HISTORY_EMPTY_RU,
    HISTORY_FILTER_HINT_RU,
    MENU_RU,
    ONBOARDING_1_RU,
    ONBOARDING_2_RU,
    ONBOARDING_3_RU,
    REMINDER_NUDGE_RU,
    REMINDER_STATE_TEMPLATE_RU,
    SESSION_TIMEOUT_NUDGE_RU,
    SETTINGS_PROMPT_RU,
    SETTINGS_SAVED_TEMPLATE_RU,
    START_RU,
    STATS_EMPTY_RU,
    STATS_RU,
    THOUGHT_PROMPT_RU,
    THOUGHT_SAVED_RU,
    _format_result,
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


DISTORTION_LABEL_TO_CODE = {
    "Катастрофизация": "catastrophizing",
    "Чтение мыслей": "mind_reading",
    "Черно-белое мышление": "black_white",
    "Обесценивание позитивного": "discounting_positive",
    "Сверхобобщение": "overgeneralization",
    "Персонализация": "personalization",
    "Эмоц. обоснование": "emotional_reasoning",
    "Долженствование": "should_statements",
    "Навешивание ярлыков": "labeling",
    "Предсказание будущего": "fortune_telling",
    "Другое": "other",
}

DISTORTION_EXPLAIN = {
    "Катастрофизация": "ожидаю самый худший исход как неизбежный",
    "Чтение мыслей": "уверен, что знаю, что другие думают обо мне",
    "Черно-белое мышление": "вижу только крайности: либо успех, либо провал",
    "Обесценивание позитивного": "игнорирую всё хорошее как «не считается»",
    "Сверхобобщение": "по одному случаю делаю вывод «всегда/никогда»",
    "Персонализация": "беру на себя лишнюю ответственность за всё вокруг",
    "Эмоц. обоснование": "если чувствую страх, значит опасность точно реальна",
    "Долженствование": "жёсткие «я должен/должна», без права на ошибку",
    "Навешивание ярлыков": "вместо фактов клею общий негативный ярлык",
    "Предсказание будущего": "уверен, что всё пойдёт плохо заранее",
}

DISTORTION_DETAILS = {
    "catastrophizing": "Катастрофизация\n\nКак выглядит: «если что-то пойдёт не так — это катастрофа».\nЧем вредит: резко поднимает тревогу и блокирует действие.\nКак проверить: выпиши 3 более вероятных исхода, не только худший.",
    "mind_reading": "Чтение мыслей\n\nКак выглядит: «они точно думают, что я слабый/глупый».\nЧем вредит: заставляет реагировать на догадки, а не факты.\nКак проверить: какие реальные данные у меня есть, кроме предположений?",
    "black_white": "Черно-белое мышление\n\nКак выглядит: «или идеально, или провал».\nЧем вредит: обесценивает нормальный прогресс.\nКак проверить: где шкала 0–100, а не только 0/100?",
    "discounting_positive": "Обесценивание позитивного\n\nКак выглядит: «да, получилось, но это случайно/не считается».\nЧем вредит: мозг не фиксирует опоры и успехи.\nКак проверить: что конкретно получилось благодаря моим действиям?",
    "overgeneralization": "Сверхобобщение\n\nКак выглядит: «один раз не вышло — значит всегда так».\nЧем вредит: делает будущее заранее проигранным.\nКак проверить: есть ли примеры, где было иначе?",
    "personalization": "Персонализация\n\nКак выглядит: «это всё из-за меня», даже если факторов много.\nЧем вредит: лишняя вина и выгорание.\nКак проверить: что в зоне моей ответственности, а что нет?",
    "emotional_reasoning": "Эмоциональное обоснование\n\nКак выглядит: «мне страшно, значит это точно опасно».\nЧем вредит: эмоция подменяет факт.\nКак проверить: какие есть внешние подтверждения, кроме чувства?",
    "should_statements": "Долженствование\n\nКак выглядит: «я должен быть идеальным, всегда справляться».\nЧем вредит: жёсткость к себе, вина и злость.\nКак проверить: заменяю «должен» на «предпочитаю/могу/выбираю».",
    "labeling": "Навешивание ярлыков\n\nКак выглядит: «я неудачник», вместо описания ситуации.\nЧем вредит: фиксирует негативную идентичность.\nКак проверить: описать конкретный поступок, а не клеймо на себя целиком.",
    "fortune_telling": "Предсказание будущего\n\nКак выглядит: «всё равно будет плохо».\nЧем вредит: лишает мотивации пробовать.\nКак проверить: какие факты подтверждают прогноз, а какие — нет?",
    "other": "Другое\n\nЕсли не нашёл точное совпадение, выбери ближайший вариант и иди дальше — это нормально. Главное, чтобы формулировка помогала действовать.",
}

CODE_TO_DISTORTION_LABEL = {v: k for k, v in DISTORTION_LABEL_TO_CODE.items()}


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


def _is_too_vague(text: str) -> bool:
    s = (text or "").strip().lower()
    vague = {
        "не знаю",
        "всё плохо",
        "плохо",
        "сложно",
        "никак",
        "норм",
        "нормально",
        "тяжело",
        "устал",
    }
    if s in vague:
        return True
    return len(s) < 10


async def _handle_crisis(update: Update, context: ContextTypes.DEFAULT_TYPE, source_text: str) -> int:
    if update.effective_user:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO entries (tg_user_id, thought_text, emotion_label, is_completed, completed_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            """,
            (update.effective_user.id, source_text[:500], "CRISIS_SIGNAL"),
        )
        conn.commit()
        conn.close()

    context.user_data.pop("draft_entry", None)
    if update.message:
        await update.message.reply_text(CRISIS_SUPPORT_RU)
    return ConversationHandler.END


def _main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["🎯 Новая мысль", "📜 История"], ["⚙️ Настройки"]],
        resize_keyboard=True,
    )


def _main_menu_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Новая мысль", callback_data="menu:new")],
        [InlineKeyboardButton("📜 История", callback_data="menu:history"), InlineKeyboardButton("📊 Статистика", callback_data="menu:stats")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="menu:settings"), InlineKeyboardButton("❓ Помощь", callback_data="menu:help")],
    ])


def _distortion_choice_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["Катастрофизация", "Чтение мыслей"],
            ["Черно-белое мышление", "Обесценивание позитивного"],
            ["Сверхобобщение", "Персонализация"],
            ["Эмоц. обоснование", "Долженствование"],
            ["Навешивание ярлыков", "Предсказание будущего"],
            ["Не уверен", "Другое"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _flow_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["В меню"]],
        resize_keyboard=True,
    )


def _distortion_info_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("Катастрофизация", callback_data="dist_info:catastrophizing")],
        [InlineKeyboardButton("Чтение мыслей", callback_data="dist_info:mind_reading")],
        [InlineKeyboardButton("Черно-белое мышление", callback_data="dist_info:black_white")],
        [InlineKeyboardButton("Обесценивание позитивного", callback_data="dist_info:discounting_positive")],
        [InlineKeyboardButton("Сверхобобщение", callback_data="dist_info:overgeneralization")],
        [InlineKeyboardButton("Персонализация", callback_data="dist_info:personalization")],
        [InlineKeyboardButton("Эмоц. обоснование", callback_data="dist_info:emotional_reasoning")],
        [InlineKeyboardButton("Долженствование", callback_data="dist_info:should_statements")],
        [InlineKeyboardButton("Навешивание ярлыков", callback_data="dist_info:labeling")],
        [InlineKeyboardButton("Предсказание будущего", callback_data="dist_info:fortune_telling")],
        [InlineKeyboardButton("Другое", callback_data="dist_info:other")],
        [InlineKeyboardButton("⬅️ Назад к выбору", callback_data="dist_info:back")],
    ]
    return InlineKeyboardMarkup(rows)


def _distortion_detail_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Выбрать это искажение", callback_data=f"dist_pick:{code}")],
            [InlineKeyboardButton("⬅️ Назад к выбору", callback_data="dist_info:back")],
        ]
    )


def _intensity_quick_keyboard(kind: str) -> InlineKeyboardMarkup:
    prefix = "int_before" if kind == "before" else "int_after"
    values = [20, 40, 60, 80, 100]
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(str(v), callback_data=f"{prefix}:{v}") for v in values]]
    )


async def _send_main_menu(msg) -> None:
    await msg.reply_text(MENU_RU, reply_markup=_main_menu_inline())


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
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    if not msg:
        return
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Тёплый", callback_data="tone:warm")],
            [InlineKeyboardButton("Нейтральный", callback_data="tone:neutral")],
        ]
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(SETTINGS_PROMPT_RU, reply_markup=kb)
    else:
        await msg.reply_text(SETTINGS_PROMPT_RU, reply_markup=kb)


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


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help message with all commands."""
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    if not msg:
        return
    if update.callback_query:
        await update.callback_query.edit_message_text(HELP_RU, parse_mode=None)
    else:
        await msg.reply_text(HELP_RU, parse_mode=None)


async def main_menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    action = (query.data or "").split(":", 1)[-1]
    msg = query.message
    if not msg:
        return

    if action == "new":
        await new_thought_entry(update, context)
    elif action == "history":
        await show_history(update, context)
    elif action == "stats":
        await show_stats(update, context)
    elif action == "settings":
        await show_settings(update, context)
    elif action == "help":
        await show_help(update, context)


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user statistics."""
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    if not msg or not update.effective_user:
        return

    user_id = update.effective_user.id

    conn = get_conn()
    cur = conn.cursor()

    # Total cards
    cur.execute("SELECT COUNT(*) FROM entries WHERE tg_user_id = ? AND is_completed = 1", (user_id,))
    total = cur.fetchone()[0] or 0

    if total == 0:
        conn.close()
        if update.callback_query:
            await update.callback_query.edit_message_text(STATS_EMPTY_RU)
        else:
            await msg.reply_text(STATS_EMPTY_RU)
        return

    # Cards in last 7 days
    cur.execute(
        "SELECT COUNT(*) FROM entries WHERE tg_user_id = ? AND is_completed = 1 AND datetime(COALESCE(completed_at, created_at)) >= datetime('now', '-7 days')",
        (user_id,),
    )
    week = cur.fetchone()[0] or 0

    # Cards in last 30 days
    cur.execute(
        "SELECT COUNT(*) FROM entries WHERE tg_user_id = ? AND is_completed = 1 AND datetime(COALESCE(completed_at, created_at)) >= datetime('now', '-30 days')",
        (user_id,),
    )
    month = cur.fetchone()[0] or 0

    # Average delta
    cur.execute(
        "SELECT AVG(intensity_before - intensity_after) FROM entries WHERE tg_user_id = ? AND is_completed = 1 AND intensity_before IS NOT NULL AND intensity_after IS NOT NULL",
        (user_id,),
    )
    avg_row = cur.fetchone()[0]
    avg_delta = f"{avg_row:.1f}" if avg_row else "—"

    # Calculate streak (consecutive days with completed cards)
    cur.execute(
        "SELECT DISTINCT date(COALESCE(completed_at, created_at)) as day FROM entries WHERE tg_user_id = ? AND is_completed = 1 ORDER BY day DESC",
        (user_id,),
    )
    days = [r[0] for r in cur.fetchall()]

    streak = 0
    if days:
        from datetime import datetime, timedelta
        today = datetime.now().date()
        expected = today
        for d in days:
            day_date = datetime.strptime(d, "%Y-%m-%d").date()
            if day_date == expected or day_date == expected - timedelta(days=1):
                streak += 1
                expected = day_date - timedelta(days=1)
            else:
                break

    # Top emotions
    cur.execute(
        "SELECT emotion_label, COUNT(*) as cnt FROM entries WHERE tg_user_id = ? AND is_completed = 1 AND emotion_label IS NOT NULL AND emotion_label != 'CRISIS_SIGNAL' GROUP BY emotion_label ORDER BY cnt DESC LIMIT 5",
        (user_id,),
    )
    top_emotions = [f"  • {r[0]}: {r[1]}" for r in cur.fetchall()]
    top_emotions_str = "\n".join(top_emotions) if top_emotions else "  Пока нет данных"

    conn.close()

    # Build message
    emoji = "⭐" if streak >= 3 else "💡"
    stats_text = STATS_RU.format(
        emoji=emoji,
        total=total,
        week=week,
        month=month,
        avg_delta=avg_delta,
        streak=streak,
        top_emotions=top_emotions_str,
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(stats_text)
    else:
        await msg.reply_text(stats_text)


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
          AND (s.last_nudge_at IS NULL OR datetime(s.last_nudge_at) <= datetime('now', '-20 hours'))
          AND NOT EXISTS (
              SELECT 1 FROM entries e
              WHERE e.tg_user_id = s.tg_user_id
                AND e.is_completed = 1
                AND datetime(COALESCE(e.completed_at, e.created_at)) >= datetime('now', '-24 hours')
          )
        """
    )
    users = [r[0] for r in cur.fetchall()]
    conn.close()

    for tg_user_id in users:
        try:
            await app.bot.send_message(chat_id=tg_user_id, text=REMINDER_NUDGE_RU)
            conn2 = get_conn()
            cur2 = conn2.cursor()
            cur2.execute(
                "UPDATE settings SET last_nudge_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE tg_user_id = ?",
                (tg_user_id,),
            )
            conn2.commit()
            conn2.close()
        except Exception as e:
            logging.error(f"send_daily_nudges | Failed to send nudge to user={tg_user_id}: {e}")


async def send_session_timeout_nudges(context: ContextTypes.DEFAULT_TYPE) -> None:
    app = context.application
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT e.id, e.tg_user_id
        FROM entries e
        JOIN settings s ON s.tg_user_id = e.tg_user_id
        WHERE e.is_completed = 0
          AND COALESCE(s.reminders_enabled, 1) = 1
          AND datetime(e.created_at) <= datetime('now', '-45 minutes')
          AND (e.timeout_nudged_at IS NULL OR datetime(e.timeout_nudged_at) <= datetime('now', '-12 hours'))
        ORDER BY e.id DESC
        LIMIT 200
        """
    )
    rows = cur.fetchall()
    conn.close()

    for row in rows:
        entry_id, tg_user_id = row[0], row[1]
        try:
            await app.bot.send_message(chat_id=tg_user_id, text=SESSION_TIMEOUT_NUDGE_RU)
            conn2 = get_conn()
            cur2 = conn2.cursor()
            cur2.execute(
                "UPDATE entries SET timeout_nudged_at = CURRENT_TIMESTAMP WHERE id = ?",
                (entry_id,),
            )
            conn2.commit()
            conn2.close()
        except Exception as e:
            logging.error(f"send_session_timeout_nudges | user={tg_user_id} entry={entry_id}: {e}")


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
        SELECT created_at, thought_text, emotion_label, intensity_before, distortion, distortion_code,
               evidence_for, evidence_against, alternative_thought, intensity_after
        FROM entries
        WHERE tg_user_id = ?
          AND is_completed = 1
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
                    "distortion_code": r[5],
                    "evidence_for": r[6],
                    "evidence_against": r[7],
                    "alternative_thought": r[8],
                    "intensity_after": r[9],
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
        if isinstance(r[3], int) and isinstance(r[9], int):
            delta = r[3] - r[9]
        lines.append(
            f"\n[{i}] {r[0]}\n"
            f"Мысль: {r[1] or '—'}\n"
            f"Эмоция: {r[2] or '—'}\n"
            f"До/После: {r[3] if r[3] is not None else '—'}/{r[9] if r[9] is not None else '—'} (Δ {delta})\n"
            f"Искажение: {r[4] or '—'} [{r[5] or '—'}]\n"
            f"За: {r[6] or '—'}\n"
            f"Против: {r[7] or '—'}\n"
            f"Альтернатива: {r[8] or '—'}"
        )

    data = "\n".join(lines).encode("utf-8")
    bio = BytesIO(data)
    bio.name = "clarity_export.txt"
    await update.message.reply_document(document=bio, filename="clarity_export.txt")


async def new_thought_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    if not msg or not update.effective_user:
        return ConversationHandler.END
    tone = _get_tone(update.effective_user.id)
    await msg.reply_text(f"{_tone_text(tone, 'thought_prompt')}\n\n{CANCEL_HINT_RU}", reply_markup=_flow_keyboard())
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
    if _is_too_vague(thought_text):
        await update.message.reply_text("Попробуй конкретнее: «Я думаю, что … и из-за этого …». Так разбор будет точнее.")
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
    await update.message.reply_text(f"{_tone_text(tone, 'thought_saved')}\n\n{EMOTION_PROMPT_RU}", reply_markup=emotion_keyboard)
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
    await update.message.reply_text(INTENSITY_PROMPT_RU, reply_markup=_flow_keyboard())
    await update.message.reply_text("Быстрый выбор:", reply_markup=_intensity_quick_keyboard("before"))
    return WAIT_INTENSITY_BEFORE


async def _save_intensity_before_and_next(update: Update, context: ContextTypes.DEFAULT_TYPE, value: int, msg) -> int:
    draft = context.user_data.get("draft_entry")
    if not draft or not draft.get("thought_text") or not update.effective_user:
        await msg.reply_text("Черновик не найден. Нажми «Новая мысль» и начни заново.")
        return ConversationHandler.END

    draft["intensity_before"] = value
    context.user_data["draft_entry"] = draft

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO entries (tg_user_id, thought_text, emotion_label, intensity_before, is_completed)
        VALUES (?, ?, ?, ?, 0)
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

    await msg.reply_text(EMOTION_STEP_DONE_RU)
    await msg.reply_text(DISTORTION_PROMPT_RU, reply_markup=_distortion_choice_keyboard())
    return WAIT_DISTORTION


async def receive_intensity_before(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    raw = (update.message.text or "").strip()
    if not raw.isdigit():
        await update.message.reply_text("Нужно число от 0 до 100.")
        return WAIT_INTENSITY_BEFORE

    value = int(raw)
    if value < 0 or value > 100:
        await update.message.reply_text("Только диапазон 0–100.")
        return WAIT_INTENSITY_BEFORE

    return await _save_intensity_before_and_next(update, context, value, update.message)


async def choose_intensity_before(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return WAIT_INTENSITY_BEFORE
    await query.answer()

    try:
        value = int((query.data or "int_before:0").split(":", 1)[1])
    except Exception:
        await query.message.reply_text("Не поняла значение. Введи число 0–100.")
        return WAIT_INTENSITY_BEFORE

    if value < 0 or value > 100:
        await query.message.reply_text("Только диапазон 0–100.")
        return WAIT_INTENSITY_BEFORE

    return await _save_intensity_before_and_next(update, context, value, query.message)


async def distortion_info_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return WAIT_DISTORTION
    await query.answer()

    code = (query.data or "dist_info:back").split(":", 1)[1]
    if code == "back":
        await query.edit_message_text(
            "Выбери искажение, чтобы посмотреть подробное объяснение:",
            reply_markup=_distortion_info_keyboard(),
        )
        return WAIT_DISTORTION

    text = DISTORTION_DETAILS.get(code)
    if not text:
        await query.edit_message_text("Не нашла описание, выбери пункт из списка.", reply_markup=_distortion_info_keyboard())
        return WAIT_DISTORTION

    await query.edit_message_text(text, reply_markup=_distortion_detail_keyboard(code))
    return WAIT_DISTORTION


async def distortion_pick_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return WAIT_DISTORTION
    await query.answer()

    code = (query.data or "dist_pick:other").split(":", 1)[1]
    label = CODE_TO_DISTORTION_LABEL.get(code, "Другое")

    draft = context.user_data.get("draft_entry", {})
    entry_id = draft.get("entry_id")
    if not entry_id:
        await query.message.reply_text("Не нашла активную запись. Нажми «Новая мысль» и начни заново.")
        return ConversationHandler.END

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE entries SET distortion = ?, distortion_code = ? WHERE id = ?",
        (label, code, entry_id),
    )
    conn.commit()
    conn.close()

    draft["distortion"] = label
    draft["distortion_code"] = code
    context.user_data["draft_entry"] = draft

    short = f"\nКоротко: {DISTORTION_EXPLAIN[label]}." if label in DISTORTION_EXPLAIN else ""
    await query.message.reply_text(f"{DISTORTION_SAVED_RU}{short}\n\n{EVIDENCE_FOR_PROMPT_RU}", reply_markup=_flow_keyboard())
    return WAIT_EVIDENCE_FOR


async def receive_distortion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    distortion = (update.message.text or "").strip()
    if not distortion:
        await update.message.reply_text("Выбери искажение кнопкой или введи текстом.")
        return WAIT_DISTORTION

    if distortion.lower() == "не уверен":
        await update.message.reply_text(
            "Ок, давай разберёмся точнее.\n"
            "Нажми «Подробнее» на варианте, который ближе всего, потом выбери искажение в меню.",
            reply_markup=_distortion_info_keyboard(),
        )
        return WAIT_DISTORTION

    draft = context.user_data.get("draft_entry", {})
    entry_id = draft.get("entry_id")
    if not entry_id:
        await update.message.reply_text("Не нашла активную запись. Нажми «Новая мысль» и начни заново.")
        return ConversationHandler.END

    distortion_code = DISTORTION_LABEL_TO_CODE.get(distortion, "other")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE entries SET distortion = ?, distortion_code = ? WHERE id = ?",
        (distortion, distortion_code, entry_id),
    )
    conn.commit()
    conn.close()

    draft["distortion"] = distortion
    draft["distortion_code"] = distortion_code
    context.user_data["draft_entry"] = draft

    short = f"\nКоротко: {DISTORTION_EXPLAIN[distortion]}." if distortion in DISTORTION_EXPLAIN else ""
    await update.message.reply_text(f"{DISTORTION_SAVED_RU}{short}\n\n{EVIDENCE_FOR_PROMPT_RU}", reply_markup=_flow_keyboard())
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
    if _is_too_vague(evidence_for):
        await update.message.reply_text("Нужны наблюдаемые факты. Пример: «дедлайн сдвинулся на 2 дня», «получил 1 критичный комментарий».")
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

    await update.message.reply_text(EVIDENCE_AGAINST_PROMPT_RU, reply_markup=_flow_keyboard())
    return WAIT_EVIDENCE_AGAINST


def _alternative_hint_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Что бы я сказал другу?", callback_data="alt_hint:friend")],
            [InlineKeyboardButton("Факты против страха", callback_data="alt_hint:facts")],
            [InlineKeyboardButton("Мягкая реалистичная версия", callback_data="alt_hint:balanced")],
            [InlineKeyboardButton("🤖 Помоги переформулировать", callback_data="alt_ai:rewrite")],
        ]
    )


def _alternative_hint_text(kind: str, thought: str) -> str:
    thought = (thought or "эту мысль").strip()
    if kind == "friend":
        return f"Если бы друг сказал: «{thought}», я бы ответил: «Ты не обязан верить первой тревожной мысли. Давай опираться на факты и на то, что реально в твоём контроле прямо сейчас»."
    if kind == "facts":
        return "Проверь: какие 2–3 факта прямо сейчас не подтверждают худший сценарий? Собери их и сформулируй более точную мысль."
    return "Более реалистичная формулировка: «Да, сейчас мне непросто. Но это временно, и у меня есть шаги, которые помогут стабилизироваться»."


def _ai_rewrite_options(thought: str, evidence_against: str) -> list[str]:
    t = (thought or "").strip() or "Мне сейчас тяжело"
    ea = (evidence_against or "").strip()
    fact_tail = f" Факты против худшего сценария: {ea[:140]}." if ea else ""

    return [
        f"Сейчас мне тревожно, и это объяснимо. Но мысль «{t[:120]}» — это не факт.{fact_tail} Я могу сделать один маленький шаг и проверить реальность.",
        f"Я замечаю автоматическую мысль: «{t[:120]}». Она усиливает эмоцию, но не определяет реальность.{fact_tail} Более точный вывод: ситуация сложная, но решаемая по шагам.",
        f"Мне непросто, и это ок. Вместо «{t[:120]}» я выбираю: «Сейчас тяжело, но я справляюсь шаг за шагом».{fact_tail}",
    ]


async def receive_evidence_against(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    evidence_against = (update.message.text or "").strip()
    if _contains_crisis_signal(evidence_against):
        return await _handle_crisis(update, context, evidence_against)
    if len(evidence_against) < 3:
        await update.message.reply_text("Слишком коротко. Напиши хотя бы 3 символа.")
        return WAIT_EVIDENCE_AGAINST
    if _is_too_vague(evidence_against):
        await update.message.reply_text("Дай 1–2 контрфакта. Например: «раньше уже справлялся», «есть поддержка», «есть план B».")
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
    await update.message.reply_text(ALTERNATIVE_PROMPT_RU, reply_markup=_flow_keyboard())
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
    cur.execute(
        "UPDATE entries SET intensity_after = ?, is_completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
        (after, entry_id),
    )
    conn.commit()
    conn.close()

    delta = before - after
    next_step = _next_step_recommendation(delta=delta, after=after, distortion=distortion)
    if update.message:
        # Use the new formatted result with visual elements
        result_text = _format_result(before=before, after=after, delta=delta, next_step=next_step)
        await update.message.reply_text(result_text, reply_markup=_main_menu_inline())

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

    await update.message.reply_text(INTENSITY_AFTER_PROMPT_RU, reply_markup=_intensity_quick_keyboard("after"))
    return WAIT_INTENSITY_AFTER


async def apply_alternative_hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    draft = context.user_data.get("draft_entry", {})
    thought = draft.get("thought_text", "")
    entry_id = draft.get("entry_id")
    if not entry_id:
        await query.message.reply_text("Не нашла активную запись. Нажми «Новая мысль» и начни заново.")
        return

    data = query.data or "alt_hint:balanced"
    if data == "alt_ai:back":
        await query.edit_message_text(ALTERNATIVE_HINT_PROMPT_RU, reply_markup=_alternative_hint_keyboard())
        return

    if data == "alt_ai:rewrite":
        options = _ai_rewrite_options(thought=thought, evidence_against=draft.get("evidence_against", ""))
        ai_text = (
            "🤖 Варианты переформулировки:\n\n"
            f"1) {options[0]}\n\n"
            f"2) {options[1]}\n\n"
            f"3) {options[2]}\n\n"
            "Скопируй понравившийся вариант (можно отредактировать) и отправь сообщением."
        )
        await query.edit_message_text(
            ai_text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад к подсказкам", callback_data="alt_ai:back")]]
            ),
        )
        return

    kind = data.split(":", 1)[1]
    hint_text = _alternative_hint_text(kind, thought)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE entries SET alternative_thought = ? WHERE id = ?", (hint_text, entry_id))
    conn.commit()
    conn.close()

    draft["alternative_thought"] = hint_text
    context.user_data["draft_entry"] = draft

    await query.edit_message_text(f"Подсказка:\n{hint_text}")
    await query.message.reply_text(INTENSITY_AFTER_PROMPT_RU, reply_markup=_intensity_quick_keyboard("after"))


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


async def choose_intensity_after(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return WAIT_INTENSITY_AFTER
    await query.answer()

    try:
        after = int((query.data or "int_after:0").split(":", 1)[1])
    except Exception:
        await query.message.reply_text("Не поняла значение. Введи число 0–100.")
        return WAIT_INTENSITY_AFTER

    if after < 0 or after > 100:
        await query.message.reply_text("Только диапазон 0–100.")
        return WAIT_INTENSITY_AFTER

    draft = context.user_data.get("draft_entry", {})
    entry_id = draft.get("entry_id")
    if not entry_id:
        await query.message.reply_text("Не нашла активную запись. Нажми «Новая мысль» и начни заново.")
        return ConversationHandler.END

    return await _finalize_with_after_intensity(update, context, after)


def _parse_history_filters(text: str) -> tuple[str | None, str | None, str | None, int]:
    emotion = None
    distortion = None
    distortion_code = None
    days = 30
    parts = (text or "").split()

    # quick UI shortcuts: "История 7д", "История 30д", "История тревога"
    if len(parts) >= 2 and parts[0].lower() == "история":
        p = parts[1].lower()
        if p in {"7д", "7d"}:
            days = 7
        elif p in {"30д", "30d"}:
            days = 30
        elif p in {"тревога", "грусть", "злость", "стыд", "вина", "страх", "раздражение", "пустота"}:
            emotion = parts[1].capitalize()

    for part in parts[1:]:
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        v = v.replace("_", " ").strip()
        if k == "emotion" and v:
            emotion = v
        elif k == "distortion" and v:
            distortion = v
            distortion_code = DISTORTION_LABEL_TO_CODE.get(v)
        elif k == "distortion_code" and v:
            distortion_code = v.lower()
            distortion = CODE_TO_DISTORTION_LABEL.get(distortion_code, distortion)
        elif k == "days" and v.isdigit():
            days = max(1, min(365, int(v)))
    return emotion, distortion, distortion_code, days


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    if not msg or not update.effective_user:
        return

    base_text = update.message.text if update.message else "История"
    emotion, distortion, distortion_code, days = _parse_history_filters(base_text or "")

    query = (
        """
        SELECT created_at, thought_text, emotion_label, intensity_before, intensity_after, distortion
        FROM entries
        WHERE tg_user_id = ?
          AND is_completed = 1
          AND datetime(COALESCE(completed_at, created_at)) >= datetime('now', ?)
        """
    )
    params = [update.effective_user.id, f"-{days} days"]

    if emotion:
        query += " AND emotion_label = ?"
        params.append(emotion)
    if distortion_code:
        query += " AND distortion_code = ?"
        params.append(distortion_code)
    elif distortion:
        query += " AND distortion = ?"
        params.append(distortion)

    query += " ORDER BY id DESC LIMIT 10"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        if update.callback_query:
            await update.callback_query.edit_message_text(HISTORY_EMPTY_RU)
        else:
            await msg.reply_text(HISTORY_EMPTY_RU)
        return

    lines = [f"📜 История (последние {len(rows)} карточек)\n━━━━━━━━━━━━━━━"]
    for r in rows:
        thought = (r[1] or "").replace("\n", " ").strip()
        if len(thought) > 40:
            thought = thought[:40] + "…"
        emo = r[2] or "—"
        before = r[3] if r[3] is not None else "—"
        after = r[4] if r[4] is not None else "—"
        dist = r[5] or "—"
        delta = "—"
        if isinstance(before, int) and isinstance(after, int):
            delta = before - after

        # Visual indicator for improvement
        if isinstance(delta, int):
            if delta > 0:
                delta_str = f"↓{delta}"  # Down arrow for improvement
            elif delta < 0:
                delta_str = f"↑{abs(delta)}"
            else:
                delta_str = "—"
        else:
            delta_str = delta

        lines.append(f"• {emo} {delta_str}\n  {thought[:35]}")

    lines.append(f"\n{HISTORY_FILTER_HINT_RU}")
    text = "\n".join(lines)
    if update.callback_query:
        await update.callback_query.edit_message_text(text)
    else:
        await msg.reply_text(text)
