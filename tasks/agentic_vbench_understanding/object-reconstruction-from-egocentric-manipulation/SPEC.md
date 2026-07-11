---
title: Task Spec Card
summary: 3D reconstruction of interacted objects from three egocentric clips.
read_when: Reviewing or reproducing this video-understanding task.
---

# Task Spec Card

```yaml
task: agentic_vbench_understanding/object-reconstruction-from-egocentric-manipulation

# 1. What kind of thinking does this task need?
cognitive_level: reasoning
# The output is a full 3D surface mesh, synthesised from many partial views of an
# object being turned over in hand. The agent must integrate silhouettes/appearance
# across the clip under the given camera model into one consistent 3D shape: multi-
# view geometric reasoning, not perception of any single frame.

# 2. Which modalities are REQUIRED (not just present)?
modalities_required:
  video: The 3D shape only emerges from many viewpoints across the clip as the object
    is rotated; no single frame shows the whole surface, and no caption encodes geometry.
  audio: not used

# 3. The exact question and output schema.
question: For each of the three clips, reconstruct the 3D surface mesh of that clip's
  designated target object from how it appears across the clip.
output_schema: >
  One triangle mesh per clip in /workspace/output/, named by clip id: clip_01.obj (or
  .ply/.glb/.stl), clip_02.*, clip_03.*. Each is vertices + triangular faces. Scale and
  pose are free, scored after a best-fit similarity alignment.

# 4. Evidence chain.
evidence:
  - "Each object is grasped, lifted, and rotated through the clip; recovering the full
     surface requires fusing views from far-apart moments across the whole ~2 min clip."
  - "Three separate objects across three clips: the agent must reconstruct each from
     its own clip; there is no shortcut that covers all three."
  - "Self-occlusion means no single frame is sufficient; back and bottom faces only
     appear at specific later moments as the hand reorients the object."

# 5. Ground truth.
ground_truth:
  source: The scanned 3D reference mesh of each interacted object (the capture set's
    object models), sampled to a dense reference point cloud baked into the verifier.
  tier: logged
  verification: "Reference mesh reprojects onto the object silhouette in sampled frames;
    mesh diameters are physically sensible (16-42 cm); each object is confirmed present
    and manipulated in its clip."

# 6. Scorer: deterministic code only.
scorer:
  metric: >
    Per clip, after a best-fit similarity alignment (PCA-frame + 24 octahedral rotations
    + similarity-ICP, symmetric trimmed-chamfer ranking): score = surface-F^2 *
    (voxel-IoU / oracle_iou), clipped to [0,1]. The surface F-score (self-calibrating
    tolerance = 4 median NN spacings) catches wrong/partial surfaces; the flood-filled
    volumetric IoU collapses concavity-filling convex hulls and silhouette slabs. The IoU
    is normalised by the per-object oracle_iou ceiling (the IoU the true mesh reaches
    under independent resampling+voxelisation, baked at authoring) so the true shape
    scores 1.0. reward = mean over the three clips.
  oracle_reward: 1.0   # measured: 0.9985-1.0 end-to-end in Docker (>= 0.999)
  null_reward: 0.0     # measured: empty output dir

# 7. Difficulty: measured with real strong-agent runs.
difficulty:
  strong_agent_reward: 0.043  # Claude 0.043, Antigravity 0.033, Cursor 0.019, Codex 0.014 (all < 0.10)
  tool_call_turns: 64          # Antigravity 64, Cursor 60 (>50); Claude 46, Codex 11
  agent_model: Claude Code CLI (Opus 4.8), Codex CLI (GPT-5.5), Antigravity CLI, Cursor CLI (Composer)

# 8. Anti-shortcut ablations (each must be <= 0.15). Best-case degraded submission scored.
anti_shortcut:
  single_frame: <= 0.13    # a silhouette slab (extruded 2D bbox) scores 0.005-0.012
  video_only: n/a          # audio not used
  audio_only: n/a
  no_media: 0.0           # empty output / stock mesh; wrong object (keyboard) = 0.003-0.009
  frame_dump_no_tools: <= 0.13  # a convex hull (no concavity, best tool-less guess):
    # coffee_pot 0.127, spatula_red 0.017

# 9. Input media (three short clips; multi-clip -> exempt from length floor).
input:
  clips: 3
  objects: [coffee_pot, coffee_pot, spatula_red]   # concave shapes (survive the hull test)
  url: hosted on Hugging Face (see Dockerfile MATERIALS_BASE); baked at build with SHA256
  sha256:
    clip_01: 2f153d49b5c6b61e58d6b648af1002718dddd2fe2b32c6ba28d4e9d80d388a1c
    clip_02: bbfabad6a5e5736de3ec5de7d31cee679c8c8267fdb0bc88ca52bcc8c82f47e6
    clip_03: 9d2cd0f8127622bc5805f4cbaf83efcbf17a9ad8d1f46748a26a9ccb7c5ab546
  length_min: ~2 min each (short-clip set; exempt from the 10-min single-video floor)
  resolution: 1024x1024 pinhole (>= 720p; rectified from a wider capture)
```
