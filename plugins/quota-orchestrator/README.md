# QuotaOrchestrator

Selective multi-model routing for Codex and Claude Code. In Claude Code, the
plugin provides five specialized agents (`scout`, `researcher`, `runner`,
`builder`, `architect`), the `quota-orchestrator` skill, routing rules loaded at
session start and an agent-identity hook. Install it from the repository
marketplace; setup, migration and validation are described in
[claude/README.md](claude/README.md) (English) and
[claude/README.fr.md](claude/README.fr.md) (français). Licensed under MIT.

```text
claude plugin marketplace add masskrdjn/QuotaOrchestrator
claude plugin install quota-orchestrator@quota-orchestrator
```
