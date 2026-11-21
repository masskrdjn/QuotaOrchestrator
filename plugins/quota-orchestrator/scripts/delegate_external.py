"""Run one explicitly requested mission through an installed agent CLI."""

import argparse
from contextlib import nullcontext
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


PROVIDERS = {
    "codex": [
        "exec", "--sandbox", "read-only", "--ephemeral", "--color", "never",
        "--skip-git-repo-check",
    ],
    "claude": [
        "--permission-mode", "plan", "--output-format", "text", "--disable-slash-commands",
    ],
    "grok": ["--permission-mode", "plan", "--output-format", "plain"],
    "agy": ["--mode", "plan", "--sandbox", "--output-format", "text", "--disable-slash-commands"],
}

NODE_ENTRIES = {
    "codex": "@openai/codex/bin/codex.js",
    "grok": "@xai-official/grok/bin/grok",
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
    shim_dir = Path(shim).parent
    modules = shim_dir / "node_modules"
    if provider == "claude":
        executable = modules / "@anthropic-ai/claude-code/bin/claude.exe"
        return [str(executable)] if executable.is_file() else None
    if provider in NODE_ENTRIES:
        entry = modules / NODE_ENTRIES[provider]
        local_node = shim_dir / "node.exe"
        node = str(local_node) if local_node.is_file() else shutil.which("node.exe")
        return [node, str(entry)] if node and entry.is_file() else None
    return None


def delegate(provider, mission, model, effort, timeout):
    result = {"provider": provider}
    try:
        command = executable_command(provider)
    except FileNotFoundError as exc:
        return {**result, "status": "unavailable", "error": str(exc)}
    except OSError as exc:
        return {**result, "status": "failed", "error": str(exc)}
    if command is None:
        return {**result, "status": "unavailable", "error": f"{provider} was not found on PATH."}

    command += PROVIDERS[provider]
    if model:
        command.append(f"--model={model}")
    if effort:
        if provider == "codex":
            command.extend(["-c", f"model_reasoning_effort={json.dumps(effort, ensure_ascii=False)}"])
        else:
            command.append(f"--effort={effort}")

    try:
        temp_dir = tempfile.TemporaryDirectory() if provider in {"codex", "grok"} else nullcontext()
        with temp_dir as directory:
            output_path = None
            prompt_input = {"stdin": subprocess.DEVNULL}
            process_timeout = timeout
            if provider == "codex":
                output_path = Path(directory) / "last-message.txt"
                command.extend(["-o", str(output_path), "-"])
                prompt_input = {"input": mission}
            elif provider == "claude":
                command.append("--print")
                prompt_input = {"input": mission}
            elif provider == "grok":
                prompt_path = Path(directory) / "mission.txt"
                prompt_path.write_bytes(mission.encode("utf-8"))
                command.extend(["--prompt-file", str(prompt_path)])
            else:
                command.extend([f"--print-timeout={timeout}s", f"--print={mission}"])
                process_timeout += 1  # Let Antigravity handle its own deadline first.

            try:
                response = subprocess.run(
                    command,
                    **prompt_input,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=process_timeout,
                    check=False,
                )
            except FileNotFoundError as exc:
                return {**result, "status": "unavailable", "error": str(exc)}

            if response.returncode:
                return {
                    **result, "status": "failed", "exit_code": response.returncode,
                    "error": (response.stderr.strip() or response.stdout.strip())[-2000:],
                }

            message = ""
            if output_path is not None:
                try:
                    message = output_path.read_text(encoding="utf-8", errors="replace").strip()
                except FileNotFoundError:
                    pass
            message = message or response.stdout.strip()
    except subprocess.TimeoutExpired:
        return {**result, "status": "timeout", "error": f"CLI exceeded {process_timeout} seconds."}
    except OSError as exc:
        return {**result, "status": "failed", "error": str(exc)}

    if not message:
        return {**result, "status": "failed", "error": "CLI returned an empty response."}
    return {**result, "status": "ok", "response": message}


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
