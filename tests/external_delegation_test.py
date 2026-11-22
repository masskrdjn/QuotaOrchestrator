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
list_models = MODULE["list_models"]
parse_fallback = MODULE["parse_fallback"]
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

    def test_write_mode_flags_for_all_providers(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_cli = Path(directory) / "fake_cli.py"
            fake_cli.write_text(
                "import json, sys\n"
                "from pathlib import Path\n"
                "args = sys.argv[1:]\n"
                "if '-o' in args:\n"
                "    Path(args[args.index('-o') + 1]).write_text(json.dumps(args), encoding='utf-8')\n"
                "else:\n"
                "    print(json.dumps(args))\n",
                encoding="utf-8",
            )
            expected_mode_flag = {
                "codex": ("--sandbox", "workspace-write"),
                "claude": ("--permission-mode", "acceptEdits"),
                "grok": ("--permission-mode", "acceptEdits"),
                "agy": ("--mode", "accept-edits"),
            }
            for provider, (flag, value) in expected_mode_flag.items():
                with self.subTest(provider=provider), patch.dict(
                    delegate.__globals__,
                    executable_command=lambda _: [sys.executable, str(fake_cli)],
                ):
                    result = delegate(provider, "edit file", "m1", "high", 5, mode="write")
                    self.assertEqual(result["status"], "ok", result)
                    self.assertEqual(result["mode"], "write")
                    args = json.loads(result["response"])
                    idx = args.index(flag)
                    self.assertEqual(args[idx + 1], value)
                    for forbidden in (
                        "--yolo",
                        "--dangerously-bypass-approvals-and-sandbox",
                        "--dangerously-skip-permissions",
                        "bypassPermissions",
                    ):
                        self.assertNotIn(forbidden, args)

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

    def test_list_models_and_check_models_for_agy_and_grok(self):
        agy_stdout = (
            "gemini-4-neon-high\tGemini 4 Neon (High)\n"
            "gemini-4-hydrogen-high\tGemini 4 Hydrogen (High)\n"
            "claude-opus-5-5-high\tClaude Opus 5.5 (High)\n"
            "claude-sonnet-5-5-high\tClaude Sonnet 5.5 (High)\n"
        )
        grok_stdout = (
            "You are logged in with grok.com.\n\n"
            "Default model: grok-4.7\n\n"
            "Available models:\n"
            "  * grok-4.7 (default)\n"
        )
        with patch.dict(list_models.__globals__, executable_command=lambda p: [p]):
            with patch("subprocess.run", return_value=subprocess.CompletedProcess(["agy"], 0, agy_stdout, "")):
                agy_listing = list_models("agy", 5)
                self.assertEqual(agy_listing["status"], "ok")
                self.assertEqual(
                    agy_listing["models"],
                    [
                        "gemini-4-neon-high",
                        "gemini-4-hydrogen-high",
                        "claude-opus-5-5-high",
                        "claude-sonnet-5-5-high",
                    ],
                )
            with patch("subprocess.run", return_value=subprocess.CompletedProcess(["grok"], 0, grok_stdout, "")):
                grok_listing = list_models("grok", 5)
                self.assertEqual(grok_listing["status"], "ok")
                self.assertEqual(grok_listing["models"], ["grok-4.7"])

    def test_ordered_fallback_chain_and_paid_agy_bridge_detection(self):
        # Free agy account without claude-opus-5-5-high falls back to codex:gpt-6.2-sol:xhigh.
        free_agy_models = "gemini-4-hydrogen-high\tGemini 4 Hydrogen (High)\n"

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ["claude", "--permission-mode"]:
                return subprocess.CompletedProcess(cmd, 1, "", "Model claude-fable-5-2 unavailable on plan")
            if cmd == ["agy", "models"]:
                return subprocess.CompletedProcess(cmd, 0, free_agy_models, "")
            if cmd[0] == "codex":
                out_idx = cmd.index("-o") + 1
                Path(cmd[out_idx]).write_text("Sol xhigh fallback response", encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, "", "")
            raise AssertionError(f"Unexpected command: {cmd}")

        with patch.dict(delegate.__globals__, executable_command=lambda p: [p]), patch(
            "subprocess.run", side_effect=fake_run,
        ):
            result = delegate(
                "claude",
                "arbitrate architecture",
                "claude-fable-5-2",
                "xhigh",
                5,
                fallbacks=["agy:claude-opus-5-5-high", "codex:gpt-6.2-sol:xhigh"],
                check_models=True,
            )
            self.assertEqual(result["status"], "ok", result)
            self.assertEqual(result["provider"], "codex")
            self.assertEqual(result["model"], "gpt-6.2-sol")
            self.assertEqual(result["effort"], "xhigh")
            self.assertTrue(result["fallback_used"])
            self.assertEqual(
                result["requested"],
                {"provider": "claude", "model": "claude-fable-5-2", "effort": "xhigh"},
            )
            self.assertEqual(len(result["attempts"]), 2)
            self.assertEqual(result["attempts"][0]["provider"], "claude")
            self.assertEqual(result["attempts"][0]["status"], "failed")
            self.assertEqual(result["attempts"][1]["provider"], "agy")
            self.assertEqual(result["attempts"][1]["status"], "unavailable")
            self.assertIn("claude-opus-5-5-high", result["attempts"][1]["error"])

    def test_timeout_stops_fallback_chain_immediately(self):
        with patch.dict(delegate.__globals__, executable_command=lambda p: [p]), patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 5),
        ) as run:
            result = delegate(
                "claude",
                "long task",
                "opus",
                "high",
                5,
                fallbacks=["codex:gpt-6.2-sol:high"],
            )
            self.assertEqual(result["status"], "timeout")
            self.assertFalse(result["fallback_used"])
            self.assertEqual(run.call_count, 1)

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

            # Invalid fallback provider is rejected with exit code 2.
            path.write_text("valid mission", encoding="utf-8")
            argv = [str(SCRIPT), "grok", str(path), "--fallback", "unknown:m1:high"]
            with patch.object(sys, "argv", argv), redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as exc:
                    main()
                self.assertEqual(exc.exception.code, 2)
                self.assertIn("unknown fallback provider", stderr.getvalue())

    def test_main_list_models_mode(self):
        expected = {"provider": "agy", "status": "ok", "models": ["gemini-4-neon-high"]}
        mocked = Mock(return_value=expected)
        with patch.object(sys, "argv", [str(SCRIPT), "agy", "--list-models"]), redirect_stdout(
            io.StringIO(),
        ) as stdout, patch.dict(main.__globals__, list_models=mocked):
            self.assertEqual(main(), 0)
            self.assertEqual(json.loads(stdout.getvalue()), expected)
            mocked.assert_called_once_with("agy", 120)

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


if __name__ == "__main__":
    unittest.main()
