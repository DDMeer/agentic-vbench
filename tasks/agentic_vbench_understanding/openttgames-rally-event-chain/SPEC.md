---
title: OpenTTGames Rally Event-Chain Reconstruction Spec
summary: Spec Card for full-match table-tennis rally event-chain reconstruction.
read_when: Reviewing or calibrating this task.
---

# Task Spec Card

```yaml
task: agentic_vbench_understanding/openttgames-rally-event-chain

cognitive_level: understanding

modalities_required:
  video: >
    Rally discovery, racket-contact timing, player identity,
    forehand/backhand classification, stroke-type recognition,
    and rally-ending classification require temporal visual evidence.
  audio: not used

question: >
  Reconstruct the ordered stroke chain and terminal outcome for each valid
  rally in a full 23-minute-55-second table-tennis match.

output_schema: >
  Rally-grouped JSON containing serve timestamp in seconds,
  ordered timestamped stroke sequence with player, hand, and stroke type,
  and timestamped terminal rally outcome.

evidence:
  - t=7.28s, video, early-match rally requiring serve and ordered stroke-chain reconstruction
  - t=1346.79s, video, late-match rally requiring the same reconstruction near the end of the full video

ground_truth:
  source: Extended OpenTTGames game_2 frame-level annotations
  tier: dataset-provided
  verification: >
    Ground truth is generated deterministically from the published
    frame-level annotations. Serve events define candidate rally windows.
    Adjacent identical terminal labels within 2 frames are deduplicated.
    Rally windows without exactly one explicit terminal annotation after
    deduplication are excluded. Regenerating the reference from the source
    annotation produces exact JSON equality with the verifier reference.

input:
  url: https://lab.osai.ai/datasets/openttgames/data/game_2.mp4
  sha256: 330ac07730bae6d899dbbbd00ad43500c583e6af6ea6dd261565bc77811eba66
  size_bytes: 10833064677
  length_min: 23.9167
  fps: 120
  resolution: 1920x1080
  frames: 172200

dataset_summary:
  total_annotation_events: 1575
  total_serves: 92
  valid_rallies: 86
  excluded_incomplete_rallies: 6
  annotated_strokes: 399
  benchmark_strokes: 384

scorer:
  metric: >
    Rally discovery F1 using serve timestamps within 1.0 s, multiplied by
    rally-ending score, stroke-timing F1 with 0.35 s tolerance, and mean
    F1 across player, hand, and stroke-type fields.
  oracle_reward: 1.0
  null_reward: 0.0
```
