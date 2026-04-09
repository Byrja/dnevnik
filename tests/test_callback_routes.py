import re
import unittest
from pathlib import Path


def main_py() -> str:
    return Path(__file__).resolve().parents[1].joinpath("src", "main.py").read_text(encoding="utf-8")


class CallbackRoutesTests(unittest.TestCase):
    def test_menu_new_entrypoint_exists(self) -> None:
        src = main_py()
        self.assertRegex(src, r"CallbackQueryHandler\(new_thought_entry, pattern=r\"\^menu:new\$\"\)")

    def test_menu_new_is_in_conversation_entry_points(self) -> None:
        src = main_py()
        self.assertIn("entry_points=[", src)
        self.assertIn("CallbackQueryHandler(new_thought_entry, pattern=r\"^menu:new$\")", src)

    def test_menu_callback_routes_exist(self) -> None:
        src = main_py()
        self.assertIn("menu:(history|stats|settings|help)", src)

    def test_distortion_callback_routes_exist(self) -> None:
        src = main_py()
        self.assertIn("dist_info:", src)
        self.assertIn("dist_pick:", src)

    def test_intensity_quick_callbacks_exist(self) -> None:
        src = main_py()
        self.assertIn("int_before:(20|40|60|80|100)", src)
        self.assertIn("int_after:(20|40|60|80|100)", src)


if __name__ == "__main__":
    unittest.main()
