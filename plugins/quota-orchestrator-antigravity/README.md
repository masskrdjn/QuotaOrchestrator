# QuotaOrchestrator for Antigravity (Google Gemini)

[Français](README.fr.md) · [Main repository](../../README.md)

Selective multi-model routing for **Google Gemini** models in **Google Antigravity** (App, CLI, and IDE). Delegates substantial, well-scoped work to specialized subagents and lower-cost Gemini tiers while keeping decisions, integration, and small local tasks at the primary agent.

## Prerequisites

- **Google Antigravity** (`agy` CLI, App, or IDE).
- **Python 3.11+** available on `PATH` as `python` (required by the `PreToolUse` delegation guard hook).

## Installation

### From a local checkout

```bash
agy plugin validate --strict ./plugins/quota-orchestrator-antigravity
agy plugin install ./plugins/quota-orchestrator-antigravity
agy plugin list
```

When working inside this repository, `.agents/plugins.json` also registers `plugins/quota-orchestrator-antigravity` automatically at the workspace level.

### From GitHub

```bash
agy plugin install https://github.com/masskrdjn/QuotaOrchestrator/tree/main/plugins/quota-orchestrator-antigravity
```

### Packaging and Marketplace release

Antigravity's `marketplace.json` validator (`agy plugin validate ./.antigravity-plugin/marketplace.json`) requires an `https://` archive URL and its matching `sha256` checksum. From the repository root, build and verify the deterministic `.zip` bundle before publishing a GitHub release:

```bash
python scripts/build_antigravity_bundle.py
python scripts/build_antigravity_bundle.py --check
agy plugin validate --strict ./dist/quota-orchestrator-antigravity-0.13.0.zip
```

Attach the generated `dist/quota-orchestrator-antigravity-<version>.zip` to the matching GitHub Release (`v<version>`), then verify the remote catalog with `agy plugin validate --strict ./.antigravity-plugin/marketplace.json`.

## Included components

- **7 custom subagents** (`agents/*.md`) for `invoke_subagent`:
  - `runner` (`flash_lite`) — long validation suites and independent test matrices.
  - `scout` (`flash`) — read-only codebase exploration with `path:line` evidence.
  - `researcher` (`flash`) — multi-source web and documentation research.
  - `builder-flash` (`flash`) — well-specified, reliably testable implementation.
  - `builder` (`pro`) — complex implementation requiring technical judgment.
  - `strategist` (`pro`) — read-only framing, decomposition, and specification.
  - `architect` (`pro`) — rare, high-stakes architectural decisions on a bounded brief.
- **Always-on routing rules** (`rules/AGENTS.md`) — triage thresholds, same-model/effort ban, and quota preservation.
- **On-demand routing skill** (`skills/quota-orchestrator/SKILL.md`) — full Google Gemini model & effort routing matrix for `swarm` and `agy --model` (`gemini-3.8-flash-*`, `gemini-4-hydrogen-*`, `gemini-4-neon-*`, `gemini-4-argon-*`).
- **PreToolUse delegation guard** (`hooks.json` + `scripts/check_delegation.py`) — blocks redundant delegations that would run a child on the exact same model and effort as the parent (`invoke_subagent` with `Model="inherit"` on generic roles, or `swarm` `add` with missing/identical `model`). Requires Python 3.11+ available as `python`.

## Google Gemini model tiers

| Surface | Tier / Model IDs | Typical Role |
|---|---|---|
| `invoke_subagent` | `flash_lite` | `runner` |
| `invoke_subagent` | `flash` | `scout`, `researcher`, `builder-flash` |
| `invoke_subagent` | `pro` | `builder`, `strategist`, `architect` |
| `swarm` / CLI | `gemini-3.8-flash-{low,medium,high}` | Fast validations, high-volume triage (~$0.75 / $3.75 per 1M tokens) |
| `swarm` / CLI | `gemini-4-hydrogen-{low,medium,high,xhigh}` | Structured exploration, research, specified implementation ($1.50 / $7.50 per 1M tokens) |
| `swarm` / CLI | `gemini-4-neon-{low,medium,high,xhigh}` | Default root, complex engineering, multi-file integration ($3.00 / $15.00 per 1M tokens) |
| `swarm` / CLI | `gemini-4-argon-{low,medium,high}` | Rare frontier reasoning & `architect` consultations (separate weekly quota pool) |
