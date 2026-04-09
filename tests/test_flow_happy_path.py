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


class FakeUpdate:
    def __init__(self, user: FakeUser, text: str = "") -> None:
        self.effective_user = user
        self.message = FakeMessage(user, text)
        self.callback_query = None


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


if __name__ == "__main__":
    unittest.main()
