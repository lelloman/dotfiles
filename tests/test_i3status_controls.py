import importlib.machinery
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts/.local/bin/i3status-controls"
loader = importlib.machinery.SourceFileLoader("i3status_controls", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
i3status_controls = importlib.util.module_from_spec(spec)
loader.exec_module(i3status_controls)


class I3StatusControlsTest(unittest.TestCase):
    def test_controls_are_prepended_to_status_update(self):
        update = i3status_controls.augment_update(',[{"name":"time","full_text":"12:00"}]')

        self.assertTrue(update.startswith(","))
        blocks = json.loads(update[1:])
        self.assertEqual(["project", "reset", "time"], [block["name"] for block in blocks])

    def test_left_click_returns_control_name(self):
        self.assertEqual("project", i3status_controls.click_name(',{"name":"project","button":1}'))

    def test_other_clicks_and_status_blocks_are_ignored(self):
        self.assertIsNone(i3status_controls.click_name('{"name":"project","button":3}'))
        self.assertIsNone(i3status_controls.click_name('{"name":"time","button":1}'))
        self.assertIsNone(i3status_controls.click_name("["))


if __name__ == "__main__":
    unittest.main()
