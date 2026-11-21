"""Run one explicitly requested mission through an installed agent CLI."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


PROVIDERS = {
    "claude": ["--permission-mode", "plan", "--output-format", "text"],
    "grok": ["--permission-mode", "plan", "--output-format", "plain"],
    "agy": ["--mode", "plan", "--sandbox", "--output-format", "text"],
}


def executable_command(provider):
    if os.name != "nt":
        executable = shutil.which(provider)
        return [executable] if executable else None

    executable = shutil.which(f"{provider}.exe")
    if executable:
        return [executable]

    # npm's Windows shims go through a shell. Resolve their known entry points
    # directly so mission text is always passed as data.
    shim = shutil.which(f"{provider}.cmd")
    if shim is None:
        return None
    modules = Path(shim).parent / "node_modules"
    if provider == "claude":
        executable = modules / "@anthropic-ai/claude-code/bin/claude.exe"
        return [str(executable)] if executable.is_file() else None
    if provider == "grok":
        entry = modules / "@xai-official/grok/bin/grok"
        node = shutil.which("node.exe")
        return [node, str(entry)] if node and entry.is_file() else None
    return None


def delegate(provider, mission, model, effort, timeout):
    result = {"provider": provider}
    command = executable_command(provider)
    if command is None:
        return {**result, "status": "unavailable", "error": f"{provider} was not found on PATH."}

    command += PROVIDERS[provider]
    if model:
        command.append(f"--model={model}")
    if effort:
        command.append(f"--effort={effort}")
    if provider == "claude":
        command.append("--print")
        prompt_input = {"input": mission}
    elif provider == "grok":
        command.append(f"--single={mission}")
        prompt_input = {"stdin": subprocess.DEVNULL}
    else:
        command.append(f"--print={mission}")
        prompt_input = {"stdin": subprocess.DEVNULL}
    try:
        response = subprocess.run(
            command,
            **prompt_input,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {**result, "status": "timeout", "error": f"CLI exceeded {timeout} seconds."}
    except OSError as exc:
        return {**result, "status": "unavailable", "error": str(exc)}

    if response.returncode:
        return {
            **result, "status": "failed", "exit_code": response.returncode,
            "error": (response.stderr.strip() or response.stdout.strip())[-2000:],
        }
    if not response.stdout.strip():
        return {**result, "status": "failed", "error": "CLI returned an empty response."}
    return {**result, "status": "ok", "response": response.stdout.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=PROVIDERS)
    parser.add_argument("mission", type=Path, help="UTF-8 file containing the mission and context")
    parser.add_argument("--model", help="Model ID accepted by the target CLI")
    parser.add_argument("--effort", help="Effort accepted by the target CLI and model")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        mission = args.mission.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if not mission.strip() or "\0" in mission:
        parser.error("the mission must be nonempty UTF-8 text without NUL characters")

    result = delegate(args.provider, mission, args.model, args.effort, args.timeout)
    print(json.dumps(result))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
