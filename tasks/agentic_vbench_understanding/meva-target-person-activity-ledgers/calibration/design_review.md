# Current design

The task is hard perception over one ten-minute, 1080p surveillance montage.
The agent must exhaustively find six allowed activities and assign every
occurrence to one of ten video-local roster targets.

- Ground truth contains every closed-vocabulary activity attached to each
  selected geometry component.
- Activity-local person tracks are linked only with at least 20 shared frames,
  median IoU at least 0.90, and nearest-rank q10 IoU at least 0.80.
- The montage interleaves exact 1,800-frame source segments and contains 18,000
  frames at 30 fps.
- The deterministic scorer requires exact target and activity type, then grants
  temporal credit from midpoint accuracy, interval IoU, and duration agreement
  under one-to-one matching.
- Ground truth is stored at a root-only image path outside Harbor's uploaded
  tests directory. The evaluated agent is non-root and the verifier is root.
- Submission validation rejects symlinks, hardlinks to ground truth, FIFOs,
  non-regular files, and files larger than 1 MB.

Independent final reviews accepted all ten targets, all 29 assignments, montage
alignment, licensing, leakage controls, scorer behavior, and verifier isolation.
