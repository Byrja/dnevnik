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
        self.assertIn("menu:(history|stats|settings|help|home)", src)
        self.assertIn("followup:(3h)", src)

    def test_funnel_command_registered(self) -> None:
        src = main_py()
        self.assertIn('CommandHandler("funnel", show_funnel)', src)

    def test_admin_ab_command_registered(self) -> None:
        src = main_py()
        self.assertIn('CommandHandler("admin_ab", admin_ab_mode)', src)

    def test_distortion_callback_routes_exist(self) -> None:
        src = main_py()
        self.assertIn("dist_info:(back|catastrophizing|mind_reading|black_white|discounting_positive|overgeneralization|personalization|emotional_reasoning|should_statements|labeling|fortune_telling|other)", src)
        self.assertIn("dist_pick:(catastrophizing|mind_reading|black_white|discounting_positive|overgeneralization|personalization|emotional_reasoning|should_statements|labeling|fortune_telling|other)", src)

    def test_intensity_quick_callbacks_exist(self) -> None:
        src = main_py()
        self.assertIn("int_before:(20|40|60|80|100)", src)
        self.assertIn("int_after:(20|40|60|80|100)", src)


if __name__ == "__main__":
    unittest.main()
