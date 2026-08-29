# Source-terminal exception audit

The benchmark ground truth is derived from the commit-pinned Extended OpenTTGames
annotation for `game_2`.

Six serve-defined windows contain real live-play exchanges in the official video
but have no supported terminal annotation in the pinned source annotation.
Per maintainer review, only these six source-terminal gaps were manually
video-audited.

The source-provided stroke sequences were retained unchanged. Only the missing
terminal event was completed.

| Rally ID | Serve time (s) | Source state | Video-audited terminal | Ending anchor (s) |
|---:|---:|---|---|---:|
| 13 | 195.158 | No supported terminal label after the source strokes | Left player's return lands on the right side; the right player then catches the ball by hand -> `left_winner` | 197.583 |
| 16 | 218.792 | No supported terminal label after the source strokes | Right player's return ends the point when the left player does not make a legal return and catches/stops the ball -> `right_winner` | 220.767 |
| 18 | 236.108 | No supported terminal label after the source strokes | Left player's final return is stopped by the net -> `left_net` | 239.833 |
| 24 | 331.967 | No supported terminal label after the serve | Right player's serve is stopped by the net -> `right_net` | 332.200 |
| 55 | 771.217 | No supported terminal label after the source strokes | Right player's return fails to cross the net -> `right_net` | 772.933 |
| 73 | 1057.983 | No supported terminal label after the source strokes | Left player's return lands on the right side; the right player then catches the ball by hand -> `left_winner` | 1059.367 |

## Scope

This is a bounded exception audit, not a relabeling pass over the benchmark.

The six terminal completions above are the only manual additions to the
commit-pinned source annotation. All 399 stroke annotations remain
source-derived.

The video audit used the official `game_2.mp4` media corresponding to the
benchmark source. Ending anchors were selected through fine-grained frame
inspection and mapped to the benchmark's 120 fps video timeline.

After applying these six documented exceptions, the generated benchmark contains
92 valid rallies, 399 source-derived strokes, and zero silently excluded
serve-defined windows.
