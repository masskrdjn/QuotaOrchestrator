---
name: external-delegation
description: Orchestrate and delegate missions across installed Codex, Claude Code, Grok Build, and Antigravity CLIs with capability matching, reasoning effort selection, bounded read/write modes, and ordered fallbacks.
---

# Multi-CLI External Delegation & Model Routing

Use only when the user authorizes external CLI delegation and sending the mission context to the target provider. Apply the project's delegation rules and retain primary responsibility for verifying the response and integrating changes.

## 1. Invocation & Helper Options

Resolve `../../scripts/delegate_external.py` relative to this skill directory in the installed plugin. From the mission's working directory, run:

```text
python "<absolute script path>" <codex|claude|grok|agy> "<UTF-8 mission file>" [options]
```

Supported options:
- `--model <MODEL>` and `--effort <EFFORT>`: target model ID and reasoning effort. For Antigravity (`agy`), pass either `--model gemini-4-neon --effort high` or a suffixed ID (`--model gemini-4-neon-high`, `--model claude-opus-5-5-high`).
- `--mode <read|write>` (default `read`):
  - `read`: read-only / plan mode (`codex --sandbox read-only`, `claude` and `grok --permission-mode plan`, `agy --mode plan --sandbox`). Use for architecture, framing (`strategist`), research, large-context audits, and independent reviews.
  - `write`: bounded workspace edits (`codex --sandbox workspace-write`, `claude` and `grok --permission-mode acceptEdits`, `agy --mode accept-edits --sandbox`). Never uses `--yolo`, `--dangerously-skip-permissions`, or `bypassPermissions`. Assign disjoint file scopes or an isolated git worktree so two agents never edit the same files concurrently.
- `--fallback <PROVIDER[:MODEL[:EFFORT]]>` (repeatable): ordered fallback chain tried automatically when a target CLI or model is `unavailable` or `failed` (missing binary, account tier restriction, quota exhaustion). Never triggers after a `timeout`.
- `--check-models`: before invoking `agy` or `grok`, queries `agy models` or `grok models` to confirm the target model is exposed by the active subscription (for example, checking whether a paid `agy` account exposes `claude-opus-5-5-high` or `gemini-4-argon-high` before running, and jumping immediately to the next `--fallback` if absent).
- `--list-models`: prints the JSON list of models exposed by `agy` or `grok` for the current account and exits.
- `--timeout <SECONDS>` (default `120`).

Remove any temporary mission file you created after the call.

## 2. Warm Cache vs. Multi-Turn Tool Loops

1. **Preserve the host's warm cache for small work**: micro-tasks (1–2 tool calls), local checks, and follow-ups that depend on the current conversation's hot prompt cache must stay in the host CLI (root or native intra-CLI subagents).
2. **Amortize external cold start over an autonomous internal tool loop**: each external CLI invocation starts with a **cold cache** on Turn 1 at the target provider, then reuses its **own warm cache** across its internal multi-turn tool loop (Turns 2..N: reading files, searching, editing in `write` mode, running targeted tests). Therefore:
   - Delegate **self-contained end-to-end missions** (a complete `builder` lot, a full `writer` draft, a bounded `architect` envelope, or a full-repo audit) in a **single invocation**.
   - Avoid multi-process ping-pong (calling an external CLI repeatedly in ephemeral mode for tiny incremental steps).

## 3. Multi-CLI Model Capabilities, Efforts & Context Cliffs

| CLI | Model (`--model`) | Efforts (`--effort`) | API Rate In / Out ($/MTok) | Context Cliff | Core Strengths & Constraints |
|---|---|---|---|---|---|
| `codex` | `gpt-6-luna` | `high` *(floor)*, `xhigh`, `max` | $0.10 / $0.50 *(cache $0.01)* | > 272k (×2 in / ×1.5 out) | Lowest cost/token (20× cheaper than Sol). `high` for exploration/checks; `max` for fully specified implementation. |
| `codex` | `gpt-6.1-terra` | `low`, `medium`, `high`, `xhigh`, `max` | $1.00 / $5.00 *(cache $0.05)* | > 272k (×2 in / ×1.5 out) | Visual/UI workflows (`visual_operator`) and clear technical writing (`writer`). Half the cost of Sol. |
| `codex` | `gpt-6.2-sol` | `low`, `medium`, `high`, `xhigh`, `max` | $2.00 / $10.00 *(cache $0.10)* | > 272k (×2 in / ×1.5 out) | Multi-step debugging, logical decomposition (`strategist` at `medium`), and complex implementation (`builder` at `high`). |
| `codex` | `gpt-6.2-astra` | `low`, `medium`, `high`, `xhigh`, `max` | $8.00 / $40.00 *(cache $0.40)* | > 272k (×2 in / ×1.5 out) | Deep abstract reasoning (`architect` at `low`/`medium`). Scarce quota; keep in `read` mode (`architect`) to avoid autonomous *Hiding Failures*. |
| `claude` | `claude-haiku-5-5` | `low`, `medium`, `high` | $0.10 / $0.50 *(≤ 100k)* | **> 100k** (×5: $0.50 / $2.50) | Fast validation suites (`runner` at `medium`). Keep below 100k input tokens. |
| `claude` | `sonnet` (`claude-sonnet-5-5`) | `low`, `medium`, `high`, `xhigh` | $2.00 / $10.00 *(cache $0.10)* | 1M max | Reliable fact extraction (`scout`/`researcher` at `medium`) and multi-file coding (`builder` at `high`). |
| `claude` | `opus` (`claude-opus-5-5`) | `medium`, `high`, `xhigh` | $4.00 / $20.00 *(cache $0.20)* | 1M max | Top *PR-ready* patch quality, cross-cutting refactors, and critical security/code reviews (`high`/`xhigh`). |
| `claude` | `claude-fable-5-2` (`fable`) | `xhigh` | $8.00 / $40.00 *(cache $0.20)* | 1M max (128k out) | Frontier algorithmic/scientific reasoning (~174 ECI). Requires 30-day retention (**unavailable under ZDR**) and explicit extra-credit consent. |
| `agy` | `gemini-3.8-flash` | `low`, `medium`, `high` | ~$0.75 / $3.75 | Shared 5h pool | Fast triage and mechanical checks. |
| `agy` | `gemini-4-hydrogen` | `low`, `medium`, `high`, `xhigh` | $1.50 / $7.50 *(cache ~$0.075)* | Shared 5h pool | Fast exploration, structured research, well-specified code, and high-speed counter-analysis. |
| `agy` | `gemini-4-neon` | `low`, `medium`, `high`, `xhigh` | $3.00 / $15.00 *(cache ~$0.15)* | **1M+ stable** | Full-repository ingestion (> 250k–1M tokens) and multi-language CLI engineering without 200k/272k price cliffs. |
| `agy` | `gemini-4-argon` | `low`, `medium`, `high` | Frontier tier | **Dedicated weekly pool** | Long-horizon synthesis and rare architectural arbitration (`architect`). |
| `agy` *(paid bridge)* | `claude-sonnet-5-5-{low,medium,high}`<br>`claude-opus-5-5-{low,medium,high}` | Suffixed (`low`, `medium`, `high`) | Paid Antigravity subscription | Account-dependent | Hosted Claude models inside `agy`. Always pass `--check-models` so free/unsupported `agy` accounts fall back cleanly. |
| `grok` | `grok-4.7` *(default)*<br>`grok-build-0.1` *(API)* | `low`, `medium`, `high`, `xhigh` | $2.00 / $6.00 *(4.7 < 200k)*<br>$1.00 / $2.00 *(build-0.1)* | **≥ 200k** (×2: $4.00 / $12.00) | High output speed (tokens/s) and low output cost below 200k. **Free tier limitation**: on a free `grok` account, high reasoning efforts and large prompts fail or exhaust quota immediately — treat as `free_restricted` and route to fallbacks by default. |

## 4. Cross-CLI Routing & Fallback Matrix

When a primary model is unavailable (no Fable access on Claude, free-tier Grok account, exhausted weekly Argon/Astra quota, or missing CLI), apply **effort compensation** on the fallback tier: raise effort (`high` → `xhigh` or `max`) and tighten the mission envelope (≤ 80 lines for `architect`) or freeze the contract (`builder`).

| Mission Type | Mode | Primary Target | Fallback 1 *(No Fable / Free Grok safe)* | Fallback 2 *(Cross-pool / Paid `agy` bridge)* | Fallback 3 *(Intra-CLI / Lower tier + max effort)* |
|---|---|---|---|---|---|
| **Frontier arbitration / Deadlock (`architect` max)** | `read` | `claude:claude-fable-5-2:xhigh` *(non-ZDR, confirmed access)* | `codex:gpt-6.2-astra:medium` *or* `agy:gemini-4-argon-high` | `claude:opus:xhigh` *or* `agy:claude-opus-5-5-high` *(with `--check-models`)* | `codex:gpt-6.2-sol:max` *or* `agy:gemini-4-neon-xhigh` |
| **Standard architectural second opinion (`architect`)** | `read` | Cross-family: `codex:gpt-6.2-astra:low` ↔ `agy:gemini-4-argon-medium` | `claude:opus:xhigh` | `agy:claude-opus-5-5-high` *(with `--check-models`)* | `codex:gpt-6.2-sol:xhigh` *or* `agy:gemini-4-neon-xhigh` |
| **Critical code/security review & anti-*Hiding Failures*** | `read` | `claude:opus:high` | `agy:claude-opus-5-5-high` *(with `--check-models`)* *or* `claude:sonnet:xhigh` | `agy:gemini-4-neon-high` | `codex:gpt-6.2-sol:xhigh` |
| **Logical framing & decomposition (`strategist`)** | `read` | `codex:gpt-6.2-sol:medium` *(or `high`)* | `agy:gemini-4-neon-medium` *(preferred if > 250k tokens)* | `claude:sonnet:high` | `codex:gpt-6-luna:max` |
| **Fast counter-opinion / Red-team (< 200k tokens)** | `read` | `grok:grok-4.7:medium` *(paid/API Grok only)* | `agy:gemini-4-hydrogen-high` | `codex:gpt-6-luna:xhigh` | `claude:sonnet:medium` |
| **Massive context audit (> 250k–1M tokens)** | `read` | `agy:gemini-4-neon-high` | `agy:gemini-4-hydrogen-high` | `claude:sonnet:medium` | Host `scout` in < 60 KB chunks |
| **Complex cross-CLI implementation (`builder`)** | `write` | `claude:sonnet:high` *or* `codex:gpt-6.2-sol:high` | `agy:claude-sonnet-5-5-high` *(with `--check-models`)* *or* `agy:gemini-4-neon-high` | `codex:gpt-6-luna:max` *or* `agy:gemini-4-hydrogen-xhigh` *(on frozen contract)* | Host native `builder` |
| **Clear documentation (`writer`) & UI analysis** | `read` / `write` | `codex:gpt-6.1-terra:medium` *(or `high`)* | `claude:sonnet:medium` *(writing)* / `agy:gemini-4-hydrogen-medium` *(UI)* | `codex:gpt-6-luna:high` | Host root |

Example command with ordered fallbacks and model availability check:

```text
python "<absolute script path>" claude mission.txt --mode read --model opus --effort high --check-models --fallback agy:claude-opus-5-5-high --fallback codex:gpt-6.2-sol:xhigh
```

## 5. Response Verification & Mandatory Traceability

Read the JSON output from `delegate_external.py`:
- Use `response` only when `status` is `ok`.
- If `fallback_used` is `true`, inspect `requested`, `attempts`, and the winning `provider`, `model`, and `effort`. **Always report the actual executed CLI/model/effort to the user** — never present a fallback response as coming from the initially requested model (such as Fable, Astra, Argon, or Grok).
- If all candidates fail or time out, report the failure and `attempts` diagnostics without silently inventing a result.
