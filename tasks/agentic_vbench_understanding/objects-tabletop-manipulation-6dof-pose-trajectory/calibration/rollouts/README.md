# Rollouts

`claude-code.jsonl` is a Claude Code (Opus 4.8) run on the current design, where the agent
is given object_points.json and attempts a model-based 6DoF pose per query frame. It ran
long and still scored below the bar. Base64 frames pasted by the agent are elided; host
paths and dataset references are redacted. Ablation runs are under `../ablations/`.
