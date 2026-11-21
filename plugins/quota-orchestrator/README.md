# QuotaOrchestrator (Codex & Claude Code Package)

Shared multi-model routing plugin package for **Codex** and **Claude Code** (version **0.13.1**). Licensed under [MIT](LICENSE).

- **Codex**: installs and reconciles nine standard global routing profiles (`scout`, `researcher`, `runner`, `builder_luna`, `builder`, `visual_operator`, `writer`, `strategist`, `architect`) via a trusted `SessionStart` hook, enforces a `PreToolUse` delegation guard, and bundles the `quota-orchestrator` and `quota-orchestrator-setup` skills. See [codex/README.md](codex/README.md) (English) and [codex/README.fr.md](codex/README.fr.md) (français).
- **Claude Code**: provides five specialized agents (`scout`, `researcher`, `runner`, `builder`, `architect`), the `quota-orchestrator` skill, routing rules loaded at `SessionStart`, and a `PostToolUse` agent-identity hook. See [claude/README.md](claude/README.md) (English) and [claude/README.fr.md](claude/README.fr.md) (français).
- **Google Antigravity**: packaged natively at the repository root (`.antigravity-plugin/plugin.json`). See the [repository overview](../../README.md) and [.antigravity-plugin/README.md](../../.antigravity-plugin/README.md).

## Install

### Codex

```sh
codex plugin marketplace add masskrdjn/QuotaOrchestrator
codex plugin add quota-orchestrator@quota-orchestrator
```

### Claude Code

```sh
claude plugin marketplace add masskrdjn/QuotaOrchestrator
claude plugin install quota-orchestrator@quota-orchestrator
```
