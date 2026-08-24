# Rollouts

- `claude-code-fable.jsonl` — Claude Code CLI (Fable 5), fresh complete run on the fixed
  task (object_points shipped), executed inside the built task image; ends with the CLI's
  closing result record (num_turns 226). This is the run behind the current-design row in
  `../scores.md`.
- `codex.txt` — Codex CLI (GPT-5.5) run on the earlier revision, before object_points
  shipped; kept as evidence for the unsolvable-by-design diagnosis.
- `cursor.jsonl` — Cursor CLI (Composer) run on the same earlier revision.
- `antigravity.txt` — Antigravity CLI (Gemini 3.5 Flash) run on the same earlier
  revision, executed in a filesystem-isolated Docker container that mounts only
  `materials/`; it produced no solution.json.

Base64 frames pasted by the agent are elided; host paths and dataset references are
redacted. All tool calls, reasoning, and the final answer are intact. Ablation runs are
under `../ablations/`.
