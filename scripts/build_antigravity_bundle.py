#!/usr/bin/env python3
"""Build a deterministic Antigravity plugin .zip bundle and update marketplace.json.

Usage:
  python scripts/build_antigravity_bundle.py
  python scripts/build_antigravity_bundle.py --check
  python scripts/build_antigravity_bundle.py --url https://example.com/plugin.zip
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / ".antigravity-plugin/plugin.json"
MARKETPLACE_PATH = ROOT / ".antigravity-plugin/marketplace.json"
DIST_DIR = ROOT / "dist"
DEFAULT_RELEASE_BASE = "https://github.com/masskrdjn/QuotaOrchestrator/releases/download"
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)

# Exact files and directories bundled into the standalone Antigravity .zip release.
BUNDLE_FILES = (
    ".antigravity-plugin/plugin.json",
    ".antigravity-plugin/README.md",
    ".antigravity-plugin/README.fr.md",
    "hooks.json",
    "scripts/check_delegation.py",
    "scripts/check_updates.py",
    "plugins/quota-orchestrator/scripts/delegate_external.py",
)
BUNDLE_DIRS = (
    "assets",
    "agents",
    "rules",
    "skills",
)


def read_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def default_bundle_url(version: str) -> str:
    return f"{DEFAULT_RELEASE_BASE}/v{version}/quota-orchestrator-antigravity-{version}.zip"


def collect_bundle_paths(root: Path = ROOT) -> list[Path]:
    paths: list[Path] = []
    for rel in BUNDLE_FILES:
        path = root / rel
        if path.is_file():
            paths.append(path)
    for rel_dir in BUNDLE_DIRS:
        directory = root / rel_dir
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            paths.append(path)
    return sorted(set(paths), key=lambda p: p.relative_to(root).as_posix())


def build_zip_bytes(root: Path = ROOT) -> bytes:
    """Create a reproducible zip archive of the Antigravity plugin."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in collect_bundle_paths(root):
            rel = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(filename=rel, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if rel.startswith("scripts/") else 0o644
            info.external_attr = (0o100000 | mode) << 16
            content = path.read_bytes()
            if path.suffix in {".json", ".md", ".py"}:
                content = content.replace(b"\r\n", b"\n")
            zf.writestr(info, content)
    return buffer.getvalue()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Override HTTPS URL written into marketplace.json")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that marketplace.json matches the current plugin bundle without writing files.",
    )
    args = parser.parse_args(argv)

    manifest = read_manifest()
    version = manifest["version"]
    url = args.url or default_bundle_url(version)
    archive_bytes = build_zip_bytes(ROOT)
    digest = sha256_hex(archive_bytes)

    if args.check:
        marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
        entry, = marketplace["plugins"]
        source = entry["source"]
        if source.get("url") != url:
            print(f"MISMATCH url: expected {url}, got {source.get('url')}", file=sys.stderr)
            return 1
        if source.get("sha256") != digest:
            print(f"MISMATCH sha256: expected {digest}, got {source.get('sha256')}", file=sys.stderr)
            return 1
        print(f"OK: marketplace.json matches deterministic bundle v{version} ({digest})")
        return 0

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DIST_DIR / f"quota-orchestrator-antigravity-{version}.zip"
    out_path.write_bytes(archive_bytes)

    marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    entry, = marketplace["plugins"]
    entry["source"] = {
        "source": "url",
        "url": url,
        "sha256": digest,
    }
    MARKETPLACE_PATH.write_text(json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Built {out_path.relative_to(ROOT)} ({len(archive_bytes)} bytes)")
    print(f"SHA-256: {digest}")
    print(f"Updated {MARKETPLACE_PATH.relative_to(ROOT)} -> {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
