import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import handlers


class SafetyGuardsTests(unittest.TestCase):
    def test_soft_crisis_markers_detected(self):
        phrases = [
            "Мне иногда кажется, что лучше бы меня не было.",
            "не хочу просыпаться по утрам",
            "иногда хочу исчезнуть",
            "кажется, нет смысла жить",
            "всем будет лучше без меня",
        ]
        for p in phrases:
            self.assertTrue(handlers._contains_crisis_signal(p), p)

    def test_neutral_phrases_not_detected_as_crisis(self):
        phrases = [
            "Я устал после работы",
            "Мне тревожно из-за дедлайна",
            "Хочу отдохнуть и выспаться",
        ]
        for p in phrases:
            self.assertFalse(handlers._contains_crisis_signal(p), p)

    def test_noise_input_detection(self):
        self.assertTrue(handlers._is_noise_input("........."))
        self.assertTrue(handlers._is_noise_input("---"))
        self.assertFalse(handlers._is_noise_input("тревога"))


if __name__ == "__main__":
    unittest.main()
