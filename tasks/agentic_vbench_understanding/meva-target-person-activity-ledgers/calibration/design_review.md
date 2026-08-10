# Design review and repairs

An independent pre-implementation review identified four risks in the earlier
target-person ledger sketch:

1. Multi-person transfer labels could be duplicated under two identities.
2. A selected subset could penalize correct unscored activities.
3. Two contiguous five-minute clips would weaken the long-horizon claim.
4. Strict boundary matching could reject genuine visible occurrences.

The frozen task addresses them as follows:

- Multi-person transfer activities are excluded. The closed vocabulary contains
  only single-target object-handling and vehicle-door activities.
- For each roster target, every closed-vocabulary activity attached to its
  accepted geometry component is included.
- One-minute segments from both source clips are interleaved. Scored evidence
  runs from 1.9 seconds through 534.0 seconds of the ten-minute montage.
- The deterministic scorer grants soft temporal credit from midpoint accuracy,
  interval IoU, and duration agreement, while retaining exact target and
  activity labels and one-to-one matching.

The final gate is direct observability: two independent reviewers inspect all
roster targets, every scored event, and the complete montage for missed
qualifying occurrences before the package is frozen.

The first visual audit found that two proposed vehicle references were one
continuous person whose annotation tracks did not overlap. Both references and
all five of their events were removed instead of introducing a manual identity
join. The frozen package therefore contains ten targets and 29 assignments.
