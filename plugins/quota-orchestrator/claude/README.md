# Selective Multi-Model Routing for Claude Code

[Français](README.fr.md) · [Repository and Codex guide](../../../README.md)

A Claude Code configuration, installable as a plugin or per project, that
hands work to specialized roles only when delegation preserves quality while reducing total cost or latency. The
primary agent stays responsible for decisions, integration, and user
communication.

## Routing policy

Priorities, in order:

1. Preserve result quality and relevance.
2. Reduce total cost, including coordination and rework.
3. Reduce latency.

A lower total cost paid with more tokens on a cheaper tier is a good trade.
Degraded quality or multiplied latency is not.

Small, bounded tasks stay with the primary agent. Delegation is used when a
clearly scoped role can perform substantial work more efficiently or provide
useful independent analysis.

| Role | Model | Effort | $/1M in | $/1M out | Responsibility |
| --- | --- | --- | --- | --- | --- |
| Primary | `opus` | `xhigh` | 4 | 20 | Triage, decisions, integration, small local tasks |
| `scout` | `sonnet` | `medium` | 2 | 10 | Read-only codebase and log exploration |
| `researcher` | `sonnet` | `medium` | 2 | 10 | Multi-source external research |
| `runner` | `claude-haiku-5-5` | `medium` | 0.10 / 0.50 | 0.50 / 2.50 | Long validations and large mechanical batches |
| `builder` | `sonnet` | `high` | 2 | 10 | Scoped implementation with targeted validation |
| `architect` | `opus`, or `fable` on confirmed access | `xhigh` | 4 → 10 | 20 → 50 | Rare, bounded architecture decisions only |

`opus` means Opus 5.5 on the Anthropic API and subscriptions, which requires
Claude Code 2.1.280 or newer; an older CLI or another provider serves a
different model. `sonnet` means Sonnet 5.5 on the Anthropic API from Claude
Code 2.1.284; per the documentation it resolves to an older Sonnet on Bedrock,
Vertex, Foundry and Claude Platform on AWS. Sonnet 5.5's effort levels are
recalibrated relative to Sonnet 5, so the settings were re-chosen from the
official guidance rather than carried over.

`runner` uses the fixed Haiku 5.5 model ID. Its prices above apply to prompts
up to / over 100,000 tokens, respectively. The threshold includes uncached
input, cache writes, and cache reads for each request; output tokens do not
count toward it. Both input and output use the selected rate for that request.
See the [Haiku 5.5 announcement](https://www.anthropic.com/claude-haiku-5-5)
and [pricing](https://platform.claude.com/docs/en/about-claude/pricing).

Three choices deserve a justification:

- **`runner` on the cheapest tier.** The role executes and reports; it does not
  design. Its bounds — three fix/test cycles, stop on a repeated signal, two
  attempts on an environment problem — are exactly what makes this tier safe
  here. Haiku 5.5 supports `effort`; `medium` is the recommended starting point
  for agentic work. `low` can stop early or skip checks on long prompts, so the
  role explicitly requires executing checks before reporting success. See the
  [Haiku 5.5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5#use-effort-to-control-thinking).
- **`scout` and `researcher` do not go down there.** Both produce facts the
  primary agent will believe without re-checking. Too low a tier yields
  confident, wrong claims whose rework costs more than the saving. Their effort
  stays `medium`: their work is bounded by input and output rather than by
  reasoning, and lower effort consolidates tool calls — cheaper and faster at
  equal quality.
- **`builder` raises effort rather than tier, but stops at `high`.** Effort is
  the first quality lever within a model; `sonnet`/`high` costs half as much as
  the tier above for input, output, and cache reads. `xhigh` is
  not the default: the documentation reserves it for long-horizon work with very
  large token budgets and for cases where evals show a gain, and `builder`'s
  bounded tasks (three attempts) are neither. Move it to `xhigh` only on
  measurement, from complete runs.

Two escalations exist, decided explicitly and passed at invocation without
editing any role file: `builder` to `opus` for a hard task, and `architect` to
`fable` on confirmed access, as a second call when the Opus 5.5 opinion leaves
a decisive contradiction. An environment problem never raises a tier.

## Claude Fable 5.2 access

Fable 5.2 was released on November 9, 2026. Its standard API rates per million
tokens are $8 input, $40 output, $10 for a 5-minute cache write, $16 for a
1-hour cache write, and $0.20 for a cache read. Input, output, and cache writes
cost twice the Opus 5.5 rates; cache reads cost the same. Fable 5.1 keeps its
historical $10/$50 input/output rates.

On first-party Claude Code, the `fable` alias selects Fable 5.2 with CLI
version 2.1.321 or newer; its model ID is `claude-fable-5-2`. Pinned model
settings, organization restrictions, and third-party provider mappings can
still resolve to Fable 5.1 or make Fable unavailable. Check `resolvedModel`;
an alias or CLI version alone does not prove which model ran.

Fable 5.2 supports a 1M-token context and up to 128K output tokens. It requires
30-day data retention and is unavailable under zero data retention (ZDR) unless
Anthropic expressly authorizes it. If the organization requires ZDR without
that authorization, treat Fable 5.2 as unavailable.

Fast mode is optional and doubles Fable 5.2 input/output rates to $16/$80 per
million tokens. It requires separate explicit authorization. The transcript
exporter applies standard rates and does not read the service tier, so its
estimate does not price Fast mode correctly; use the bill for actual cost.

Access is **presumed unavailable**. Check:

```bash
claude auth status --json
claude --version
```

The full decision table lives in the skill. Third-party providers require their
own Fable model ID or mapping; do not assume the `fable` alias is portable.
Team and Enterprise settings may restrict the model or keep Fable 5.1 pinned.

Available still does not mean authorized. On a subscription, Fable may bill to
*usage credits* — money on top of the subscription. Before the first
consultation, the primary agent asks once, naming the effective model and its
standard rates; Fast mode needs separate consent. It records the answer in
`.claude/settings.local.json` — gitignored, so it stays per-machine.
Non-interactive runs (`-p`) and SDK calls can bill without asking, so never
escalate there without prior explicit authorization.

Without access, or on refusal, `architect` answers on Opus 5.5 at `xhigh` and
**says explicitly that this is not a Fable opinion**. Afterwards the effective
model is checked through runtime metadata when available (for example
`resolvedModel`). Missing metadata does not discard the work or repeat its
validation; it only prevents claiming an attested Fable consultation.

Sources consulted November 9, 2026: [Fable 5.2 model overview](https://platform.claude.com/docs/en/models/fable-5-2/overview),
[Fable 5.2 migration guide](https://platform.claude.com/docs/en/models/fable-5-2/whats-new-fable-5-2),
and [Claude Code model configuration](https://code.claude.com/docs/en/model-config).
## Observed execution identity

The `.claude/hooks/agent_identity.py` hook adds a report to the parent's context
with `resolvedModel`, its provenance, and observed effort when available. It
reads native metadata and the transcript of the specific child. It never turns
a requested alias or profile setting into an effective model, and does not
modify Claude Code's native response. Unknown fields remain `null`.
Launch resolution and observed execution remain distinct; model differences,
model changes, and incomplete evidence are reported.

The hook ships with both plugin and classic installation. Python 3 must be
available as `python` to the Claude Code process. Restart the session after an
update and check that the hook is enabled: without its report, identity is not
attested. Metadata failures require a targeted check, never a full rerun of the
child's work. Internal transcript formats may change; tests cover the observed
format, not future CLI guarantees. Transport: [Anthropic hooks](https://code.claude.com/docs/en/hooks).

Validation without model calls: `python plugins/quota-orchestrator/claude/test_agent_identity.py`.

## Project layout

- `CLAUDE.md`, `.claude/agents/`, and
  `.claude/skills/quota-orchestrator/SKILL.md` define the routing rules, roles,
  and decision workflow.
- `.claude/settings.json` sets shared defaults; `.claude/hooks/agent_identity.py`
  reports model metadata observed for each child agent.
- The [Claude Code marketplace](../../../.claude-plugin/marketplace.json) selects the shared package. Its [manifest](../.claude-plugin/plugin.json) loads the skill and hooks. Claude Code discovers the roles in `../agents/`.
- `extract_claude_jsonl.ps1` calculates token use, duration, and dollar cost from
  session transcripts.

## Usage

### Inheritance and precedence

Claude Code builds its instruction chain from lowest to highest precedence:
organization-managed instructions, then `~/.claude/CLAUDE.md`, then the
repository root `CLAUDE.md`, then `CLAUDE.local.md`. A subdirectory's
`CLAUDE.md` loads on demand, when Claude works in it. The `@path` syntax imports
another file; relative paths resolve from the importing file, not the current
directory.

If your project already has a `CLAUDE.md`, **do not replace it**: keep its
contents and add the routing rules to it. To scope instructions to a
subdirectory, place another `CLAUDE.md` there.

For settings, `~/.claude/settings.json` provides your personal values. The
project's `.claude/settings.json` sits above it, `.claude/settings.local.json`
above that, and organization-managed settings take precedence over everything.

### Install as a plugin

The repository is also a Claude Code plugin marketplace. The plugin ships the
five roles, the `quota-orchestrator` skill, and a `SessionStart` hook that
loads `CLAUDE.md` into the primary agent's context at startup, resume, `/clear`,
and compaction. Subagents do not receive it, consistent with the rule that they
do not route.

From the CLI:

```bash
claude plugin marketplace add ./
```

```bash
claude plugin install quota-orchestrator@quota-orchestrator
```

From a local checkout, `claude plugin marketplace add ./` replaces the first
command, and `claude --plugin-dir ./plugins/quota-orchestrator` loads the plugin for a single session
without installing it. In the desktop app (Code tab), click **+** next to the
prompt box, then **Add plugins**. If the menu shows **Plugins**, choose
**Browse plugins**. Find `quota-orchestrator` in the local marketplace; a
user-scope install from the CLI is also available in the app's local sessions.
Start a new session, or run `/reload-plugins`, afterwards.

Things to know:

- Plugin components are namespaced: the roles appear as `quota-orchestrator:scout`
  and so on, the skill as `quota-orchestrator:quota-orchestrator`. A project or user
  agent with the same short name takes precedence over the plugin's.
- The hook runs `cat`, so it needs a POSIX shell: Git Bash on Windows.
- The plugin does not load `.claude/settings.json`. Choose `opus` and `xhigh` with `/model` and
  `/effort`, or copy `effortLevel`, `modelSettings`, and `permissions.deny` from
  this repository's `.claude/settings.json` into `~/.claude/settings.json`.
- Do not combine the plugin with `install.py` in the same project: the rules
  would load twice and the project's roles would shadow the plugin's.
- Both host manifests share the same version (**0.10.1**). The marketplace does not duplicate it.
- `.claude/settings.json` contains shared configuration and is intentionally
  tracked by Git. Keep personal settings and secrets in the ignored
  `.claude/settings.local.json`.

To migrate from the old ClaudeSkills install, check its scope with
`claude plugin list`, uninstall `claudeskills@claudeskills`, and remove its
marketplace. Add this project's marketplace and install
`quota-orchestrator@quota-orchestrator` with the same scope (`--scope user`,
`project`, or `local`). Claude component prefixes now use `quota-orchestrator:`.

The behavior described here applies to Claude Code, including local desktop
sessions. Claude.ai chat does not provide the same environment for hooks and
subagents.

### Update and validate a release

After publishing the marketplace:

```bash
claude plugin marketplace update quota-orchestrator
claude plugin update quota-orchestrator@quota-orchestrator
```

Start a new session or use `/reload-plugins`. Python 3.11+ must be accessible as
`python`, including from Claude Code, for the identity hook.

Before committing, validate both manifests separately (the CLI recognizes the
repository root as a marketplace) and run the tests without model calls:

```bash
claude plugin validate plugins/quota-orchestrator/.claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json --strict
python plugins/quota-orchestrator/claude/test_plugin.py
python plugins/quota-orchestrator/claude/test_agent_identity.py
python plugins/quota-orchestrator/claude/test_extract_claude_jsonl.py
python plugins/quota-orchestrator/claude/test_install.py
python plugins/quota-orchestrator/claude/smoketest.py
```

`smoketest.py` requires Windows PowerShell 5.1. Tests that call models remain
separate in `smoketest_live.py` and consume budget.

### Install into a project

1. Requires Python 3.11 or newer. From this repository, run:

   ```text
   python plugins/quota-orchestrator/claude/install.py path/to/your/project
   ```

   Use `--dry-run` to preview every change. The installer appends the routing
   rules to an existing `CLAUDE.md` between `claudeskills:routing` markers,
   adds missing `.claude/settings.json` keys and the identity hook while keeping
   existing hooks, backs up modified files
   under `.claudeskills-backup/`, and warns instead of overwriting divergent
   role, skill, or hook files.
2. Review the warnings, then the models, efforts, and permission rules for your
   environment, then run `/agents` to confirm all five roles are seen with the
   right model and effort.
3. Start a new session from the repository so the instruction chain is rebuilt.
4. Ask Claude to summarize its active instructions if you want to verify
   discovery.

Claude Code discovers repository instructions from `CLAUDE.md`, skills from
`.claude/skills`, roles from `.claude/agents`, and settings from
`.claude/settings.json`. See the official documentation for
[CLAUDE.md](https://code.claude.com/docs/en/memory),
[skills](https://code.claude.com/docs/en/skills),
[subagents](https://code.claude.com/docs/en/sub-agents),
[models](https://code.claude.com/docs/en/model-config), and
[settings](https://code.claude.com/docs/en/settings).

## Measurement

Without measurement, a gain is expected, not demonstrated.
`extract_claude_jsonl.ps1` reads session JSONL transcripts and aggregates
tokens, durations, and **dollar cost** by model, by effort, and by role.

```powershell
.\plugins\quota-orchestrator\claude\extract_claude_jsonl.ps1
```

The report carries a `Complete` field. It is `true` only when no diagnostic was
raised. An incomplete report has exactly the status *not observable*: its
tokens, costs, and durations must never appear in a ratio, a median, a
comparison, or an economic recommendation. Compare at least two complete
reports, otherwise conclude that no comparison is possible.

The script reads two levels: the session transcript for the primary agent, and
`<session>/subagents/agent-*.jsonl` for each delegated role. That second source
is essential — the call result that spawned a subagent carries only its **final
turn**, not its total. Relying on it under-counts massively. A background
subagent is measured like any other; what makes a run unobservable is a missing
transcript, a model absent from the price table, or a cache write whose
time-to-live is unknown.

A second trap, also handled: one message appears once per content block and its
`usage` is **cumulative**. The script keeps the maximum per message id; keeping
the first would lose most of the output tokens.

A cache write is priced by its time-to-live: 1.25× input for a 5-minute cache,
**2× for a one-hour cache**. Claude Code uses both within a single session —
typically one hour for the primary agent and five minutes for a subagent.
Conflating them under-counts the bill by a third, so the script reads the
per-TTL breakdown and refuses to price a write whose TTL is unknown.

Prices live in a single table at the top of the script; that is the only place
to update when they change. `python plugins/quota-orchestrator/claude/test_extract_claude_jsonl.py` checks the
script's contract against synthetic transcripts, with no model calls.

Fable 5.2 uses the standard API rates in that table. The transcript exporter
does not read the service tier, so it cannot price Fast mode's 2x input/output
rates; use billing data for actual Fast-mode cost.

Haiku 5.5 costs are calculated per deduplicated request before aggregation,
so a role can mix prompts on either side of the 100,000-token threshold.
Haiku 4.5 prices remain available for historical transcripts. Sonnet 5.5 cache
reads now cost $0.10 per million tokens, following the October 7, 2026 update.

## Safety boundaries

- Never run with `--dangerously-skip-permissions` or in `bypassPermissions` mode.
- Do not widen session permissions to consult `architect`; if its restrictions
  no longer hold, isolate the decision in another session.
- `architect` does not explore, execute commands, edit files, or delegate.
- Roles stay within their scope and do not perform routing themselves: `Agent`
  is absent from every role's tool list, which effectively prevents delegation.

## Customization

Edit `.claude/settings.json` for default efforts, and the matching file under
`.claude/agents/` to change a role. Keep models, efforts, and role boundaries
synchronized across `CLAUDE.md`, `.claude/skills/quota-orchestrator/SKILL.md`, and this README.
Keep every role in `../agents/` identical to its copy in `.claude/agents/`;
`python plugins/quota-orchestrator/claude/test_plugin.py` checks the manifests against the repository.

The tiers proposed here are defensible, not measured on your work. The
measurement script exists precisely so you can tune them on your own tasks — and
the doctrine forbids claiming a demonstrated gain until two complete runs show it.

Model availability depends on your account and environment.
