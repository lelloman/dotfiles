import importlib.machinery
import importlib.util
import json
import unittest
from unittest.mock import patch
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts/.local/bin/i3status-controls"
loader = importlib.machinery.SourceFileLoader("i3status_controls", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
i3status_controls = importlib.util.module_from_spec(spec)
loader.exec_module(i3status_controls)


class I3StatusControlsTest(unittest.TestCase):
    @patch.object(i3status_controls, "pactl", side_effect=["Volume: 32768 / 50% / -18.06 dB", "Mute: no"])
    def test_controls_are_prepended_to_status_update(self, _pactl):
        update = i3status_controls.augment_update(',[{"name":"time","full_text":"12:00"}]')

        self.assertTrue(update.startswith(","))
        blocks = json.loads(update[1:])
        self.assertEqual(
            ["project", "reset", "volume_down", "volume", "volume_up", "time"],
            [block["name"] for block in blocks],
        )
        self.assertEqual("🔊 50%", blocks[3]["full_text"])

    @patch.object(i3status_controls, "pactl", side_effect=["Volume: 65536 / 100%", "Mute: yes"])
    def test_muted_volume(self, _pactl):
        self.assertEqual("🔇 muted", i3status_controls.volume_blocks()[1]["full_text"])

    @patch.object(i3status_controls, "pactl", side_effect=FileNotFoundError)
    def test_missing_audio_service_keeps_bar_available(self, _pactl):
        blocks = json.loads(i3status_controls.augment_update('[{"name":"time"}]'))
        self.assertEqual("🔊 unavailable", blocks[3]["full_text"])
        self.assertEqual("time", blocks[-1]["name"])

    def test_volume_mouse_actions(self):
        for name, button, command, amount in [
            ("volume_down", 1, "set-sink-volume", "-5%"),
            ("volume_up", 1, "set-sink-volume", "+5%"),
            ("volume", 1, "set-sink-mute", "toggle"),
            ("volume", 4, "set-sink-volume", "+5%"),
            ("volume", 5, "set-sink-volume", "-5%"),
        ]:
            with self.subTest(name=name, button=button):
                self.assertEqual(
                    [command, "@DEFAULT_SINK@", amount],
                    i3status_controls.volume_action({"name": name, "button": button}),
                )
        self.assertIsNone(i3status_controls.volume_action({"name": "time", "button": 4}))
        self.assertIsNone(i3status_controls.volume_action({"name": "volume", "button": 3}))

    def test_left_click_returns_control_name(self):
        self.assertEqual("project", i3status_controls.click_name(',{"name":"project","button":1}'))

    def test_other_clicks_and_status_blocks_are_ignored(self):
        self.assertIsNone(i3status_controls.click_name('{"name":"project","button":3}'))
        self.assertIsNone(i3status_controls.click_name('{"name":"time","button":1}'))
        self.assertIsNone(i3status_controls.click_name("["))


if __name__ == "__main__":
    unittest.main()
