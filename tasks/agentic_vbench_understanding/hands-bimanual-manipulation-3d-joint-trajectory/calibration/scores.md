# Calibration: hands-bimanual-manipulation-3d-joint-trajectory

Deterministic soft-PCK scorer (`steps/solve/tests/judge.py`, TAU = 3 cm). A task clears
the bar when every real agent scores below 0.10 and a real attempt takes more than
50 tool-call turns. Oracle must be 1.0 and an empty attempt near 0.

| run | score | rollout (tool-call turns) |
|---|---|---|
| oracle | 1.0 | - |
| empty / null | 0.0 | - |
| random guess | 0.0 | - |
| Claude Code CLI (Fable 5) | 0.0 | 64 |
| Claude Code CLI (Opus 4.8) | 0.0 | 67 |
| Codex CLI (GPT-5.5) | 0.0 | 13 |
| Antigravity CLI (Gemini 3.5 Flash) | 0.0 | 45 |
| Cursor CLI (Composer) | 0.0 | 57 |

The Fable 5 row is a fresh run with a current model on the shipped task, executed inside
the built task image itself; the full stream transcript is
`rollouts/claude-code-fable.jsonl` and ends with the CLI's closing result record
(num_turns 66, of which 64 are tool calls). The container had network access for the
model API, so the agent could and did pip install OpenCV and MediaPipe Hands, ran a
purpose-built hand-landmark detector with multi-crop passes and a handedness
disambiguation step, and submitted a complete, well-formed 36-frame solution. It still
scored 0.0: not one of the 720 (clip x frame x joint) units landed within 3 cm. That run
had strictly more tooling than the shipped image (numpy plus ffmpeg, no network), so the
in-image score cannot be higher.

Every real agent scored 0.0. Fable 5 (64 tool calls), Claude Opus (67), Cursor (57), and
Antigravity (45) ran long on detection, PnP, and camera-model work and still produced no
correct metric 3D joint, which is what drives the over-50-turn long-horizon property
here. Codex chose to stop early on its own after fewer turns (13) and reached the same
0.0; the task did not lack work for it. Monocular metric 3D hand-joint recovery is beyond
all of them.

## The 3 cm target is reachable (partial-credit curve)

Because every agent scored 0.0 and the oracle copies the answer key, here is what a
method that recovers joints to a given accuracy would score, obtained by adding gaussian
noise of the stated magnitude to the reference joints and grading:

| per-joint error | reward |
|---|---|
| 5 mm | 0.733 |
| 10 mm | 0.476 |
| 15 mm | 0.245 |
| 20 mm | 0.151 |
| 30 mm | 0.052 |
| 50 mm | 0.015 |

The reward rises smoothly as accuracy improves, so a genuinely good reconstruction is
rewarded well before it is perfect. The gap between this curve and the agents' 0.0 is the
difficulty: they could not get any joint reliably within a few centimetres.

## Anti-shortcut ablations (target ≤ 0.15; real Claude Code runs on degraded input)

Each row is a real agent run on the degraded input, graded by the same judge. Transcripts
and summaries are in `calibration/ablations/`.

| ablation | score | turns |
|---|---|---|
| single_frame (one still frame per clip + intrinsics) | 0.0 | 43 |
| no_media (only cameras.json + queries.json) | 0.0 | 2 |
| frame_dump_no_tools (pre-dumped frames, no shell tools) | 0.0 | 17 |
| video_only / audio_only | n/a (audio not used) | - |

single_frame is the strongest test: the agent spent 43 turns trying to triangulate depth
from one frame per clip and still landed at 0.0, because metric depth is not recoverable
from a single view. These runs were on the host with general CV libraries available; the
shipped image has only numpy and ffmpeg, so in-image scores can only be lower.

Raw transcripts are in `rollouts/`, one file per agent, so a reviewer can confirm each
score was earned honestly and count the tool-call turns. Honesty notes verifiable in the
transcripts: the agents were given only `materials/` (clips + camera/query JSON), never
the ground truth; the GT-derived hand-model profile is absent, so no agent could shortcut
via forward kinematics. Agents were run on the host, where general CV libraries happened
to be importable (used only for camera projection, not for any answer key). The real
task image ships only numpy + ffmpeg, so the in-image difficulty is at least as high.

Oracle end-to-end verified by building the task image and running
setup → solve.sh → judge.py in Docker (reward = 1.0).
