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
    forehand/backhand classification, stroke-technique recognition,
    and terminal-outcome classification require temporal visual evidence.
    Only contacts visible in frame are scored; the camera framing is narrower
    than the playing area, so observability is itself part of the task.
  audio: not used

question: >
  Reconstruct the ordered stroke chain and terminal outcome for every
  live-play rally whose serve contact is visible in a full
  23-minute-55-second table-tennis match.

output_schema: >
  Rally-grouped JSON containing serve timestamp in seconds, an ordered
  timestamped stroke sequence with player, hand, and stroke technique,
  and a timestamped terminal rally outcome. Serve timestamps are matched
  within 1.0 s, stroke timestamps within 0.35 s, and ending timestamps
  within 1.0 s.

evidence:
  - t=7.28s, video, early-match rally requiring serve and ordered stroke-chain reconstruction
  - t=1346.79s, video, late-match rally requiring the same reconstruction near the end of the full video
  - t=102.71s, video, rally 8 terminates on a net-stop that must be distinguished
    from the separate point played later in the same annotation window

ground_truth:
  source: >
    Extended OpenTTGames game_2 frame-level structured annotations from
    moamal01/table_tennis_data commit
    36471a76b969a0340df59258a813bf8214e68e7c,
    data/raw/game_data/train/game_2.json,
    annotation SHA256
    7466f1f8c46316406ae224a17491354eac89f9cc2de858633b6f893573db4fe7.
    Six source-terminal gaps and one two-point serve window are handled as
    explicitly documented bounded video-audit exceptions.
  tier: machine-truth
  verification: >
    Serve events define 92 rally windows. Ordinary exact "net" events are
    treated as non-terminal net crossings, while supported player-prefixed
    ending labels define terminal outcomes. Adjacent identical terminal labels
    within 2 frames are deduplicated. Six live-play windows
    (rally IDs 13, 16, 18, 24, 55, and 73) contain no source terminal
    annotation; only their missing terminal outcomes were completed by
    bounded frame-level inspection of the official video. Serve window 8 spans
    two points - the scoreboard moves 4:3 to 4:4 inside the gap - so it is
    truncated at frame 12325 (102.708 s, the frame at which the net arrests the
    ball's forward motion) with terminal left_net, and the second point is
    excluded in full (12 strokes) because its serve contact frame is not
    resolvable in the source video. Cross-referencing strokes against the
    source's own net/bounce events surfaced 26 unannotated opponent contacts;
    23 were confirmed off-frame and 3 were examined at 1/120 s and found to
    show no labellable contact, so no stroke was added to the benchmark. No
    serve window is silently excluded. Deterministic regeneration produces 92
    benchmark rallies containing 387 source-derived strokes, and the generated
    solution and verifier references are byte-for-byte identical.

scorer:
  metric: >
    Rally discovery uses F1 over serve timestamps matched within 1.0 s.
    Within matched rallies, strokes are matched in order within 0.35 s.
    Stroke semantic credit is awarded only when the complete
    (player, hand, stroke) tuple matches for a timing-aligned stroke.
    Rally-ending credit is awarded only when both the exact ending label
    and ending timestamp within 1.0 s match. The final reward is the
    product of rally-discovery F1, joint rally-ending accuracy,
    stroke-timing F1, and joint stroke-semantic F1.
  oracle_reward: 1.0
  null_reward: 0.0

difficulty:
  # Filled once all three harnesses are calibrated, per family precedent: every
  # merged task in this family ships this card complete. Two of three are done
  # (Codex 0.001858 / 53 turns, Antigravity 0.000000 / 164 turns, both clearing
  # the gates); the measured values live in calibration/scores.md until Claude
  # Code and the ablations land.
  strong_agent_reward: pending final calibration
  tool_call_turns: pending final calibration
  agent_model: pending final calibration

anti_shortcut:
  single_frame: pending final calibration
  video_only: not applicable; audio is not a required modality
  audio_only: not applicable; audio is not a required modality
  no_media: pending forced-answer no-media calibration
  frame_dump_no_tools: pending final calibration

input:
  url: https://lab.osai.ai/datasets/openttgames/data/game_2.mp4
  sha256: 330ac07730bae6d899dbbbd00ad43500c583e6af6ea6dd261565bc77811eba66
  length_min: 23.9167
  resolution: 1080
```

## Dataset and provenance summary

- Official video size: 10,833,064,677 bytes
- Video frame rate: 120 fps
- Video frame count: 172,200
- Source annotation events: 1,575
- Serve-defined rally windows: 92
- Published stroke annotations: 399
- Benchmark rallies: 92
- Benchmark strokes: 387
- Silently excluded serve windows: 0
- Bounded source-terminal exceptions: 6
- Exception rally IDs: 13, 16, 18, 24, 55, 73
- Video-gap truncations: 1 (rally 8)
- Strokes excluded by that truncation: 12
- Strokes added by manual audit: 0

The six terminal exceptions change only otherwise-missing terminal outcomes.
The rally 8 truncation removes a second point whose serve contact frame is not
resolvable in the source video. No stroke was added by hand; every benchmark
stroke remains source-derived. See `calibration/source-exception-audit.md` for
the scoped video audit and `calibration/generation_audit.json` for
deterministic generation metadata.

## Observability boundary

The fixed camera framing is narrower than the playing area, so a player who
retreats to return a ball can leave the frame. Cross-referencing the source's
own `net` and `bounce` events against its stroke labels surfaces 26 opponent
contacts that physically occurred but carry no annotation; 23 are confirmed
off-frame and 3 were examined frame by frame without yielding a labellable
contact. The benchmark therefore scores only contacts observable in the media,
and `steps/solve/instruction.md` states that rule to the agent: report only
visible contacts, never infer one from the ball's later path, and omit a rally
whose serve contact is not visible. This keeps the reachable ceiling at 1.0 for
an agent that perceives the video correctly.

## Difficulty

Final difficulty values are intentionally deferred until the agent-facing
contract, ground truth, and verifier are frozen. Final calibration must use
the current task image with Internet access disabled.

The final calibration record belongs in `calibration/scores.md` and must
include one current-image run each for Codex, Claude Code, and Antigravity,
including harness/model versions, reward, tool-call turns, and the raw native
trajectory location.

## Anti-shortcut checks

After the task contract is frozen, run exactly the required degraded-input
checks:

- single representative frame only;
- forced answer with no media;
- all frames available but no agentic tools.

Each degraded-input run must score at or below 0.15. If one exceeds that
threshold, fix the shortcut rather than changing the threshold.