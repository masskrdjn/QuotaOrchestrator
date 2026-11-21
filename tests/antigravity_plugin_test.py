"""Validate the native Antigravity plugin, marketplace, and PreToolUse delegation guard."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD_PATH = ROOT / "scripts/check_delegation.py"
BUILDER_PATH = ROOT / "scripts/build_antigravity_bundle.py"

EXPECTED_AGENTS = {
    "runner": "flash_lite",
    "scout": "flash",
    "researcher": "flash",
    "builder-flash": "flash",
    "builder": "pro",
    "strategist": "pro",
    "architect": "pro",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AntigravityPluginTest(unittest.TestCase):
    def test_manifest_and_components(self):
        manifest = json.loads((ROOT / ".antigravity-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "quota-orchestrator")
        self.assertEqual(manifest["displayName"], "QuotaOrchestrator")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertTrue((ROOT / manifest["logo"]).is_file())
        self.assertLessEqual(len(manifest["suggestedPrompts"]), 3)
        self.assertTrue((ROOT / "rules/AGENTS.md").is_file())
        self.assertTrue((ROOT / "skills/quota-orchestrator/SKILL.md").is_file())
        self.assertTrue((ROOT / "hooks.json").is_file())
        self.assertTrue(GUARD_PATH.is_file())

    def test_agents_frontmatter(self):
        agent_files = sorted((ROOT / "agents").glob("*.md"))
        self.assertEqual({p.stem for p in agent_files}, set(EXPECTED_AGENTS))
        for path in agent_files:
            text = path.read_text(encoding="utf-8")
            parts = text.split("---", 2)
            self.assertEqual(len(parts), 3, path.name)
            head = parts[1]
            name_match = re.search(r"^name:\s*(\S+)\s*$", head, re.MULTILINE)
            model_match = re.search(r"^model:\s*(\S+)\s*$", head, re.MULTILINE)
            self.assertIsNotNone(name_match, path.name)
            self.assertEqual(name_match.group(1), path.stem)
            self.assertIsNotNone(model_match, path.name)
            self.assertEqual(model_match.group(1), EXPECTED_AGENTS[path.stem])
            self.assertRegex(head, r"(?m)^subagent:\s*true\s*$", path.name)
            self.assertRegex(head, r"(?m)^mainAgent:\s*false\s*$", path.name)
            self.assertIn("tools:", head, path.name)

    def test_marketplace_bundle_checksum(self):
        manifest = json.loads((ROOT / ".antigravity-plugin/plugin.json").read_text(encoding="utf-8"))
        mp = json.loads((ROOT / ".antigravity-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(mp["name"], "quota-orchestrator")
        entry, = mp["plugins"]
        self.assertEqual(entry["name"], "quota-orchestrator")
        source = entry["source"]
        self.assertTrue(source["url"].startswith("https://"))
        self.assertIn(manifest["version"], source["url"])
        self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")

        builder = load_module("agy_bundle_builder", BUILDER_PATH)
        self.assertEqual(builder.sha256_hex(builder.build_zip_bytes(ROOT)), source["sha256"])

    def test_hooks_json_structure(self):
        hooks = json.loads((ROOT / "hooks.json").read_text(encoding="utf-8"))
        guard = hooks["quota-orchestrator-delegation-guard"]
        self.assertTrue(guard["enabled"])
        group, = guard["PreToolUse"]
        self.assertEqual(group["matcher"], "invoke_subagent|swarm")
        handler, = group["hooks"]
        self.assertEqual(handler["type"], "command")
        self.assertIn("check_delegation.py", handler["command"])

    def test_cli_validation_when_available(self):
        agy = shutil.which("agy")
        if not agy:
            self.skipTest("agy CLI not available on PATH")
        # Root repo check: 0 errors, only the documented multi-tool warning on root AGENTS.md.
        proc = subprocess.run(
            [agy, "plugin", "validate", "--json", str(ROOT)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)
        unexpected = [
            f for f in report["findings"]
            if f["severity"] == "error" or (f["severity"] == "warning" and f.get("file") != "AGENTS.md")
        ]
        self.assertEqual(unexpected, [], report["findings"])
        self.assertEqual(report["components"]["agents"], len(EXPECTED_AGENTS))
        self.assertEqual(report["components"]["skills"], 1)
        self.assertEqual(report["components"]["rules"], 1)
        self.assertEqual(report["components"]["hooks"], 1)

        # Standalone .zip bundle check: strict validation with 0 findings.
        builder = load_module("agy_bundle_builder", BUILDER_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "quota-orchestrator-antigravity.zip"
            bundle.write_bytes(builder.build_zip_bytes(ROOT))
            zip_proc = subprocess.run(
                [agy, "plugin", "validate", "--strict", str(bundle)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(zip_proc.returncode, 0, zip_proc.stdout + zip_proc.stderr)


class AntigravityDelegationGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guard = load_module("agy_check_delegation", GUARD_PATH)

    def test_invoke_subagent_allows_bundled_tiers_and_browser(self):
        for type_name, model in [
            ("scout", "inherit"),
            ("runner", "flash_lite"),
            ("builder-flash", "flash"),
            ("research", "flash"),
            ("browser", "inherit"),
            ("image-generator", "inherit"),
        ]:
            with self.subTest(type_name=type_name, model=model):
                res = self.guard.evaluate({
                    "modelName": "gemini-4-neon-medium",
                    "toolCall": {
                        "name": "invoke_subagent",
                        "args": {"TypeName": type_name, "Model": model},
                    },
                })
                self.assertEqual(res["decision"], "allow")

    def test_invoke_subagent_denies_redundant_inherit(self):
        for type_name in ("self", "research", "unknown-agent"):
            with self.subTest(type_name=type_name):
                res = self.guard.evaluate({
                    "modelName": "gemini-4-neon-medium",
                    "toolCall": {
                        "name": "invoke_subagent",
                        "args": {"TypeName": type_name, "Model": "inherit"},
                    },
                })
                self.assertEqual(res["decision"], "deny")

    def test_swarm_add_blocks_missing_or_identical_model(self):
        for args in [
            {"action": "add", "name": "worker-1", "brief": "do work"},
            {"action": "add", "name": "worker-1", "model": "gemini-4-neon-medium"},
            {"action": "add", "name": "worker-1", "model": "Gemini 4 Neon (Medium)"},
        ]:
            with self.subTest(args=args):
                res = self.guard.evaluate({
                    "modelName": "gemini-4-neon-medium",
                    "toolCall": {"name": "swarm", "args": args},
                })
                self.assertEqual(res["decision"], "deny")

    def test_swarm_allows_different_model_and_non_add_actions(self):
        for args in [
            {"action": "add", "name": "worker-1", "model": "gemini-4-hydrogen-medium"},
            {"action": "add", "name": "worker-1", "model": "Gemini 3.8 Flash (Medium)"},
            {"action": "status"},
            {"action": "models", "all": True},
        ]:
            with self.subTest(args=args):
                res = self.guard.evaluate({
                    "modelName": "gemini-4-neon-medium",
                    "toolCall": {"name": "swarm", "args": args},
                })
                self.assertEqual(res["decision"], "allow")


if __name__ == "__main__":
    unittest.main()
