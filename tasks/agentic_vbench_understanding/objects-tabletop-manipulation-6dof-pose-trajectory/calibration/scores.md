# Calibration: objects-tabletop-manipulation-6dof-pose-trajectory

Deterministic soft-ADD scorer (`steps/solve/tests/judge.py`, TAU = 0.1 x object
diameter). A task clears the bar when a strong agent scores below 0.10 while a genuine
attempt is long-horizon, the oracle scores 1.0, and an empty attempt is near 0.

| run | score |
|---|---|
| oracle | 1.0 |
| empty / null | 0.0 |
| random guess | 0.0 |

Oracle verified end to end by building the task image (materials pulled from Hugging
Face) and running setup, solve.sh, then judge.py in Docker: reward 1.0. The agent phase
was checked to contain no ground truth anywhere on the image; the poses ship verifier
side only (tests/ for the grader, a solution/ copy for the oracle).

## The task is solvable, and the ADD bar is reachable

The earlier revision defined the pose in the object's canonical frame without giving the
agent that frame, which made it unsolvable and pinned every agent at exactly 0.0. This
revision ships `object_points.json` (the canonical point set the pose maps from), so a
correct pose is now well defined. To show the bar is reachable, here is what a pose
recovered to a given accuracy scores, obtained by perturbing the oracle poses and grading:

| translation error | rotation error | reward |
|---|---|---|
| 5 mm | 2 deg | 0.71 |
| 10 mm | 5 deg | 0.43 |
| 20 mm | 8 deg | 0.13 |
| 30 mm | 12 deg | 0.03 |

Reward rises smoothly as the pose gets closer, so a good model-based pose estimate is
rewarded well before it is perfect. The difficulty is estimating a metric 6DoF pose from
a single moving view; a wrong rotation or wrong metric depth both fail.

## Anti-shortcut ablations (target <= 0.15; real Claude Code runs on degraded input)

Each row is a real agent run on the degraded input, graded by the same judge; transcripts
are in `calibration/ablations/`.

| ablation | score | turns |
|---|---|---|
| single_frame (one still frame per clip + intrinsics + object_points) | 0.0 | 50 |
| no_media (only cameras.json, queries.json, object_points.json) | 0.0 | 4 |
| video_only / audio_only | n/a (audio not used) | - |

Turn counts are the `num_turns` field of the closing result record in each transcript.
single_frame is the strongest test here: the agent had the object points and one frame
per clip, spent 50 turns trying to fit a pose, and still scored 0.0, because a single
view does not fix metric depth. These runs are on the host where general CV libraries are
available; the shipped image has only numpy and ffmpeg, so in-image scores can only be
lower.
