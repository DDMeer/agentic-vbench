# Calibration — minecraft-gameplay-ledger-s1 (v30)

**Scorer:** `reward = 0.85 · LCS-F1(action, target) + 0.15 · weapon-F1 over LCS-aligned kills`,
order-aware. The weapon component changed in v30 — see *Scorer correction* below — so **v23 numbers
are not comparable to v30 numbers** and are kept in a separate table.

**Media:** `game_v30.mp4`, sha256 `6096f244…652f51e6f069248997459d9b945d9fde7c00`, 1144 s (19.1 min),
**248 events** (83 mine / 147 place / 18 kill), 44 distinct block+mob types, 8 biomes, 3 structures
(cabin, watchtower, well) + a staircase mine, 1280×720 @ 25 fps, no audio.
2.4% of frames uninformative, mean dominant-colour share 0.242.

## v30 — current scorer

| run | score | turns | tokens | notes |
|---|---|---|---|---|
| oracle | **1.0000** | — | — | harness path (`solve.sh` → `judge.py`); ledger 1.0, weapon 1.0 |
| correct multiset, shuffled | 0.2306 | — | — | order sensitivity, not a shortcut (see below) |
| single most-common token ×N | 0.0685 | — | — | genuine shortcut — under the 0.15 bar |
| actions right, all targets "stone" | 0.0240 | — | — | genuine shortcut — under the 0.15 bar |
| empty | 0.0 | — | — | |
| **Codex `gpt-5.6-sol` (xhigh)** | **0.2920** | **332** | 44,962,783 | ledger 0.3057, weapon 0.2143; reported 66 of 248 events |
| Antigravity (Gemini‑3.x) | _to run_ | | | |
| Claude Code (Fable 5 / Opus 4.8) | _to run_ | | | |

## Codex on v30: 0.292 — where it comes from

Codex finished **on its own** (exit 0, ~1 h of a 2.5 h budget, **332 tool calls**, 45.0 M input
tokens, 60.8 k output). It was not cut off, so this is what it judged a complete answer.

- It reported **66 of 248** events — recall **0.19** — but with good precision: LCS 48, so 48 of its
  66 claims were right *and* in the right order (0.73). Order-aware LCS-F1 is deliberately generous
  to a confident partial answer, which is why a 19% recall still scores 0.31 on the ledger.
- **weapon 0.214**, down from 0.643 on v23. It named 10 kills, 7 of which aligned to real kills, and
  got the weapon right on 3. The alignment gate is doing its job.

Decomposition of the drop from 0.4197, using the *same* rollout under both weapon rules (valid — same
video, same ground truth, only the rule differs):

| | ledger F1 | weapon | reward |
|---|---|---|---|
| v23 rollout, old rule | 0.380 | 0.643 | 0.4197 |
| v30 rollout, **old** rule | 0.3057 | 0.714 | 0.3670 |
| v30 rollout, **new** rule | 0.3057 | 0.214 | **0.2920** |

So the scorer fix accounts for **0.075** and the harder video for roughly **0.053**.

### The remaining lever is length, and the arithmetic is specific

The score is recall-limited, and recall is bounded by how much of the video the agent chooses to
examine — not by the video's length. Codex spent ~1 h and stopped voluntarily at 66 reported events.
If that self-imposed effort budget stays roughly fixed while the ledger grows, F1 ≈ 2·LCS/(n_pred +
n_gt) falls close to 1/n_gt:

| session | n_gt | n_pred (assumed ~66) | LCS (assumed ~48) | ledger F1 | reward |
|---|---|---|---|---|---|
| v30, 19 min | 248 | 66 | 48 | 0.306 | 0.292 |
| ~45 min | ~560 | 66 | 48 | 0.153 | ~0.16 |
| ~60 min | ~700 | 66 | 48 | 0.125 | ~0.11 |

The family allows 10–300 min, so this is within spec, and for a *generator* it costs only more phases
— no extra labelling. The assumption to check is whether the agent's effort really stays fixed as the
video lengthens; that is an empirical question and the next measurement, not a claim.

## Length vs difficulty — the recall-limit test (v30 248 ev, v31 633 ev)

The v30 result was recall-limited: Codex reported a confident partial ledger and stopped. The
hypothesis was that a longer video drives a fixed-effort agent's LCS-F1 down as ~1/n_gt, toward the
<0.10 bar. v31 (a 3-lap, 53-min, 633-event session; oracle 1.0, all ablations under bar) tested it
against a FRESH Codex run.

| video | events | Codex tool-calls | n_predicted | LCS | recall | ledger F1 | weapon | **reward** |
|---|---|---|---|---|---|---|---|---|
| v30, 19 min | 248 | 332 | 66 | 48 | 0.19 | 0.306 | 0.214 | **0.292** |
| v31, 53 min | 633 | 767 | 87 | 72 | 0.11 | 0.200 | 0.039 | **0.176** |

**Verdict: length lowers the score (0.292 -> 0.176) but does NOT reach <0.10, because the agent
partially compensates** — given a longer video it spent more than twice the tool-calls (332 -> 767)
and reported more events (66 -> 87), so recall fell only 0.19 -> 0.11 rather than as 1/n_gt. Reward
tracks ledger_f1 = 2*LCS/(n_pred + n_gt); with the agent's own LCS/n_pred growth, reaching
ledger_f1 = 0.10 extrapolates to roughly n_gt ~ 1800-2400 events, i.e. a **~150-200 min** session.
That is inside the family's 10-300 min window but is a large render.

So this is honestly a **MEDIUM task (~0.18 at 53 min)**, not a sub-0.10 task at practical lengths.
Two clean options, the choice is a scope call:
  1. **Ship as medium.** Report 0.176 at 53 min; it is a well-formed, oracle-1.0, ablation-clean
     ordered-reconstruction task that a strong agent only partly solves.
  2. **Push length to ~150-200 min** for <0.10. The generator already supports it (P1_LAPS); cost is
     the render + a ~190M-token calibration, scaling with length.

The order-aware LCS-F1 is deliberately generous to a confident partial answer (the family's chosen
metric), which is the root reason a partial ledger scores ~0.18 rather than near-0.

## Scorer correction found in v30 calibration

The weapon sub-score was an independent LCS-F1 over the kill-weapon sequence. With only **two**
weapon classes that stays high no matter how wrong the ledger is, so it handed out credit nobody
earned:

| ablation | ledger | weapon (old) | reward (old) | weapon (new) | reward (new) |
|---|---|---|---|---|---|
| actions right, targets "stone" | 0.028 | **1.000** | 0.174 | 0.000 | **0.024** |
| correct multiset, shuffled | 0.242 | 0.722 | 0.314 | 0.167 | **0.231** |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | **1.000** |

Weapon credit is now granted only on kill events inside the ledger's LCS alignment — the weapon of a
kill you never identified is meaningless. The oracle is unaffected, and both genuine shortcuts fall
under the family's 0.15 bar.

**On the shuffled row (0.231):** this is reported as a property, not a failed bar. Reproducing the
exact multiset of 248 events requires watching the whole video; it is most of the work, not a way
around it. The order-aware metric is deliberately generous to a right-but-misordered answer.

## v23 — previous scorer (NOT comparable)

Media was 843 s / 237 events, and the weapon component was scored independently.

| run | score | turns | tokens | notes |
|---|---|---|---|---|
| oracle | 1.0 | — | — | |
| **Codex `gpt-5.6-sol` (xhigh)** | 0.4197 | 74 | 4,692,528 | ledger 0.380, weapon 0.643 |

That 0.4197 is **not** re-scored under the v30 scorer and must not be: the rollout was produced
against a different video and different ground truth, so a rescore would be a number about nothing.
A fresh run is the only honest comparison. (An earlier kart calibration made exactly this mistake —
a rescored rollout reported 0.066 when the targeted run scored 0.335.)

Config: `codex exec --dangerously-bypass-approvals-and-sandbox`, Codex CLI v0.145.0,
`model = gpt-5.6-sol`, `model_reasoning_effort = xhigh`, ffmpeg/ffprobe on PATH.
An earlier attempt with a 55-minute cap timed out at 42 turns having written nothing; the run
above was given 2.5 h and told to write the ledger early and refine it.

## Finding: this task is NOT at the <0.10 bar — it is a medium task

Codex scores **0.42**. Where that comes from:

- It reported **89 of 237** events (recall 0.26) but got them largely in the right order
  (LCS 62, precision 0.70). Order-aware LCS-F1 is deliberately generous to a partial-but-correct
  answer, so a confident subset scores 0.38 on the ledger component.
- **`weapon_f1` is 0.643**, the weakest part of the design. The composited HUD highlights the
  held item precisely so the weapon field is answerable — and that same indicator makes it easy
  to read. This is the identical failure mode calibration found in the kart task, where the
  ranking column handed over the finishing order.

There is an inherent tension here that should be stated rather than hidden: several rounds of
work went into making *every* scored action visible on camera (witnessed-kill and
witnessed-placement gates, a mob roster restricted to what the renderer actually draws, a camera
that holds on each block). Fairness demands that. But an action that is clearly visible is also
more identifiable, so the fairness work is part of why the score is 0.42 rather than <0.10.

Options, not yet chosen (the same discipline applied to kart — do not tune the metric until it
passes):
1. **Weight the weapon component down or drop it**, since the HUD is a proxy for it.
2. **Raise recall difficulty**: many more events, and visually-confusable targets (several plank
   and log variants, terracotta shades) so identification is genuinely hard rather than merely
   long.
3. **Accept it as a medium-difficulty entry** at ~0.42.

The proposal issue has deliberately **not** been filed, because claiming "<0.10 for all three
agents" would be false.
