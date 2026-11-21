#!/usr/bin/env python3
"""Antigravity SessionStart update checker for QuotaOrchestrator.

Checks once per 2-hour TTL whether a newer version of QuotaOrchestrator is
available on GitHub, and emits a non-blocking systemMessage if an update is
found. Never modifies files inside the plugin and always fails open (exit 0)
when offline or unreachable.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PLUGIN_ROOT / ".antigravity-plugin" / "plugin.json"
DEFAULT_REMOTE_URL = (
    "https://raw.githubusercontent.com/masskrdjn/QuotaOrchestrator/"
    "main/.antigravity-plugin/plugin.json"
)
REPO_URL = "https://github.com/masskrdjn/QuotaOrchestrator"
DEFAULT_TTL_SECONDS = 2 * 60 * 60  # 2 hours
DEFAULT_TIMEOUT_SECONDS = 2.0
MAX_RESPONSE_BYTES = 64 * 1024
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_semver(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = SEMVER_RE.fullmatch(value.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def read_local_version(manifest_path: Path = MANIFEST_PATH) -> str | None:
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    version = data.get("version") if isinstance(data, dict) else None
    return version.strip() if isinstance(version, str) and parse_semver(version) else None


def default_cache_path() -> Path:
    override = os.environ.get("QUOTA_ORCHESTRATOR_CACHE_PATH")
    if override:
        return Path(override)
    return Path(tempfile.gettempdir()) / "quota-orchestrator-antigravity" / "update_check.json"


def read_cache(cache_path: Path) -> dict[str, Any] | None:
    try:
        if not cache_path.is_file() or cache_path.is_symlink():
            return None
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def write_cache(cache_path: Path, payload: dict[str, Any]) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        if cache_path.parent.is_symlink():
            return
        fd, tmp_name = tempfile.mkstemp(dir=cache_path.parent, prefix=".update-check-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=True)
            os.replace(tmp_name, cache_path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
    except OSError:
        return


def fetch_remote_version(url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> str | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "QuotaOrchestrator-UpdateCheck/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_RESPONSE_BYTES)
        data = json.loads(raw.decode("utf-8"))
    except (OSError, urllib.error.URLError, ValueError, UnicodeDecodeError):
        return None
    version = data.get("version") if isinstance(data, dict) else None
    return version.strip() if isinstance(version, str) and parse_semver(version) else None


def check_for_update(
    *,
    local_version: str | None = None,
    cache_path: Path | None = None,
    remote_url: str | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now: float | None = None,
    fetcher: Callable[[str], str | None] | None = None,
) -> dict[str, Any]:
    if os.environ.get("QUOTA_ORCHESTRATOR_DISABLE_UPDATE_CHECK") == "1":
        return {}

    current = local_version if local_version is not None else read_local_version()
    current_tuple = parse_semver(current)
    if current_tuple is None:
        return {}

    target_cache = cache_path or default_cache_path()
    current_time = time.time() if now is None else now
    cached = read_cache(target_cache)

    remote_version: str | None = None
    cache_fresh = False
    if cached is not None:
        checked_at = cached.get("checked_at")
        if isinstance(checked_at, (int, float)) and 0 <= (current_time - checked_at) < ttl_seconds:
            cache_fresh = True
            cached_remote = cached.get("remote_version")
            if isinstance(cached_remote, str) and parse_semver(cached_remote):
                remote_version = cached_remote.strip()

    if not cache_fresh:
        url = remote_url or os.environ.get("QUOTA_ORCHESTRATOR_UPDATE_URL") or DEFAULT_REMOTE_URL
        fetch_fn = fetcher or fetch_remote_version
        remote_version = fetch_fn(url)
        write_cache(
            target_cache,
            {
                "checked_at": current_time,
                "remote_version": remote_version,
            },
        )

    remote_tuple = parse_semver(remote_version)
    if remote_tuple is None or remote_tuple <= current_tuple:
        return {}

    return {
        "systemMessage": (
            f"QuotaOrchestrator: mise à jour disponible ({current} → {remote_version}). "
            f"Pour mettre à jour : agy plugin uninstall quota-orchestrator && "
            f"agy plugin install {REPO_URL}"
        )
    }


def main() -> int:
    # Drain stdin if provided by the host without failing on empty/malformed payloads.
    try:
        if not sys.stdin.isatty():
            sys.stdin.read(MAX_RESPONSE_BYTES)
    except OSError:
        pass
    result = check_for_update()
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
