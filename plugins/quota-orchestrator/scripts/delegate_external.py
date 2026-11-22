"""Run one explicitly requested mission through an installed agent CLI."""

import argparse
from contextlib import nullcontext
import json
import os
from pathlib import Path
import re
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

WRITE_PROVIDERS = {
    "codex": [
        "exec", "--sandbox", "workspace-write", "--ephemeral", "--color", "never",
        "--skip-git-repo-check",
    ],
    "claude": [
        "--permission-mode", "acceptEdits", "--output-format", "text", "--disable-slash-commands",
    ],
    "grok": ["--permission-mode", "acceptEdits", "--output-format", "plain"],
    "agy": [
        "--mode", "accept-edits", "--sandbox", "--output-format", "text",
        "--disable-slash-commands",
    ],
}

MODES = ("read", "write")

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


def parse_fallback(spec):
    parts = spec.split(":", 2)
    provider = parts[0].strip()
    if provider not in PROVIDERS:
        raise ValueError(f"unknown fallback provider {provider!r}; choose from {', '.join(PROVIDERS)}")
    model = parts[1].strip() or None if len(parts) >= 2 else None
    effort = parts[2].strip() or None if len(parts) == 3 else None
    return provider, model, effort


def _parse_model_list(provider, stdout):
    models = []
    seen = set()
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if provider == "grok":
            match = re.match(r"^\*\s+([A-Za-z0-9._-]+)", line)
            if match:
                model_id = match.group(1)
                if model_id not in seen:
                    seen.add(model_id)
                    models.append(model_id)
        elif provider == "agy":
            token = line.split()[0]
            if re.fullmatch(r"[a-z0-9][a-z0-9._-]*", token) and token not in seen:
                seen.add(token)
                models.append(token)
    return models


def list_models(provider, timeout=15):
    result = {"provider": provider}
    try:
        command = executable_command(provider)
    except FileNotFoundError as exc:
        return {**result, "status": "unavailable", "error": str(exc)}
    except OSError as exc:
        return {**result, "status": "failed", "error": str(exc)}
    if command is None:
        return {**result, "status": "unavailable", "error": f"{provider} was not found on PATH."}
    if provider not in {"agy", "grok"}:
        return {
            **result,
            "status": "ok",
            "models": [],
            "note": f"{provider} does not expose a non-interactive model listing subcommand.",
        }
    try:
        response = subprocess.run(
            [*command, "models"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {**result, "status": "unavailable", "error": str(exc)}
    except subprocess.TimeoutExpired:
        return {**result, "status": "timeout", "error": f"CLI exceeded {timeout} seconds."}
    except OSError as exc:
        return {**result, "status": "failed", "error": str(exc)}

    if response.returncode:
        return {
            **result,
            "status": "failed",
            "exit_code": response.returncode,
            "error": (response.stderr.strip() or response.stdout.strip())[-2000:],
        }
    return {**result, "status": "ok", "models": _parse_model_list(provider, response.stdout)}


def _model_is_listed(provider, model, effort, models):
    if not models:
        return True
    model_set = set(models)
    if model in model_set:
        return True
    if provider == "agy":
        if effort and f"{model}-{effort}" in model_set:
            return True
        if not effort and any(item.startswith(f"{model}-") for item in model_set):
            return True
    return False


def _delegate_once(provider, mission, model, effort, timeout, mode="read", check_models=False):
    result = {"provider": provider}
    if mode not in MODES:
        return {**result, "status": "failed", "error": f"Unsupported mode {mode!r}."}
    try:
        command = executable_command(provider)
    except FileNotFoundError as exc:
        return {**result, "status": "unavailable", "error": str(exc)}
    except OSError as exc:
        return {**result, "status": "failed", "error": str(exc)}
    if command is None:
        return {**result, "status": "unavailable", "error": f"{provider} was not found on PATH."}

    if check_models and model and provider in {"agy", "grok"}:
        listing = list_models(provider, min(timeout, 15))
        if listing["status"] != "ok":
            return listing
        if not _model_is_listed(provider, model, effort, listing.get("models", ())):
            target = f"{model}-{effort}" if (provider == "agy" and effort and not model.endswith(f"-{effort}")) else model
            return {
                **result,
                "status": "unavailable",
                "error": f"Model '{target}' is not available in {provider} models for this account.",
            }

    provider_flags = WRITE_PROVIDERS[provider] if mode == "write" else PROVIDERS[provider]
    command += provider_flags
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


def delegate(
    provider,
    mission,
    model=None,
    effort=None,
    timeout=120,
    *,
    mode="read",
    fallbacks=(),
    check_models=False,
):
    parsed_fallbacks = [
        fb if isinstance(fb, tuple) else parse_fallback(fb)
        for fb in fallbacks
    ]
    candidates = [(provider, model, effort), *parsed_fallbacks]
    attempts = []
    requested = {"provider": provider, "model": model, "effort": effort}
    last_result = None

    for index, (cand_provider, cand_model, cand_effort) in enumerate(candidates):
        outcome = _delegate_once(
            cand_provider,
            mission,
            cand_model,
            cand_effort,
            timeout,
            mode=mode,
            check_models=check_models,
        )
        if outcome["status"] == "ok":
            if index == 0 and mode == "read" and not parsed_fallbacks and not check_models:
                return outcome
            enriched = dict(outcome)
            if mode != "read":
                enriched["mode"] = mode
            if cand_model is not None:
                enriched["model"] = cand_model
            if cand_effort is not None:
                enriched["effort"] = cand_effort
            if index > 0:
                enriched["fallback_used"] = True
                enriched["requested"] = requested
                enriched["attempts"] = attempts
            return enriched

        last_result = dict(outcome)
        if mode != "read":
            last_result["mode"] = mode
        attempt_record = {
            "provider": cand_provider,
            "model": cand_model,
            "effort": cand_effort,
            "status": outcome["status"],
            "error": outcome.get("error", ""),
        }
        if "exit_code" in outcome:
            attempt_record["exit_code"] = outcome["exit_code"]
        attempts.append(attempt_record)

        # Do not trigger fallbacks after a timeout to avoid compounding long stalls.
        if outcome["status"] == "timeout":
            break

    if parsed_fallbacks:
        last_result["fallback_used"] = False
        last_result["requested"] = requested
        last_result["attempts"] = attempts
    return last_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=PROVIDERS)
    parser.add_argument("mission", nargs="?", type=Path, help="UTF-8 file containing the mission and context")
    parser.add_argument("--model", help="Model ID accepted by the target CLI")
    parser.add_argument("--effort", help="Effort accepted by the target CLI and model")
    parser.add_argument("--mode", choices=MODES, default="read", help="Execution mode: read (plan/read-only) or write (workspace edits)")
    parser.add_argument(
        "--fallback",
        action="append",
        default=[],
        metavar="PROVIDER[:MODEL[:EFFORT]]",
        help="Ordered fallback target tried when the previous CLI or model is unavailable or fails (repeatable)",
    )
    parser.add_argument(
        "--check-models",
        action="store_true",
        help="Verify that the requested model is exposed by 'agy models' or 'grok models' before running",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List models exposed by the target CLI account and exit",
    )
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    if args.list_models:
        result = list_models(args.provider, args.timeout)
        print(json.dumps(result))
        return 0 if result["status"] == "ok" else 1

    if args.mission is None:
        parser.error("the following arguments are required: mission")

    try:
        parsed_fallbacks = [parse_fallback(item) for item in args.fallback]
    except ValueError as exc:
        parser.error(str(exc))

    try:
        mission = args.mission.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if not mission.strip() or "\0" in mission:
        parser.error("the mission must be nonempty UTF-8 text without NUL characters")

    if args.mode == "read" and not parsed_fallbacks and not args.check_models:
        result = delegate(args.provider, mission, args.model, args.effort, args.timeout)
    else:
        result = delegate(
            args.provider,
            mission,
            args.model,
            args.effort,
            args.timeout,
            mode=args.mode,
            fallbacks=parsed_fallbacks,
            check_models=args.check_models,
        )
    print(json.dumps(result))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
