"""Run with: python test_plugin.py"""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PLUGIN = ROOT.parent
REPOSITORY = PLUGIN.parents[1]
ROLES = ["architect", "builder", "researcher", "runner", "scout"]
# Champs de frontmatter qu'un agent de plugin voit ignorés.
IGNORED = ("hooks", "mcpServers", "permissionMode")


if __name__ == "__main__":
    manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((REPOSITORY / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))

    assert manifest["name"] == marketplace["name"] == marketplace["plugins"][0]["name"] == "quota-orchestrator"
    assert (REPOSITORY / marketplace["plugins"][0]["source"]).resolve() == PLUGIN

    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"]), "release version required"
    entry = marketplace["plugins"][0]
    assert "version" not in entry, "keep plugin.json as the only version source"
    settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
    for config, variable, prefix in [(manifest, "CLAUDE_PLUGIN_ROOT", "claude/"),
                                      (settings, "CLAUDE_PROJECT_DIR", "")]:
        hook = config["hooks"]["PostToolUse"][0]
        assert hook["matcher"] == "Agent|Task|TaskOutput"
        command = hook["hooks"][0]["command"]
        assert command == 'python "${' + variable + '}/' + prefix + '.claude/hooks/agent_identity.py"'
        assert (ROOT / ".claude/hooks/agent_identity.py").is_file()

    agents = sorted((PLUGIN / "agents").glob("*.md"))
    for path in agents:
        assert path.read_bytes() == (ROOT / ".claude/agents" / path.name).read_bytes()
    assert sorted(path.stem for path in agents) == ROLES, agents
    assert sorted(path.stem for path in (ROOT / ".claude/agents").glob("*.md")) == ROLES
    for path in agents:
        head = path.read_text(encoding="utf-8").split("---")[1]
        assert not re.search(rf"^({'|'.join(IGNORED)}):", head, re.M), f"{path.name}: champ ignoré par le plugin"
        # Un « : » non guillemeté invalide le YAML : le runtime perd alors model et tools.
        for line in head.strip().splitlines():
            key, _, value = line.partition(": ")
            assert value[:1] in "\"'" or ": " not in value and " #" not in value, f"{path.name}: {key} à mettre entre guillemets"
        assert re.search(r"^model: \S", head, re.M) and re.search(r"^tools: \S", head, re.M), f"{path.name}: model ou tools absent"
    assert (PLUGIN / manifest["skills"] / "quota-orchestrator/SKILL.md").is_file()

    hook = manifest["hooks"]["SessionStart"][0]
    assert {"startup", "resume", "clear", "compact"} <= set(hook["matcher"].split("|"))
    target = re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"]+)", hook["hooks"][0]["command"]).group(1)
    assert (PLUGIN / target).samefile(ROOT / "CLAUDE.md"), target

    print("PASS: manifestes, cinq rôles, skill, version unique et hooks SessionStart/PostToolUse.")
