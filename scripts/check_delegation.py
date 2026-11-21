#!/usr/bin/env python3
"""Offline Antigravity PreToolUse guard for QuotaOrchestrator.

Blocks redundant delegations that would execute a child agent on the exact same
model and effort as the parent session:
- `invoke_subagent`: blocks `Model="inherit"` (or omitted) when the target agent
  does not declare a distinct model tier (e.g. `self`, `research`, or a custom
  agent configured with `model: inherit`), except capability-bound built-ins
  (`browser`, `image-generator`).
- `swarm` (`action="add"`): blocks missing `model` (which inherits the
  coordinator's exact model/effort) or an explicit `model` matching the active
  parent `modelName`.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

MAX_INPUT = 1024 * 1024
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CAPABILITY_BUILTINS = {"browser", "image-generator"}
INHERIT_BUILTINS = {"self", "research"}
VALID_TIERS = {"flash_lite", "flash", "pro"}


def normalize_model(value: Any) -> str:
    """Normalize model IDs and display names to a comparable slug."""
    if not isinstance(value, str):
        return ""
    text = value.strip().lower()
    if not text:
        return ""
    # Convert display names like "Gemini 4 Neon (Medium)" -> "gemini-4-neon-medium"
    text = re.sub(r"[()]+", " ", text)
    text = re.sub(r"[^a-z0-9.]+", "-", text).strip("-")
    return text


def agent_frontmatter_model(type_name: str) -> str | None:
    """Read the `model:` field from a bundled plugin agent if present."""
    if not type_name or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", type_name.lower()):
        return None
    candidates = [
        PLUGIN_ROOT / "agents" / f"{type_name}.md",
        PLUGIN_ROOT / "agents" / type_name / "agent.md",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) < 3:
            return None
        match = re.search(r"^\s*model\s*:\s*['\"]?([a-zA-Z0-9._-]+)['\"]?\s*$", parts[1], re.MULTILINE)
        return match.group(1).strip().lower() if match else "inherit"
    return None


def allow() -> dict[str, Any]:
    return {"decision": "allow"}


def deny(reason: str) -> dict[str, Any]:
    return {"decision": "deny", "reason": reason}


def check_invoke_subagent(args: dict[str, Any]) -> dict[str, Any]:
    type_name = str(args.get("TypeName") or "").strip().lower()
    if type_name in CAPABILITY_BUILTINS:
        return allow()

    requested_model = str(args.get("Model") or "inherit").strip().lower()
    if requested_model in VALID_TIERS:
        return allow()

    if requested_model not in {"", "inherit"}:
        return allow()

    if type_name in INHERIT_BUILTINS:
        return deny(
            f"QuotaOrchestrator: délégation '{type_name}' refusée avec Model='inherit' "
            "(même modèle et même effort que la racine). Choisissez un palier inférieur "
            "(flash_lite/flash) ou gardez la tâche à la racine."
        )

    profile_model = agent_frontmatter_model(type_name)
    if profile_model in VALID_TIERS:
        return allow()

    if profile_model in {None, "inherit"}:
        return deny(
            f"QuotaOrchestrator: délégation '{type_name or 'inconnue'}' refusée sans palier "
            "distinct (Model='inherit'). Précisez flash_lite, flash ou pro, ou traitez à la racine."
        )
    return allow()


def check_swarm(args: dict[str, Any], parent_model: str) -> dict[str, Any]:
    action = str(args.get("action") or "").strip().lower()
    if action != "add":
        return allow()

    raw_child_model = args.get("model")
    child_model = normalize_model(raw_child_model)
    if not child_model or child_model in {"inherit", "default", "auto"}:
        return deny(
            "QuotaOrchestrator: swarm add refusé sans 'model' explicite "
            "(hériterait du même modèle et du même effort que la racine). "
            "Spécifiez un modèle cible (ex. gemini-3.8-flash-medium, gemini-4-hydrogen-high) "
            "ou gardez le travail à la racine."
        )

    parent_slug = normalize_model(parent_model)
    if parent_slug and parent_slug not in {"auto", "default"} and child_model == parent_slug:
        return deny(
            f"QuotaOrchestrator: swarm add refusé pour '{raw_child_model}' "
            f"(identique au modèle/effort racine '{parent_model}'). "
            "Choisissez un palier moins coûteux ou traitez la tâche à la racine."
        )

    return allow()


def evaluate(event: dict[str, Any]) -> dict[str, Any]:
    tool_call = event.get("toolCall")
    if not isinstance(tool_call, dict):
        return allow()
    tool_name = str(tool_call.get("name") or "").strip().lower()
    args = tool_call.get("args")
    if not isinstance(args, dict):
        args = {}

    if tool_name == "invoke_subagent":
        return check_invoke_subagent(args)
    if tool_name == "swarm":
        return check_swarm(args, str(event.get("modelName") or ""))
    return allow()


def main() -> int:
    raw = sys.stdin.read(MAX_INPUT)
    if not raw.strip():
        print(json.dumps(allow()))
        return 0
    try:
        event = json.loads(raw)
    except ValueError:
        print(json.dumps(allow()))
        return 0
    result = evaluate(event if isinstance(event, dict) else {})
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
