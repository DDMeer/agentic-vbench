---
title: Task Spec Card
summary: Right-hand 3D joint trajectory from three egocentric manipulation clips.
read_when: Reviewing or reproducing this video-understanding task.
---

# Task Spec Card

```yaml
task: agentic_vbench_understanding/hands-bimanual-manipulation-3d-joint-trajectory

# 1. What kind of thinking does this task need?
cognitive_level: reasoning
# The answer is metric 3D structure, not an on-screen readout. The agent must track
# the right hand across an egocentric clip, reason about camera geometry (the
# camera model is given) and hand motion parallax over many frames, and recover each
# joint's position in metres. It is spatial/geometric reasoning, not perception.

# 2. Which modalities are REQUIRED (not just present)?
modalities_required:
  video: The 3D joint positions exist only in the moving imagery; they must be
    triangulated/inferred from how the hand and scene shift across frames under the
    given camera model. No single frame or caption carries metric depth.
  audio: not used

# 3. The exact question and output schema.
question: For each query frame in each of the three clips, give the right hand's 20
  canonical skeleton joints as 3D points in that clip's RGB camera frame, in metres.
output_schema: >
  {"clips": {"clip_01": [{"frame": int, "joints_m": [[x,y,z] x20]}], "clip_02": [...],
  "clip_03": [...]}}. joints_m is 20 rows in the fixed joint order given in the prompt,
  metres, camera frame (+Z forward, +X right, +Y down). Scored per joint with a 3 cm
  soft tolerance.

# 4. Evidence chain: the answer depends on many far-apart moments.
evidence:
  - "36 query frames total (12 per clip), spread across the middle 90% of each ~2 min
     clip, so the answer is distributed over the whole timeline, not one lookup."
  - "Each query needs the hand localised in 3D at that instant; metric depth for a
     monocular view only resolves by integrating the hand's and scene's motion
     across neighbouring frames plus the supplied camera intrinsics."
  - "Two hands are present and often overlap; the agent must consistently isolate the
     right hand throughout, which requires following the interaction over time."

# 5. Ground truth.
ground_truth:
  source: The capture rig's logged hand-tracking (per-frame hand model + wrist pose),
    forward-kinematicked to 20 canonical joints and transformed into each clip's RGB
    camera frame using the logged device trajectory and factory camera extrinsics.
  tier: logged
  verification: "Reprojected joints land on the visible hand in sampled frames; per-frame
    hand bounding boxes from the rig agree; hand scale (wrist-to-fingertip spans) is
    anatomically consistent (~18-22 cm hand span) across all queries."

# 6. Scorer: deterministic code only.
scorer:
  metric: >
    Per joint, soft hit = clip(1 - ||pred - gt|| / TAU, 0, 1) with TAU = 0.03 m.
    reward = mean soft hit over all (clip, query frame, joint) = 720 scored units.
  oracle_reward: 1.0
  null_reward: 0.0   # measured: empty/None submission

# 7. Difficulty: measured with real strong-agent runs.
difficulty:
  strong_agent_reward: 0.0    # Claude Opus 4.8, Codex GPT-5.5, Cursor Composer: all 0.0
  tool_call_turns: 67         # Claude 67, Antigravity 45, Cursor 57; Codex self-stopped at 13
  agent_model: Claude Code CLI (Opus 4.8), Codex CLI (GPT-5.5), Antigravity CLI, Cursor CLI (Composer)

# 8. Anti-shortcut ablations (each must be <= 0.15). Best-case degraded submission scored.
anti_shortcut:
  single_frame: 0.0        # real hand shape at a guessed fixed depth -> no metric hit
  video_only: n/a          # audio not used
  audio_only: n/a
  no_media: 0.0            # fixed canonical hand at plausible depth
  frame_dump_no_tools: 0.0039  # eyeballed 2D + 15% scale error + 2 cm noise

# 9. Input media (three short clips; comparison/multi-clip -> exempt from length floor).
input:
  clips: 3
  url: hosted on Hugging Face (see Dockerfile MATERIALS_BASE); baked at build with SHA256
  sha256:
    clip_01: 22d4f7e060ee79eb77eadd58b92c0f3a3e840640aba2f3afc6322aee47c8b729
    clip_02: 5323761ef008f7f0e3d317a9b477c4f9ffd80da6da3504b3280324af93a47544
    clip_03: 6fc266fd070b00e547642ef3e0613ef82ca13a58b8042a86c4259f7bf8269874
  length_min: ~2 min each (short-clip set; exempt from the 10-min single-video floor)
  resolution: 1024x1024 pinhole (>= 720p; rectified from a wider capture)
```
