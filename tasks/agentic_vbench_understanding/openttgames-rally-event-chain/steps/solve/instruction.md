# Full-match table-tennis rally event-chain reconstruction

Analyze the complete table-tennis match at:

`/workspace/materials/game.mp4`

Reconstruct the ordered stroke chain for every valid live-play rally in the
match.

Use local tools such as FFmpeg, ffprobe, scripts, and frame extraction.
Inspect the full video. Do not use the Internet, pre-existing annotations,
or files outside `/workspace`.

## Definitions

- A **valid rally** starts at the serve racket contact and ends with one of
  the supported terminal outcomes listed below.

- Only report rallies for which both the serve and a supported terminal
  outcome can be identified.

- Count the serve as the first stroke.

- A **stroke** is a racket contact that sends the ball toward the opponent.

- Do not count warm-ups, dead-ball swings, or actions between rallies.

- Player identities are defined by their fixed video-side positions:
  `left` and `right`.

- `hand` must be exactly one of:
  - `forehand`
  - `backhand`

- `stroke` must be exactly one of:
  - `serve`
  - `loop`
  - `block`
  - `push`
  - `flick`
  - `lob`
  - `smash`
  - `chop`

- Rally endings must use exactly one of:
  - `left_out`
  - `right_out`
  - `left_net`
  - `right_net`
  - `left_winner`
  - `right_winner`
  - `left_double_bounce`
  - `right_double_bounce`
  - `left_not_hitting_ball`
  - `right_not_hitting_ball`
  - `left_miss_on_own_side`
  - `right_miss_on_own_side`

- All timestamps are in seconds from the first video frame.

- Report the strokes of each rally in chronological order.

- Report rallies in chronological order by serve time.

## Required output

Write valid JSON to:

`/workspace/output/solution.json`

Use this schema:

```json
{
  "rallies": [
    {
      "serve_time_sec": 7.283,
      "strokes": [
        {
          "time_sec": 7.283,
          "player": "right",
          "hand": "forehand",
          "stroke": "serve"
        },
        {
          "time_sec": 8.058,
          "player": "left",
          "hand": "backhand",
          "stroke": "push"
        },
        {
          "time_sec": 8.675,
          "player": "right",
          "hand": "backhand",
          "stroke": "push"
        }
      ],
      "ending_time_sec": 9.625,
      "ending": "left_out"
    }
  ]
}
## Evaluation tolerances

- `serve_time_sec`: within 1.0 second of the serve contact.
- each stroke `time_sec`: within 0.35 seconds of the racket contact.
- `ending_time_sec`: within 1.0 second of the terminal rally event.

Categorical fields must use exactly the vocabulary defined above.
