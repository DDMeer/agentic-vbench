# Three-Point Timeline Reconstruction

You are given one video at `/workspace/materials/game.mp4`: the full broadcast of an
NBA game (Golden State Warriors vs Cleveland Cavaliers). Reconstruct the complete
timeline of every made three-point field goal in the game, by either team.

For each made three, report the quarter, the game clock at the moment it was made,
who made it, and who assisted it (or `unassisted`). Use any tools in the image (for
example `ffmpeg` and `ffprobe`) to seek through and sample the video. The on-screen
score-and-clock graphic, the players' jerseys, and the play action are your evidence.

## What to submit

Write `/workspace/output/solution.json` in exactly this shape:

```json
{
  "three_pointers": [
    {"quarter": 1, "clock": "11:02", "shooter": "JR Smith",      "assister": "LeBron James"},
    {"quarter": 1, "clock": "8:47",  "shooter": "Stephen Curry", "assister": "unassisted"}
  ]
}
```

- One entry per made three-pointer, in any order.
- `quarter`: 1 to 4.
- `clock`: the game clock shown when the shot was made, as on the broadcast (`mm:ss`,
  or seconds when under a minute).
- `shooter`: the player's full name (first and last).
- `assister`: the assisting player's full name, or `unassisted`.

## Rules

- Stay inside this working directory. Do not read, write, or search outside it.
- Do not look anything up online, and do not rely on memory of this game; find every
  shot in the video.
- Count only made three-pointers, not attempts, not two-pointers, not free throws.
