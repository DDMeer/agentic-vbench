---
title: Task Spec Card
summary: The structured header every video-understanding task must fill in and prove.
read_when: Authoring a task. Copy this file into your task folder and fill every field.
---

# Task Spec Card

Copy this file into your task folder as `SPEC.md` and fill in every field. A reviewer
checks the card against the task; the checker (`tools/check_task.py`) verifies the
measurable parts. A task with an incomplete card does not enter review.

The card exists because "a good task" is easy to claim and hard to check. Each field
forces one concrete claim that can be verified.

```yaml
task: <family>/<task-id>

# 1. What kind of thinking does this task need?
#    perception = find/count/time events. understanding = compare, order, relate.
#    reasoning = cause, prediction, cross-event inference. Prefer understanding or
#    reasoning; pure perception must be very hard to justify itself.
cognitive_level: perception | understanding | reasoning

# 2. Which modalities are REQUIRED (not just present)? One line each on why the
#    answer cannot be produced without it.
modalities_required:
  video: <why video is necessary>
  audio: <why audio is necessary, or "not used">

# 3. The exact question the agent is asked (one task, no ambiguity), and the exact
#    output schema it fills in.
question: <one sentence>
output_schema: <the JSON shape, with units and tolerances>

# 4. Evidence chain: the specific moments (and modalities) the answer depends on.
#    A good task needs at least two far-apart moments; a single lookup is too easy.
evidence:
  - <t=..s, modality, what it contributes>
  - <t=..s, modality, what it contributes>

# 5. Ground truth: value, source, tier, and how it was verified.
#    machine-truth  = official structured record (league play-by-play, game logs)
#    logged         = the system's own recorded signals (robot proprioception, FK)
#    human-verified = perceptual judgment; requires 2+ independent annotators and
#                     ALL occurrence windows annotated
ground_truth:
  source: <where the answer key comes from>
  tier: machine-truth | logged | human-verified
  verification: <the cross-check you ran, e.g. "PBP-derived 3PM equals box-score 3PM
                 for all 10 shooters" or "FK ee-height curve matches gripper events">

# 6. Scorer: deterministic code only. State the metric and the anchors.
scorer:
  metric: <e.g. F1 over events; a TP requires X, Y, Z within tolerance T>
  oracle_reward: 1.0
  null_reward: <measured, must be <= 0.10>

# 7. Difficulty: measured with a real strong-agent run.
difficulty:
  strong_agent_reward: <measured, must be < 0.10>
  tool_call_turns: <measured, must be > 50>
  agent_model: <which model/harness>

# 8. Anti-shortcut ablations: run a strong model under each degraded input.
#    Every one must score near the null baseline (<= 0.15). If any scores well,
#    the task has a shortcut - fix the task, not the threshold.
anti_shortcut:
  single_frame: <reward with one representative frame only>
  video_only: <reward with video, audio stripped>   # for audio-visual tasks
  audio_only: <reward with audio only>              # for audio-visual tasks
  no_media: <reward with prompt+schema only - catches recall and guessable schemas>
  frame_dump_no_tools: <reward with all frames pasted, no tool use - catches tasks
                        where agency does not actually matter>

# 9. Input media.
input:
  url: <archive.org / YouTube / HF url>
  sha256: <digest of the baked file>
  length_min: <minutes; 10-300 for single-video tasks, exempt for comparison pairs>
  resolution: <height; >= 720>
```

## Prompt-writing rules (the agent-facing instruction)

- One task per task. No compound asks.
- Define every term the scorer depends on (what counts as a "made three", a "grasp",
  a "bug occurrence"), and give any closed vocabulary in full.
- Give the exact output schema, with units and the tolerance the scorer uses.
- Name the deliverable path explicitly.
- Never describe the scoring method, weights, or the ground-truth source.
- No trick wording, no hidden requirements: everything scored is stated.
