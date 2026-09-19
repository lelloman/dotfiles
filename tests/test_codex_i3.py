import runpy
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / 'scripts/.local/bin/codex-i3'
BellDetector = runpy.run_path(str(SCRIPT))['BellDetector']


class BellDetectorTest(unittest.TestCase):
    def test_notifications_and_control_strings_across_read_boundaries(self):
        cases = [
            (b'ordinary output', False),
            (b'Needs input\x07', True),
            (b'\x1b]0;Codex title\x07', False),
            (b'\x1b]2;Codex title\x1b\\', False),
            (b'\x1b]0;Codex title\x07\x07', True),
            (b'\x1bPpayload\x07\x1b\\', False),
            (b'\x1bPpayload\x1b\\\x07', True),
        ]
        for data, expected in cases:
            for split in range(len(data) + 1):
                with self.subTest(data=data, split=split):
                    detector = BellDetector()
                    first = detector.feed(data[:split])
                    second = detector.feed(data[split:])
                    self.assertEqual(expected, first or second)
            detector = BellDetector()
            results = [detector.feed(bytes([byte])) for byte in data]
            self.assertEqual(expected, any(results))


if __name__ == '__main__':
    unittest.main()
