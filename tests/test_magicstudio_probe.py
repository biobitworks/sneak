import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.magicstudio import ollama_generate, ollama_tags, probe_local_ollama


class MagicStudioProbeTests(unittest.TestCase):
    def test_tags_unreachable_is_not_tested(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("down")):
            r = ollama_tags("http://127.0.0.1:9")
        self.assertFalse(r["ok"])
        self.assertEqual(r["observed_outcome"], "NOT_TESTED")

    def test_generate_ok_detection(self):
        class Resp:
            def read(self):
                return b'{"response":"OLLAMA_OK\\n"}'

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with mock.patch("urllib.request.urlopen", return_value=Resp()):
            r = ollama_generate("lfm2.5:1.2b-instruct")
        self.assertTrue(r["ok"])
        self.assertEqual(r["observed_outcome"], "PASS")

    def test_probe_does_not_claim_magicstudio_on_cloud(self):
        with mock.patch("sneak.magicstudio.ollama_tags", return_value={"ok": False, "models": []}):
            with mock.patch("sneak.magicstudio.local_hostname", return_value="cursor"):
                r = probe_local_ollama()
        self.assertFalse(r["is_magicstudio"])
        self.assertEqual(r["observed_outcome"], "NOT_TESTED")


if __name__ == "__main__":
    unittest.main()
