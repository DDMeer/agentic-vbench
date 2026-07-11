# Calibration: object-reconstruction-from-egocentric-manipulation

Deterministic occupancy-IoU × surface-F² scorer (`steps/solve/tests/judge.py`), scored
after a scale-free best-fit similarity alignment. A task clears the bar when every real
agent scores below 0.10 and a real attempt takes more than 50 tool-call turns.
Oracle must be ~1.0 and an empty attempt near 0.

| run | score | rollout (tool-call turns) |
|---|---|---|
| oracle (reference meshes) | 1.0 | - |
| empty / null (no meshes) | 0.0 | - |
| wrong object (keyboard mesh) | ≤ 0.002 | - |
| Claude Code CLI (Opus 4.8) | 0.043 | 46 |
| Codex CLI (GPT-5.5) | 0.014 | 11 |
| Antigravity CLI | 0.033 | 64 |
| Cursor CLI (Composer) | 0.019 | 60 |

Every real agent scored below 0.10. Claude (46), Antigravity (64), and Cursor (60) ran
long, reconstructing three full meshes each via frame sampling + multi-view fusion, but
none matched the true surface well enough. The volumetric-occupancy term punishes the
coarse, concavity-poor shells the agents produced, exactly as it punishes a convex hull.
Codex ran only 11 turns because it chose to stop early on its own, not because the task
lacked work to do, and its partial attempt scored 0.014.

## Anti-shortcut ablations (target ≤ 0.15; best-case degraded submission scored)

| ablation | score |
|---|---|
| single_frame (silhouette slab, extruded 2D bbox) | 0.005–0.012 |
| no_media (empty output dir) | 0.0 |
| frame_dump_no_tools (convex hull, best tool-less guess, no concavity) | coffee_pot 0.127, spatula_red 0.017 |
| wrong object (keyboard mesh) | 0.003–0.009 |
| video_only / audio_only | n/a (audio not used) |

The convex-hull and slab shortcuts are exactly what the volumetric-IoU term defeats:
filling a real concavity (hull) or flattening the object (slab) changes the occupied
volume, so both collapse well below the bar while the true shape scores 1.0.

Raw transcripts are in `rollouts/`, one file per agent.

Oracle end-to-end verified by building the task image (materials pulled from Hugging
Face) and running setup → solve.sh → judge.py in Docker (reward = 0.9985–1.0).
