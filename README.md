# QuotaOrchestrator — Multi-Model Routing

[Français](README.fr.md)

To modify this repository, read [CONTRIBUTING.md](CONTRIBUTING.md).
See [CHANGELOG.md](CHANGELOG.md) for changes.

> [!IMPORTANT]
> Current plugin version: **0.15.0**.
>
> One repository, three native integrations: **Codex** (OpenAI), **Claude Code** (Anthropic), and **Google Antigravity** (Google Gemini).

QuotaOrchestrator provides selective multi-model routing plugins for **Codex**, **Claude Code**, and **Google Antigravity**. It delegates substantial, well-scoped work to specialized agents on lower-cost or task-matched model tiers when delegation preserves quality while reducing total cost or latency. The primary agent remains responsible for triage, decisions, integration, and user communication.

## Supported platforms at a glance

| Platform | Model family | Agents / profiles | Hooks & guards | Full guide |
|---|---|---|---|---|
| **Codex** | OpenAI GPT-6 Luna, Sol (5.6 / 6 / 6.1 / 6.2), Terra 6.1, Astra 6.2 | 9 standard profiles + 2 optional `_complex` variants | `SessionStart` profile reconciliation + `PreToolUse` delegation guard | [Codex guide](plugins/quota-orchestrator/codex/README.md) ([FR](plugins/quota-orchestrator/codex/README.fr.md)) |
| **Claude Code** | Anthropic Haiku 5.5, Sonnet 5.5, Opus 5.5, Fable 5.2 | 5 specialized agents (`scout`, `researcher`, `runner`, `builder`, `architect`) | `SessionStart` rule injection + `PostToolUse` observed-identity hook | [Claude Code guide](plugins/quota-orchestrator/claude/README.md) ([FR](plugins/quota-orchestrator/claude/README.fr.md)) |
| **Google Antigravity** | Google Gemini 3.8 Flash, Gemini 4 Hydrogen, Neon, Argon | 7 native subagents (`invoke_subagent`) + `swarm` / CLI model routing | `PreToolUse` delegation guard + `SessionStart` update checker (2h TTL) | [Antigravity guide](.antigravity-plugin/README.md) ([FR](.antigravity-plugin/README.fr.md)) |

## Quick start

All three plugins require **Python 3.11+** available on `PATH` as `python` for their bundled hooks.

### Codex

```sh
codex plugin marketplace add masskrdjn/QuotaOrchestrator
codex plugin add quota-orchestrator@quota-orchestrator
```

1. From a local checkout, replace the first command with `codex plugin marketplace add .`.
2. When Codex prompts you, review and trust the bundled `SessionStart` and `PreToolUse` hooks to configure the nine standard global profiles and enforce the delegation guard.
3. Open a new Codex task to load the profiles.

Migrating from **CodexSkills** or installing manually without the plugin? See the [Codex guide](plugins/quota-orchestrator/codex/README.md#migrate-from-codexskills).

### Claude Code

```sh
claude plugin marketplace add masskrdjn/QuotaOrchestrator
claude plugin install quota-orchestrator@quota-orchestrator
```

1. From a local checkout, use `claude plugin marketplace add ./` (or `claude --plugin-dir ./plugins/quota-orchestrator` for a single session without installing).
2. Start a new session or run `/reload-plugins`.
3. Plugin components are namespaced as `quota-orchestrator:<role>` and `quota-orchestrator:quota-orchestrator`. On Windows, the `SessionStart` hook requires a POSIX shell (Git Bash).

Migrating from **ClaudeSkills**, installing per project with `install.py`, or measuring session costs with `extract_claude_jsonl.ps1`? See the [Claude Code guide](plugins/quota-orchestrator/claude/README.md#install-as-a-plugin).

### Google Antigravity

```sh
agy plugin install https://github.com/masskrdjn/QuotaOrchestrator
```

1. From a local checkout, run `agy plugin validate .` then `agy plugin install .` (and `agy plugin list` to verify).
2. The plugin installs 7 native subagents (`agents/*.md`), always-on routing rules (`rules/AGENTS.md`), the on-demand `quota-orchestrator` skill (`skills/quota-orchestrator/SKILL.md`), and the `PreToolUse` guard (`hooks.json`).
3. Use `invoke_subagent` for tier-based delegation (`flash_lite`, `flash`, `pro`) and `swarm` or `agy --model` when exact Google Gemini model/effort selection is needed.

Packaging a release `.zip` bundle or validating the Antigravity catalog? See the [Antigravity guide](.antigravity-plugin/README.md).

## Shared routing policy

Priorities across all three platforms, in order:

1. **Preserve result quality and relevance.**
2. **Reduce total cost in API dollars** (tokens of each type × the model's rate, including root coordination, integration, and rework — more tokens on a cheaper tier is a good trade at equal quality), while preserving scarce frontier/weekly quotas (Astra, Fable, Argon).
3. **Reduce latency.**

Core rules:

- **Keep small, bounded work at the root.** Local edits, single-source lookups, direct checks, and tasks whose point of entry is already known do not amortize delegation overhead.
- **Same model and same effort → stay at the root.** This rule takes precedence over every delegation criterion, including independent reviews; a different role name is insufficient and settings must not be altered to bypass it. Codex and Antigravity enforce this via synchronous `PreToolUse` hooks.
- **Same model at higher effort → stay at the root by default.** Delegate only for a specific quality or latency need, or when comparable runs demonstrate lower total cost.
- **Lean hot path.** Always-on instructions (`AGENTS.md`, `CLAUDE.md`, `rules/AGENTS.md`) cover everyday triage and standard roles. Load the `quota-orchestrator` skill on demand only for escalations, custom model/effort choices, independent reviews, or cost comparisons.
- **Delegation transfers execution, not responsibility.** The primary agent reconciles child reports, inspects targeted `path:line` evidence (without re-reading entire files, which would cancel the savings), and never promotes a child's hypothesis into an established fact.
- **Measure before claiming savings.** Without comparable complete runs, a routing choice is an expected gain, not a demonstrated saving. Incomplete runs (`Complete = false`) are `non observable` and excluded from ratios and economic conclusions.

## Roles across platforms

| Role | Responsibility | Codex (fallback) | Claude Code | Google Antigravity (`invoke_subagent` / `swarm`) |
|---|---|---|---|---|
| **Primary** | Triage, decisions, integration, small local tasks | User-selected | `opus` (`xhigh`) | User-selected (typically `gemini-4-neon-*`) |
| `runner` | Long validation suites, test matrices, mechanical batches | `gpt-6-luna` (`high`) | `claude-haiku-5-5` (`medium`) | `flash_lite` / `gemini-3.8-flash-*` |
| `scout` | Read-only codebase & log exploration with `path:line` evidence | `gpt-6-luna` (`high`) | `sonnet` (`medium`) | `flash` / `gemini-4-hydrogen-*` |
| `researcher` | Multi-source external web & documentation research | `gpt-6-luna` (`high`) | `sonnet` (`medium`) | `flash` / `gemini-4-hydrogen-*` |
| `builder_luna` / `builder-flash` | Substantial, fully specified, reliably testable implementation | `gpt-6-luna` (`max`) | — (use `builder`) | `flash` / `gemini-4-hydrogen-*` |
| `builder` | Implementation requiring design, tradeoffs, or delicate integration | `gpt-6.2-sol` (`high`) | `sonnet` (`high`, escalate to `opus`) | `pro` / `gemini-4-neon-*` |
| `strategist` | Read-only complex framing, decomposition, and specification | `gpt-6.2-sol` (`medium`) | — | `pro` / `gemini-4-neon-*` |
| `architect` | Rare, bounded architectural decisions on an assembled brief | `gpt-6.2-astra` (`low`) | `opus` (`xhigh`) or `fable` (on confirmed access) | `pro` / `gemini-4-argon-*` |
| `visual_operator` | Visual inspection and bounded UI workflows | `gpt-6.1-terra` (`medium`) | — | Built-in `browser` subagent |
| `writer` | Substantial drafting or rewriting from established facts | `gpt-6.1-terra` (`medium`) | — | — |
| `scout_complex` / `researcher_complex` | Optional high-capacity exploration/synthesis when standard tier is insufficient | `gpt-6.2-sol` (`xhigh`) | — | `swarm` (`gemini-4-neon-*`) |

For full model pricing tables, effort selection grids, escalation gates, and platform-specific details, see the dedicated [Codex](plugins/quota-orchestrator/codex/README.md), [Claude Code](plugins/quota-orchestrator/claude/README.md), and [Antigravity](.antigravity-plugin/README.md) guides.

## External delegation (experimental)

In Codex, Claude Code, or Antigravity, ask QuotaOrchestrator to use the `external-delegation` skill
and name the target CLI and the context it may receive. For example, ask it
to send an excerpt to Grok Build for analysis, delegate a full-repository audit
to Antigravity (`gemini-4-neon-high`), or assign an isolated implementation lot
in `--mode write`. The plugin ships the shared helper and requires Python 3.11+
and an installed, authenticated target CLI on the terminal's `PATH`.

From the mission's working directory, the skill runs the bundled helper:

```text
python "<plugin directory>/scripts/delegate_external.py" claude mission.txt --mode read --model opus --effort high --check-models --fallback agy:claude-opus-5-5-high --fallback codex:gpt-6.2-sol:xhigh
```

The UTF-8 file contains a self-contained mission and its context so the target
CLI can amortize its cold start over its own internal warm-cache tool loop.
Choose `codex`, `claude`, `grok`, or `agy`. By default (`--mode read`), the
helper requests read-only mode for Codex and plan mode for the other CLIs;
`--mode write` enables bounded workspace edits (`workspace-write` on Codex,
`acceptEdits` on Claude Code and Grok Build, `accept-edits` with `--sandbox`
on Antigravity) without bypassing permission guards.

Pass repeatable `--fallback <provider>[:<model>[:<effort>]]` options to define
an ordered fallback chain when a target CLI or model is unavailable or
restricted on the current plan (such as Claude without Fable 5.2 access or a
free-tier Grok account), and `--check-models` (or `--list-models`) to verify
whether the active `agy` or `grok` subscription exposes the requested model
(including hosted Claude Sonnet/Opus 5.5 models on paid `agy` accounts) before
running. When a fallback executes, the JSON response reports `fallback_used`,
`requested`, and `attempts` so the primary agent always discloses the actual
CLI, model, and effort used. With `agy`, specify effort through a suffixed
model ID or through `--effort` with a base model ID. The default timeout is
120 seconds, with one additional second for `agy` to exit; timeouts never
trigger fallback retries. Codex and Claude Code receive the mission on stdin,
Grok reads a temporary UTF-8 file, and Antigravity receives it as a process
argument in text mode. The target's permissions apply.

## Safety boundaries

- **Never bypass permissions or sandboxes:** do not run with `--yolo`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-skip-permissions`, or `bypassPermissions`.
- **Respect read-only roles:** `architect` never explores, runs commands, edits files, or delegates; `strategist` prepares plans without editing or spawning subagents.
- **No recursive routing:** delegated subagents stay within their mission, do not load the routing skill, and do not delegate further.
- **No concurrent edits on the same files:** assign disjoint file scopes or isolated workspaces (`workspace: "share"` / `"branch"` in Antigravity `swarm`).
- **Conditional independent reviews:** never by default; trigger only for security, data loss, irreversible migrations, public contracts, unresolved contradictions, or critical behavior without reliable tests.

## Repository layout

```text
.
├── README.md, README.fr.md          # Multi-platform overview (EN / FR)
├── CONTRIBUTING.md, CHANGELOG.md    # Maintenance, versioning, and release history
├── AGENTS.md                        # Codex host instructions (synced to templates/)
├── .agents/
│   ├── plugins/marketplace.json     # Codex local marketplace catalog
│   └── skills/quota-orchestrator/   # Local Codex routing skill (FR)
├── .codex/
│   ├── config.toml                  # Codex fallback configuration
│   └── agents/*.toml                # 11 Codex role profiles (9 standard + 2 optional)
├── .claude-plugin/marketplace.json  # Claude Code marketplace catalog
├── .antigravity-plugin/
│   ├── plugin.json, marketplace.json # Native Google Antigravity manifest & catalog
│   └── README.md, README.fr.md      # Antigravity guide (EN / FR)
├── agents/*.md                      # 7 native Antigravity subagents
├── rules/AGENTS.md                  # Always-on Antigravity routing rules
├── skills/quota-orchestrator/       # On-demand Antigravity Gemini routing skill
├── hooks.json, assets/logo.png      # Antigravity PreToolUse hook config & icon
├── scripts/
│   ├── check_delegation.py          # Antigravity PreToolUse delegation guard
│   ├── check_updates.py             # Antigravity SessionStart update checker (2h TTL)
│   └── build_antigravity_bundle.py  # Deterministic .zip packager & sha256 checker
├── plugins/quota-orchestrator/      # Shared Codex & Claude Code plugin package
│   ├── README.md                    # Shared package summary
│   ├── .codex-plugin/plugin.json    # Codex plugin manifest
│   ├── .claude-plugin/plugin.json   # Claude Code plugin manifest
│   ├── codex/README.md, README.fr.md # Full Codex guide (EN / FR)
│   ├── codex-skills/                # Codex plugin skills (routing + setup)
│   ├── hooks/                       # Codex SessionStart reconciliation & PreToolUse guard
│   ├── scripts/install.py           # Bundled Codex installer
│   ├── templates/                   # Synced copies of root AGENTS.md, .codex/, .agents/
│   ├── agents/*.md                  # 5 Claude Code plugin agents
│   └── claude/                      # Claude Code guide, skill, hooks, installer, tests, JSONL cost tool
├── fixtures/release_*/              # Authentic historical release files for migration tests
└── tests/, test_install.py, test_reconcile.py
```

The root layout lets Google Antigravity install directly from the repository URL (`agy plugin install https://github.com/masskrdjn/QuotaOrchestrator`) without a subpath, while keeping Codex and Claude Code cleanly isolated inside `plugins/quota-orchestrator/` with zero component collisions.

## Validation

Python 3.11+ is required. From the repository root:

```sh
python -m unittest discover -s tests -p '*_test.py'
python test_install.py
python test_reconcile.py
agy plugin validate .
python scripts/build_antigravity_bundle.py --check
```

For Claude Code manifest and script validation (`claude plugin validate`, `test_plugin.py`, `test_agent_identity.py`, `test_extract_claude_jsonl.py`), see the [Claude Code validation section](plugins/quota-orchestrator/claude/README.md#update-and-validate-a-release). For Codex native guard integration tests (`CODEX_GUARD_TEST_BINARY`), see the [Codex plugin section](plugins/quota-orchestrator/codex/README.md#install-as-a-plugin).

## License

Licensed under the [MIT License](LICENSE).
