---
title: Task Spec Card
summary: Object 6DoF pose trajectory from three egocentric manipulation clips.
read_when: Reviewing or reproducing this video-understanding task.
---

# Task Spec Card

```yaml
task: agentic_vbench_understanding/objects-tabletop-manipulation-6dof-pose-trajectory

# 1. What kind of thinking does this task need?
cognitive_level: reasoning
# The answer is a metric 6DoF pose per frame: position and orientation in the camera
# frame. The agent must track the designated object through an egocentric clip,
# reason about the given camera geometry, and infer both where the object is (metric
# depth) and how it is oriented over time. Spatial/geometric reasoning, not a readout.

# 2. Which modalities are required (not just present)?
modalities_required:
  video: The 6DoF pose lives in the moving imagery. Metric depth and 3D orientation
    resolve only by tracking the object's silhouette/features across frames under the
    supplied camera model. No frame or caption states the pose.
  audio: not used

# 3. The exact question and output schema.
question: For each query frame in each of the three clips, give the designated target
  object's 6DoF pose (translation in metres + orientation quaternion) in that clip's
  RGB camera frame.
output_schema: >
  {"clips": {"clip_01": [{"frame": int, "t_xyz_m": [x,y,z], "q_wxyz": [w,x,y,z]}],
  "clip_02": [...], "clip_03": [...]}}. t in metres (camera frame +Z fwd, +X right,
  +Y down); q a unit quaternion, w first. Scored by ADD with tau = 10% of the object
  diameter.

# 4. Evidence chain.
evidence:
  - "36 query frames total (12 per clip) spread across the middle 90% of each ~2 min
     clip: the answer is distributed over the whole timeline."
  - "Each pose needs both metric depth and 3D orientation, which for a monocular
     monocular view resolve only by integrating the object's motion/parallax across many
     neighbouring frames plus the supplied camera intrinsics."
  - "The object is grasped, lifted, and turned over. Its pose changes substantially
     across the clip (camera-frame net displacement ~0.4-1.9 m), so a single guess
     cannot cover the trajectory."

# 5. Ground truth.
ground_truth:
  source: The capture rig's logged object-pose tracking (per-frame T_world_object),
    transformed into each clip's RGB camera frame using the logged device trajectory
    and factory camera extrinsics.
  tier: logged
  verification: "Object mesh reprojected with the logged pose overlays the visible
    object in sampled frames; camera-frame depth stays in the plausible arm's-reach
    range (0.1-1.5 m) at every query; poses are temporally continuous."

# 6. Scorer: deterministic code only.
scorer:
  metric: >
    Per query, ADD = mean over the object's baked mesh points of ||T_pred·p - T_gt·p||;
    frame_score = clip(1 - ADD / TAU, 0, 1), TAU = 0.10 * object_diameter. ADD-S
    (nearest-neighbour) for symmetric objects (none flagged here). reward = mean over
    36 query frames.
  oracle_reward: 1.0
  null_reward: 0.0   # measured: empty/None submission

# 7. Difficulty: measured with real strong-agent runs.
difficulty:
  strong_agent_reward: 0.0    # Claude Opus 4.8, Codex GPT-5.5, Cursor Composer, all 0.0
  tool_call_turns: 80         # Claude 80, Antigravity 100(isolated), Cursor 62; Codex self-stopped at 12
  agent_model: Claude Code CLI (Opus 4.8), Codex CLI (GPT-5.5), Antigravity CLI, Cursor CLI (Composer)

# 8. Anti-shortcut ablations (each must be <= 0.15). Best-case degraded submission scored.
anti_shortcut:
  single_frame: 0.0833     # one true pose repeated across the moving trajectory
  video_only: n/a          # audio not used
  audio_only: n/a
  no_media: 0.0           # fixed plausible pose, identity rotation
  frame_dump_no_tools: 0.0  # 5 cm translation error + guessed rotation

# 9. Input media (three short clips; multi-clip -> exempt from length floor).
input:
  clips: 3
  objects: [birdhouse_toy, vase, potato_masher]   # all asymmetric
  url: hosted on Hugging Face (see Dockerfile MATERIALS_BASE); baked at build with SHA256
  sha256:
    clip_01: aefb41b216cc2cbacfca639de8175a29f37006c3be730b118928ce20e27d19ee
    clip_02: b187d5cbaba972ca715f0ffd670b99b1c77ee9ad579d40b3acdff1b564c114ae
    clip_03: 56c42f94baecf5a78e2b6e32ed5af59719b51badfc6405d3f67d9b26bbc77520
  length_min: ~2 min each (short-clip set; exempt from the 10-min single-video floor)
  resolution: 1024x1024 pinhole (>= 720p; rectified from a wider capture)
```
