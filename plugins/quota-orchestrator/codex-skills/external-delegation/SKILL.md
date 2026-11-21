---
name: external-delegation
description: Send one mission to an installed Claude Code, Grok Build, or Antigravity CLI when the user explicitly requests external delegation.
---

Use only when the user explicitly authorizes the target CLI and sending the
mission context to its provider. Apply the project's delegation rules and
retain responsibility for checking the response. Use an analysis or planning
mission and include only the context needed for it.

Resolve `../../scripts/delegate_external.py` relative to this skill directory
in the installed plugin. From the mission's working directory, run
`python "<absolute script path>" <claude|grok|agy> "<UTF-8 mission file>"`.
Pass `--model`, `--effort`, or `--timeout` only when needed. The target CLI
must already be installed and authenticated. Remove any temporary mission file
you created after the call.

Read the JSON result. Use `response` only when `status` is `ok`. Report a
failed, unavailable, or timed-out run without silently changing providers.
The helper requests the target's plan mode. The host and the target CLI
enforce their own permissions.
