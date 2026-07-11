# Calibration: objects-tabletop-manipulation-6dof-pose-trajectory

Deterministic soft-ADD scorer (`steps/solve/tests/judge.py`, TAU = 0.1 · object
diameter). A task clears the bar when every real agent scores below 0.10 and a real
attempt takes more than 50 tool-call turns. Oracle must be 1.0 and an empty attempt
near 0.

| run | score | rollout (tool-call turns) |
|---|---|---|
| oracle | 1.0 | - |
| empty / null | 0.0 | - |
| random guess | 0.0 | - |
| Claude Code CLI (Opus 4.8) | 0.0 | 80 |
| Codex CLI (GPT-5.5) | 0.0 | 12 |
| Antigravity CLI | 0.0 | 100 (isolated) |
| Cursor CLI (Composer) | 0.0 | 62 |

Every real agent scored 0.0 across all 36 query poses. Claude (80 turns), Cursor
(62 turns), and Antigravity (100 turns) all worked the projection geometry at length,
each well past 50 turns, and none recovered a metric 6DoF pose within the ADD tolerance.
The task has plenty of work available: Codex chose to stop early on its own after
12 turns, landing at the same 0.0.

Integrity note: Antigravity was run in a filesystem-isolated Docker container (network on
for the model, but no repo / no ground-truth / no dataset files reachable), because it is
an aggressive retriever: it will crawl the filesystem and web-search to recognise the
source data. With the materials de-fingerprinted (rectified generic-pinhole video +
minimal intrinsics; no device serial, camera-model name, or parameter signature) and no
GT on the container filesystem, it could not shortcut and produced no valid pose, the
honest 0.0. The other agents were verified GT-clean from their transcripts.

## Anti-shortcut ablations (target ≤ 0.15; simulated best-case degraded submissions)

| ablation | score |
|---|---|
| single_frame (one true pose repeated for all frames) | 0.0833 |
| no_media (fixed pose @ 0.4 m, identity rotation) | 0.0000 |
| frame_dump_no_tools (5 cm translation error, random rotation) | 0.0000 |
| video_only / audio_only | n/a (audio not used) |

Raw transcripts are in `rollouts/` (one file per agent). The agents were given only
`materials/` (clips + camera/query/object JSON), never the ground-truth poses. Agents ran
on the host (general CV libraries importable, used only for geometry, not any answer key);
the real task image ships only numpy + ffmpeg, so the in-image difficulty is at least as
high.

Oracle end-to-end verified by building the task image and running
setup → solve.sh → judge.py in Docker (reward = 1.0).
