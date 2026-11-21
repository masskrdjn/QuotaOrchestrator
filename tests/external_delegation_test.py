"""Exercise the shared mission and response contract without provider accounts."""

import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = (Path(__file__).resolve().parents[1]
          / "plugins/quota-orchestrator/scripts/delegate_external.py")
MODULE = runpy.run_path(str(SCRIPT))
delegate = MODULE["delegate"]


class ExternalDelegation(unittest.TestCase):
    def test_context_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_cli = Path(directory) / "fake_cli.py"
            fake_cli.write_text(
                "import json, sys\n"
                "print(json.dumps({'args': sys.argv[1:], "
                "'stdin': sys.stdin.buffer.read().decode('utf-8').replace('\\r\\n', '\\n')}))\n",
                encoding="utf-8",
            )
            mission = '-test\nEntrée avec "guillemets" et $(literal)'
            for provider, prompt_flag in (
                ("claude", "--print"), ("grok", "--single"), ("agy", "--print"),
            ):
                with self.subTest(provider=provider), patch.dict(
                    delegate.__globals__,
                    executable_command=lambda _: [sys.executable, str(fake_cli)],
                ):
                    result = delegate(provider, mission, "model-id", "high", 5)
                    self.assertEqual(result["status"], "ok")
                    captured = json.loads(result["response"])
                    self.assertIn("plan", captured["args"])
                    self.assertIn("--model=model-id", captured["args"])
                    self.assertIn("--effort=high", captured["args"])
                    if provider == "claude":
                        self.assertIn(prompt_flag, captured["args"])
                        self.assertEqual(captured["stdin"], mission)
                    else:
                        self.assertIn(f"{prompt_flag}={mission}", captured["args"])
                        self.assertEqual(captured["stdin"], "")

    def test_reports_failures(self):
        with patch.dict(delegate.__globals__, executable_command=lambda _: None):
            self.assertEqual(delegate("agy", "mission", None, None, 1)["status"], "unavailable")
        with patch.dict(delegate.__globals__, executable_command=lambda _: ["agy"]):
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("agy", 1)):
                self.assertEqual(delegate("agy", "mission", None, None, 1)["status"], "timeout")
            with patch("subprocess.run", return_value=subprocess.CompletedProcess(
                ["agy"], 7, "", "Authentication failed",
            )):
                result = delegate("agy", "mission", None, None, 1)
                self.assertEqual(result["status"], "failed")
                self.assertEqual(result["exit_code"], 7)
                self.assertEqual(result["error"], "Authentication failed")
