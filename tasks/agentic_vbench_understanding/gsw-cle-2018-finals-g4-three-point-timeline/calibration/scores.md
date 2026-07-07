# Calibration — gsw-cle-2018-finals-g4-three-point-timeline

Deterministic F1 scorer (`steps/solve/tests/judge.py`). A task clears the bar when
**every real agent scores below 0.10** and a real attempt takes **more than 50
tool-call turns**. Oracle must be 1.0 and an empty attempt near 0.

| run | score | rollout (tool-call turns) |
|---|---|---|
| oracle | 1.0 | — |
| empty / null | 0.0 | — |
| 22-entry guess | 0.0 | — |
| Antigravity | _to run_ | _to run_ |
| Codex CLI | _to run_ | _to run_ |
| Claude Code CLI (Opus 4.8) | 0.0465 | 78 |

Raw transcripts are in `rollouts/` — one file per agent, so a reviewer can confirm
each score was earned honestly and count the tool-call turns.

Note: this worked example predates the three-agent requirement and was originally
calibrated with a single headless Claude run (recorded above as the Claude Code CLI
row). New tasks must fill in all three agents.
