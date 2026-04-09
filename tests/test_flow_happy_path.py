import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from telegram.ext import ConversationHandler

import db
import handlers


class FakeUser:
    def __init__(self, user_id: int = 472144090) -> None:
        self.id = user_id
        self.username = "sasha"
        self.first_name = "Sasha"


class FakeMessage:
    def __init__(self, user: FakeUser, text: str = "") -> None:
        self.from_user = user
        self.text = text
        self.chat_id = user.id
        self.answers = []

    async def reply_text(self, text: str, reply_markup=None, parse_mode=None):
        self.answers.append({"text": text, "reply_markup": reply_markup, "parse_mode": parse_mode})


class FakeCallbackQuery:
    def __init__(self, user: FakeUser, data: str, message: FakeMessage) -> None:
        self.from_user = user
        self.data = data
        self.message = message

    async def answer(self):
        return None

    async def edit_message_text(self, text: str, reply_markup=None, parse_mode=None):
        self.message.answers.append({"text": text, "reply_markup": reply_markup, "parse_mode": parse_mode, "edited": True})


class FakeUpdate:
    def __init__(self, user: FakeUser, text: str = "", callback_data: str | None = None, callback_message: FakeMessage | None = None) -> None:
        self.effective_user = user
        self.message = FakeMessage(user, text) if callback_data is None else None
        self.callback_query = (
            FakeCallbackQuery(user, callback_data, callback_message or FakeMessage(user, ""))
            if callback_data is not None
            else None
        )


class FakeJobQueue:
    def __init__(self) -> None:
        self.calls = []

    def run_once(self, cb, when):
        self.calls.append({"cb": cb, "when": when})


class FakeContext:
    def __init__(self) -> None:
        self.user_data = {}
        self.job_queue = None
        self.args = []


class FlowHappyPathTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self._tmpdir.name) / "test_data.db"
        db.init_db()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    async def test_full_happy_path_completes_entry(self) -> None:
        user = FakeUser()
        ctx = FakeContext()

        state = await handlers.new_thought_entry(FakeUpdate(user, "/new"), ctx)
        self.assertEqual(state, handlers.WAIT_THOUGHT)

        state = await handlers.receive_thought_text(FakeUpdate(user, "Я все провалю на встрече"), ctx)
        self.assertEqual(state, handlers.WAIT_EMOTION)

        state = await handlers.receive_emotion(FakeUpdate(user, "Тревога"), ctx)
        self.assertEqual(state, handlers.WAIT_INTENSITY_BEFORE)

        state = await handlers.receive_intensity_before(FakeUpdate(user, "60"), ctx)
        self.assertEqual(state, handlers.WAIT_DISTORTION)

        state = await handlers.receive_distortion(FakeUpdate(user, "Катастрофизация"), ctx)
        self.assertEqual(state, handlers.WAIT_EVIDENCE_FOR)

        state = await handlers.receive_evidence_for(FakeUpdate(user, "Дедлайн близко и задача большая"), ctx)
        self.assertEqual(state, handlers.WAIT_EVIDENCE_AGAINST)

        state = await handlers.receive_evidence_against(FakeUpdate(user, "Раньше уже делал сложные задачи вовремя"), ctx)
        self.assertEqual(state, handlers.WAIT_ALTERNATIVE_THOUGHT)

        state = await handlers.receive_alternative_thought(FakeUpdate(user, "Мне тревожно, но я могу разбить задачу на шаги"), ctx)
        self.assertEqual(state, handlers.WAIT_INTENSITY_AFTER)

        state = await handlers.receive_intensity_after(FakeUpdate(user, "35"), ctx)
        self.assertEqual(state, ConversationHandler.END)

        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT is_completed, intensity_before, intensity_after FROM entries WHERE tg_user_id = ? ORDER BY id DESC LIMIT 1",
            (user.id,),
        )
        row = cur.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], 60)
        self.assertEqual(row[2], 35)

    async def test_callback_edge_path_intensity_and_distortion_pick(self) -> None:
        user = FakeUser()
        ctx = FakeContext()

        await handlers.new_thought_entry(FakeUpdate(user, "/new"), ctx)
        await handlers.receive_thought_text(FakeUpdate(user, "Я не справлюсь"), ctx)
        await handlers.receive_emotion(FakeUpdate(user, "Тревога"), ctx)

        cb_msg = FakeMessage(user, "")
        state = await handlers.choose_intensity_before(
            FakeUpdate(user, callback_data="int_before:60", callback_message=cb_msg),
            ctx,
        )
        self.assertEqual(state, handlers.WAIT_DISTORTION)

        state = await handlers.distortion_pick_action(
            FakeUpdate(user, callback_data="dist_pick:catastrophizing", callback_message=cb_msg),
            ctx,
        )
        self.assertEqual(state, handlers.WAIT_EVIDENCE_FOR)

    async def test_followup_callback_schedules_job(self) -> None:
        user = FakeUser()
        ctx = FakeContext()
        ctx.job_queue = FakeJobQueue()
        cb_msg = FakeMessage(user, "")

        await handlers.set_followup_reminder(
            FakeUpdate(user, callback_data="followup:3h", callback_message=cb_msg),
            ctx,
        )

        self.assertEqual(len(ctx.job_queue.calls), 1)
        self.assertEqual(ctx.job_queue.calls[0]["when"], 10800)

    async def test_intensity_after_callback_completes_session(self) -> None:
        user = FakeUser()
        ctx = FakeContext()

        await handlers.new_thought_entry(FakeUpdate(user, "/new"), ctx)
        await handlers.receive_thought_text(FakeUpdate(user, "Я не справлюсь"), ctx)
        await handlers.receive_emotion(FakeUpdate(user, "Тревога"), ctx)
        await handlers.receive_intensity_before(FakeUpdate(user, "60"), ctx)
        await handlers.receive_distortion(FakeUpdate(user, "Катастрофизация"), ctx)
        await handlers.receive_evidence_for(FakeUpdate(user, "Сложная задача"), ctx)
        await handlers.receive_evidence_against(FakeUpdate(user, "Бывало и сложнее"), ctx)
        await handlers.receive_alternative_thought(FakeUpdate(user, "Я справлюсь по шагам"), ctx)

        cb_msg = FakeMessage(user, "")
        state = await handlers.choose_intensity_after(
            FakeUpdate(user, callback_data="int_after:40", callback_message=cb_msg),
            ctx,
        )
        self.assertEqual(state, ConversationHandler.END)
        self.assertTrue(any("Итог разбора" in a["text"] for a in cb_msg.answers))

    async def test_alt_hint_does_not_force_step8(self) -> None:
        user = FakeUser()
        ctx = FakeContext()

        await handlers.new_thought_entry(FakeUpdate(user, "/new"), ctx)
        await handlers.receive_thought_text(FakeUpdate(user, "Я не справлюсь"), ctx)
        await handlers.receive_emotion(FakeUpdate(user, "Тревога"), ctx)
        await handlers.receive_intensity_before(FakeUpdate(user, "60"), ctx)
        await handlers.receive_distortion(FakeUpdate(user, "Катастрофизация"), ctx)
        await handlers.receive_evidence_for(FakeUpdate(user, "Сложная задача"), ctx)
        await handlers.receive_evidence_against(FakeUpdate(user, "Бывало и сложнее"), ctx)

        cb_msg = FakeMessage(user, "")
        await handlers.apply_alternative_hint(
            FakeUpdate(user, callback_data="alt_hint:friend", callback_message=cb_msg),
            ctx,
        )

        self.assertTrue(any("Отправь свою альтернативную мысль" in a["text"] for a in cb_msg.answers))


if __name__ == "__main__":
    unittest.main()
