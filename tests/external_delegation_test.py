"""Exercise the shared mission and response contract without provider accounts."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


SCRIPT = (Path(__file__).resolve().parents[1]
          / "plugins/quota-orchestrator/scripts/delegate_external.py")
MODULE = runpy.run_path(str(SCRIPT))
delegate = MODULE["delegate"]
executable_command = MODULE["executable_command"]
main = MODULE["main"]


class ExternalDelegation(unittest.TestCase):
    def test_context_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_cli = Path(directory) / "fake_cli.py"
            fake_cli.write_text(
                "import json, sys\n"
                "from pathlib import Path\n"
                "args = sys.argv[1:]\n"
                "stdin = sys.stdin.buffer.read().decode('utf-8').replace('\\r\\n', '\\n')\n"
                "result = {'args': args, 'stdin': stdin}\n"
                "if '--prompt-file' in args:\n"
                "    prompt = Path(args[args.index('--prompt-file') + 1])\n"
                "    result['file'] = prompt.read_bytes().decode('utf-8')\n"
                "if '-o' in args:\n"
                "    output = Path(args[args.index('-o') + 1])\n"
                "    output.write_text(json.dumps(result), encoding='utf-8')\n"
                "    print('Progress noise')\n"
                "else:\n"
                "    print(json.dumps(result))\n",
                encoding="utf-8",
            )
            mission = '/help\nEntrée avec "guillemets" et $(literal)'
            long_mission = mission + "\n" + "é" * 40_000
            for provider in ("codex", "claude", "grok", "agy"):
                with self.subTest(provider=provider), patch.dict(
                    delegate.__globals__,
                    executable_command=lambda _: [sys.executable, str(fake_cli)],
                ):
                    prompt = mission if provider == "agy" else long_mission
                    result = delegate(provider, prompt, "model-id", "high", 5)
                    self.assertEqual(result["status"], "ok", result)
                    captured = json.loads(result["response"])
                    args = captured["args"]
                    self.assertIn("--model=model-id", args)
                    if provider == "codex":
                        self.assertEqual(args[:6], [
                            "exec", "--sandbox", "read-only", "--ephemeral", "--color", "never",
                        ])
                        self.assertIn("--skip-git-repo-check", args)
                        self.assertEqual(args[args.index("-c") + 1], 'model_reasoning_effort="high"')
                        self.assertEqual(args[-1], "-")
                        self.assertEqual(captured["stdin"], prompt)
                        self.assertFalse(Path(args[args.index("-o") + 1]).parent.exists())
                    else:
                        self.assertIn("plan", args)
                        self.assertIn("--effort=high", args)
                    if provider == "claude":
                        self.assertIn("--disable-slash-commands", args)
                        self.assertIn("--print", args)
                        self.assertEqual(captured["stdin"], prompt)
                    elif provider == "grok":
                        self.assertEqual(captured["file"], prompt)
                        self.assertFalse(Path(args[args.index("--prompt-file") + 1]).parent.exists())
                        self.assertEqual(captured["stdin"], "")
                    elif provider == "agy":
                        self.assertIn("--disable-slash-commands", args)
                        self.assertIn("--print-timeout=5s", args)
                        self.assertIn(f"--print={prompt}", args)
                        self.assertEqual(captured["stdin"], "")
                    if provider != "agy":
                        self.assertFalse(any(prompt in arg for arg in args))

    def test_codex_falls_back_to_stdout_when_last_message_is_missing(self):
        completed = subprocess.CompletedProcess(["codex"], 0, " fallback \n", "")
        with patch.dict(delegate.__globals__, executable_command=lambda _: ["codex"]), patch(
            "subprocess.run", return_value=completed,
        ) as run:
            result = delegate("codex", "mission", None, None, 5)
            self.assertEqual(result, {"provider": "codex", "status": "ok", "response": "fallback"})
            args = run.call_args.args[0]
            self.assertFalse(Path(args[args.index("-o") + 1]).parent.exists())

    def test_reports_failures(self):
        with patch.dict(delegate.__globals__, executable_command=lambda _: None):
            self.assertEqual(delegate("agy", "mission", None, None, 1)["status"], "unavailable")
        with patch.dict(delegate.__globals__, executable_command=lambda _: ["agy"]):
            for error, status in (
                (FileNotFoundError("missing"), "unavailable"),
                (OSError("invalid executable"), "failed"),
                (subprocess.TimeoutExpired("agy", 2), "timeout"),
            ):
                with self.subTest(error=error), patch("subprocess.run", side_effect=error) as run:
                    self.assertEqual(delegate("agy", "mission", None, None, 1)["status"], status)
                    self.assertEqual(run.call_args.kwargs["timeout"], 2)
            with patch("subprocess.run", return_value=subprocess.CompletedProcess(
                ["agy"], 7, "", "Authentication failed",
            )):
                result = delegate("agy", "mission", None, None, 1)
                self.assertEqual(result["status"], "failed")
                self.assertEqual(result["exit_code"], 7)
                self.assertEqual(result["error"], "Authentication failed")

    def test_windows_executable_precedes_shim(self):
        for provider in ("codex", "claude", "grok", "agy"):
            executable = f"C:/cli/{provider}.exe"
            with self.subTest(provider=provider), patch.dict(
                executable_command.__globals__, os=SimpleNamespace(name="nt"),
            ), patch("shutil.which", return_value=executable) as which:
                self.assertEqual(executable_command(provider), [executable])
                which.assert_called_once_with(f"{provider}.exe")

    def test_windows_npm_entry_points(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            executable_command.__globals__, os=SimpleNamespace(name="nt"),
        ):
            shim_dir = Path(directory)
            node = shim_dir / "node.exe"
            for provider, relative in (
                ("codex", "@openai/codex/bin/codex.js"),
                ("claude", "@anthropic-ai/claude-code/bin/claude.exe"),
                ("grok", "@xai-official/grok/bin/grok"),
            ):
                with self.subTest(provider=provider):
                    shim = shim_dir / f"{provider}.cmd"
                    entry = shim_dir / "node_modules" / relative
                    entry.parent.mkdir(parents=True)
                    entry.touch()
                    found = {shim.name: str(shim), "node.exe": "C:/path/node.exe"}
                    with patch("shutil.which", side_effect=found.get):
                        expected = [str(entry)] if provider == "claude" else [
                            "C:/path/node.exe", str(entry),
                        ]
                        self.assertEqual(executable_command(provider), expected)
                        if provider != "claude":
                            with patch.dict(found, {"node.exe": None}):
                                self.assertIsNone(executable_command(provider))
                            node.touch()
                            self.assertEqual(executable_command(provider), [str(node), str(entry)])
                            node.unlink()
                        entry.unlink()
                        self.assertIsNone(executable_command(provider))

    def test_main_rejects_invalid_mission_and_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mission.txt"
            for content, timeout, message in (
                ("", "5", "nonempty UTF-8"),
                ("mission\0", "5", "without NUL"),
                ("mission", "0", "--timeout must be positive"),
                ("mission", "-1", "--timeout must be positive"),
            ):
                path.write_text(content, encoding="utf-8")
                argv = [str(SCRIPT), "grok", str(path), "--timeout", timeout]
                with self.subTest(content=content, timeout=timeout), patch.object(
                    sys, "argv", argv,
                ), redirect_stderr(io.StringIO()) as stderr, patch.dict(
                    main.__globals__, delegate=lambda *_: self.fail("invalid mission was delegated"),
                ):
                    with self.assertRaises(SystemExit) as exc:
                        main()
                    self.assertEqual(exc.exception.code, 2)
                    self.assertIn(message, stderr.getvalue())

    def test_main_accepts_utf8_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mission.txt"
            path.write_text("Entrée", encoding="utf-8-sig")
            argv = [str(SCRIPT), "grok", str(path)]
            expected = {"provider": "grok", "status": "ok", "response": "réponse"}
            run = Mock(return_value=expected)
            with patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()) as stdout, patch.dict(
                main.__globals__, delegate=run,
            ):
                self.assertEqual(main(), 0)
                self.assertEqual(json.loads(stdout.getvalue()), expected)
            run.assert_called_once_with("grok", "Entrée", None, None, 120)
