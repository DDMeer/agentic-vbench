# Calibration trajectories (in-repo audit record)

One secret-free trajectory per strong-agent row in `../scores.md`. Each keeps the agent's own
commentary and the shell commands it ran; tool outputs, encrypted reasoning, and all
environment/credential context were dropped at extraction and re-scanned for keys (0 hits).

- `codex_trajectory.md` — Codex CLI `gpt-5.6-sol` (xhigh), 247 tool calls.
- `claude_trajectory.md` — Claude Code CLI `claude-opus-4-8`, 94 tool calls.

(Turn counts here and in `scores.md` are the raw session tool-call totals; the committed trajectory
collapses consecutive identical calls, so its visible `→ run` count is a few lower.)

**Rollout dumps (solution.json + reward.json) are on HF**, pinned to an immutable revision (not a
mutable `main` link), whole-file SHA256 recorded:

```
REV=39f1b933102acb3e52348752eb736b31c4c9d50b
base=https://huggingface.co/datasets/explcre/agenticvbench-understanding-materials/resolve/$REV/minecraft-gameplay-ledger-s1/calibration
```
- `$base/codex_solution.json`, `$base/codex_reward.json`
- `$base/claude_solution.json`, `$base/claude_reward.json`
- trajectory copies also on HF; SHA256:
  - `codex_trajectory.md`  `b5c2050ff81e5f563a55ae79f31e38be595bdee84dbc5f110a525e4830e39f24`
  - `claude_trajectory.md` `cdd76a983cdf341d8d73c096f7b231a8e5231e1a7ce3f6ce92f9e49409d2ffcf`
