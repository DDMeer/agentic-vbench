# Calibration: hands-bimanual-manipulation-3d-joint-trajectory

Deterministic soft-PCK scorer (`steps/solve/tests/judge.py`, TAU = 3 cm). A task clears
the bar when every real agent scores below 0.10 and a real attempt takes more than
50 tool-call turns. Oracle must be 1.0 and an empty attempt near 0.

| run | score | rollout (tool-call turns) |
|---|---|---|
| oracle | 1.0 | - |
| empty / null | 0.0 | - |
| random guess | 0.0 | - |
| Claude Code CLI (Opus 4.8) | 0.0 | 67 |
| Codex CLI (GPT-5.5) | 0.0 | 13 |
| Antigravity CLI | 0.0 | 45 |
| Cursor CLI (Composer) | 0.0 | 57 |

Every real agent scored 0.0: not a single one of the 720 (clip × frame × joint) units
landed within the 3 cm tolerance. Claude (67), Cursor (57), and Antigravity (45) ran
long on PnP, camera-model, and marker-detection work and still produced no correct metric
3D joint, which is what drives the over-50-turn long-horizon property here. Codex chose to
stop early on its own after fewer turns (13) and reached the same 0.0; the task did not
lack work for it. Monocular metric 3D hand-joint recovery is beyond all of them.

## Anti-shortcut ablations (target ≤ 0.15; simulated best-case degraded submissions)

| ablation | score |
|---|---|
| single_frame (real hand shape, guessed fixed depth) | 0.0000 |
| no_media (fixed canonical hand @ 0.4 m) | 0.0000 |
| frame_dump_no_tools (15% scale error + 2 cm noise) | 0.0039 |
| video_only / audio_only | n/a (audio not used) |

Raw transcripts are in `rollouts/`, one file per agent, so a reviewer can confirm each
score was earned honestly and count the tool-call turns. Honesty notes verifiable in the
transcripts: the agents were given only `materials/` (clips + camera/query JSON), never
the ground truth; the GT-derived hand-model profile is absent, so no agent could shortcut
via forward kinematics. Agents were run on the host, where general CV libraries happened
to be importable (used only for camera projection, not for any answer key). The real
task image ships only numpy + ffmpeg, so the in-image difficulty is at least as high.

Oracle end-to-end verified by building the task image and running
setup → solve.sh → judge.py in Docker (reward = 1.0).
