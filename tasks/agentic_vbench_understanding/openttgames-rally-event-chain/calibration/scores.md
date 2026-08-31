# Calibration — openttgames-rally-event-chain

Frozen at commit `1b7cbd5e1473a07405ad481c6179f98b2aca70f0`; every run below used that
commit's task files and the image built from its `environment/Dockerfile`.

Deterministic scorer `steps/solve/tests/judge.py`, no VLM or LLM judge.
`reward = rally_discovery_F1 × ending_joint_accuracy × stroke_timing_F1 × stroke_semantic_joint_F1`.

## Anchors

| run | reward |
|---|---:|
| oracle (`steps/solve/solution/solve.sh`) | **1.000000** |
| empty / null submission | 0.000000 |
| malformed / symlink-to-reference | 0.000000 |
| all timestamps shifted +5 s | 0.000000 |
| any single semantic field wrong (player, hand, stroke, ending label, ending time) | 0.000000 |
| serve-only ("sparse one stroke") | 0.147559 |

Thirteen regression assertions in `steps/solve/tests/test.sh`; all pass.

## Agent calibration

| harness | harness version | model | reasoning | reward | tool-call turns | wall time | trajectory |
|---|---|---|---|---:|---:|---:|---|
| Codex CLI | 0.147.0 | `gpt-5.6-sol` | high | **0.000078** | **150** | 36 min | `rollouts/codex_gpt-5.6-sol.jsonl` |
| Antigravity CLI [^parity] | 1.1.22 | `gemini-3.1-pro-high` | high | **0.000000** | **164** | 42 min | `rollouts/antigravity_gemini-3.1-pro-high.native.jsonl` |
| Claude Code CLI [^seg] | 2.1.251 | `claude-opus-4-8` | default | **0.041168** | **123** | 99.4 min | `rollouts/claude_claude-opus-4-8.jsonl` + `.seg2.jsonl` |

[^seg]: One Claude Code session executed in two segments, separated by a
subscription-window interruption, and reported as the sum. Both segments carry the
same `session_id`
`40ddfba8-6703-4fd8-bf91-6c39f778d500`, which is what ties them together.
Segment 1 (2026-08-30 23:20Z, 86 tool-call turns, 68.3 min, `is_error=true`) stopped
when the five-hour window filled with `output/` still empty. Segment 2
(2026-08-31 04:03Z, 37 turns, 31.1 min) resumed that same conversation with
`claude --continue` -- not a fresh agent rediscovering leftover files -- and finished
on its own (`is_error=false`), writing a 66 KB `output/solution.json`. Segment 2's 37
turns alone would not clear the >50 gate; the reported 123 is the sum. Neither segment
used subagents.

[^parity]: Antigravity used the pre-finalization shared rules rather than the finalized
minimal rules. The measured result is reported as-is; a strict-parity rerun can be
provided if requested.

All three harnesses have completed measured runs, and the required ablation evidence is
reported below -- with the documented frame-dump substitute caveat. Codex
and Claude Code ran under the finalized calibration setup; the Antigravity row keeps the
documented pre-finalization-rules caveat below. Every row clears the family gates: reward < 0.10 and more than 50 tool-call turns. The project's own
`scripts/understanding/check_task.py` passes all eight checks it can run here --
structure, oracle 1.0, null baseline 0.0, strong agent 0.041168 < 0.1, 123 turns > 50,
and all three required ablations at 0.0 <= 0.15.

The Codex row is the run of 2026-08-30 under the minimal shared rules
(`runpack/AGENTS.md`, sha256 `779eec27…`). Two earlier Codex runs are kept in full as
evidence rather than deleted, because the differences between them are the reason the
shared rules ended up where they did:

| rules version | turns | reward | kept at |
|---|---:|---:|---|
| pre-finalization (2026-08-29) | 53 | 0.001858 | `rollouts/historical_codex_oldrules/` |
| with "Working efficiently" section (2026-08-30) | 31 | 0.000020 | `rollouts/historical_codex_efficiencyrules/` |
| minimal, current (2026-08-30) | 150 | 0.000078 | `rollouts/` |

The middle run does not clear `tool_call_turns > 50`, which is why the efficiency
section was removed from the shared rules. **This is not a clean attribution.** The three
runs differ in more than one way at a time -- the 2026-08-29 rules also carried a line
reading "A complete best-effort answer beats an empty one", which was removed as
output-shaping guidance -- and each condition has n=1. The spread (53 / 31 / 150) is
wide enough that run-to-run variance alone could account for a large part of it. What is
established is that the reported run clears both gates, not that the efficiency section
caused the middle run's shortfall.

Only completed runs are reported as results. Attempts truncated by provider errors,
resource limits, harness defects, or a contamination detection were discarded, never
graded, and are not represented in any number above; they are retained locally under
`rollouts/aborted/` and are available on request. The Claude Code attempt of 2026-08-30
was stopped manually on cost grounds after 73 minutes with no `output/solution.json`
written; it is not scored and not reported as a result.

### Per-field diagnostics

| | Codex | Antigravity | Claude Code |
|---|---:|---:|---:|
| rally-discovery F1 | 0.364641 | 0.020000 | 0.853933 |
| stroke-timing F1 | 0.065979 | 0.009195 | 0.743003 |
| stroke-semantic joint F1 | 0.008247 | 0.000000 | 0.259542 |
| rally-ending joint accuracy | 0.393939 | 1.000000 | 0.250000 |
| rallies predicted / matched (ref 92) | 89 / 33 | 8 / 1 | 86 / 76 |
| strokes predicted / matched (ref 387) | 98 / 16 | 48 / 2 | 399 / 292 |

Antigravity's ending accuracy of 1.0 is a one-of-one artefact: it matched a single rally
and happened to get that ending right. It does not survive the product, and the run
reconstructed 8 of 92 rallies.

### How tool-call turns were counted

Each harness records work differently, so each is counted with its own rule and the rule
is stated rather than assumed:

- **Codex CLI** — distinct `item.started` records of type `command_execution`: **150**.
  A looser pattern that also counts `file_change` gives 63; the stricter shell-call count
  is reported.
- **Antigravity CLI** — distinct `step_index` whose record type is a tool action
  (`RUN_COMMAND`, `VIEW_FILE`, `CODE_ACTION`, `LIST_DIRECTORY`, …) in the CLI's **native
  transcript**: **164**.

  The CLI's `--output-format stream-json` on stdout is **not** a reliable record: in an
  earlier run it captured steps 0–76 and went silent the moment a long `run_command`
  started, while the CLI itself continued to step 186. The native transcript under
  `~/.gemini/antigravity-cli/brain/<conv>/` is therefore the authoritative artefact, and
  is what is shipped here. `num_turns` from the CLI is unusable — it reported `1` for a
  run with 40 real tool steps.
- **Claude Code CLI** — distinct `tool_use` blocks in the assistant messages of the
  `stream-json` transcript, de-duplicated by block id: **86** in session 1 and **37** in
  session 2, **123** total. The CLI's own `num_turns` is a different quantity and is not
  used — it reported `45` for session 2, counting assistant turns rather than tool calls.
  Segments are matched to the run by `session_id`, not by filename.

## Anti-shortcut ablations

Every ablation is a real Codex CLI 0.147.0 / `gpt-5.6-sol` high run on the degraded
input, in the shipped image, under the same shared rules file and the same egress policy
as the calibration row -- on a dedicated ablation gate, separate from the scored
calibration gate -- graded by the same frozen `judge.py`. Family gate: each must score
at or below 0.15.

| ablation | reward | turns | rallies submitted (ref 92) | strokes submitted (ref 387) | trajectory |
|---|---:|---:|---:|---:|---|
| `single_frame` | **0.000000** | 4 | — | — | `ablations/ablation_single-frame.jsonl` |
| `no_media` | **0.000000** | 3 | — | — | `ablations/ablation_no-media.jsonl` |
| `no_media` forced-answer | **0.000000** | 5 | 0 | 0 | `ablations/ablation_no-media-forced.jsonl` |
| `frame_dump_no_tools` (substitute) | **0.000000** | 44 | 89 | 89 | `ablations/ablation_frame-dump.jsonl` |

The forced-answer variant is the one the review asked for; the plain `no_media` row is
kept beside it because the two fail differently and the difference is the point.
| `video-only` / `audio-only` | n/a | — | — | — | audio is not a required modality |

All four clear the gate. What each one actually shows differs, and the difference matters
more than the shared 0.0:

**`single-frame` and `no-media` are refusals, not guesses.** Neither agent wrote
`output/solution.json` at all. From the single-frame transcript: "I did not fabricate
`output/solution.json` from the single frame." The `{"rallies": []}` recorded as those
runs' submissions is the harness's substitution for a missing file, not an agent
submission. These two therefore establish that the task cannot be completed without the
media; on their own they say nothing about whether the schema is guessable.

**`no-media-forced` was added to probe exactly that** and only partly succeeds. Its prompt
appends an ablation clause requiring a best-effort file regardless of missing media --
which makes the anti-shortcut test stricter, not easier. The agent complied by writing the
file, then chose to submit an empty rally list: "It contains an empty rally list because no
media was provided and unobserved events cannot be inferred." So it answers "will it guess
when forced to submit?" (no) rather than "would guessing score?".

**`frame-dump` is the load-bearing one.** That agent did not refuse. It worked for 44
turns, built its own contact-sheet tooling, submitted a real schema-valid answer, and
recovered rally boundaries reasonably well -- 89 rallies against a reference of 92. It
still scored 0.0, because it submitted 89 strokes against a reference of 387: it found
where rallies were but could not reconstruct the stroke chain inside them, and `reward` is
a product across four terms. This is stronger evidence than any forced-guess run: a
capable agent, given every frame, answering in earnest, scores zero.

The schema is not guessable in the abstract either: scoring requires matching 92 rallies
and 387 strokes within timing tolerances across four multiplied terms.

### `frame-dump`: what was actually run, and how it differs from the family definition

The family spec defines `frame_dump_no_tools` as "all frames pasted, no tool use". What
ran here was:

> frames pre-extracted at 1 fps into `materials/` (1435 PNGs), `ffmpeg`/`ffprobe`/`ffplay`
> removed from the container, shell and Python retained.

Two deviations, both deliberate and both stated rather than papered over:

1. **The agent kept a shell.** Codex CLI's only tool *is* the shell. Running it under
   `--sandbox read-only` -- the obvious way to express "no tool use" -- makes `/workspace`
   unwritable, so the agent cannot write `output/solution.json` at all. Verified directly:
   `codex sandbox -c sandbox_mode="read-only"` fails a write to `/workspace/output` with
   "Read-only file system". That would score 0.0 by construction and prove nothing. The
   merged tasks that ran this ablation faithfully used Claude Code, whose file-write tool
   is separate from Bash, so it can lose the shell and still submit.
2. **Removing `ffmpeg` did not remove the agent's ability to inspect frames.** It wrote
   `make_sheet.py` and assembled contact sheets with Python imaging instead.

So this run's restriction is *weaker* than the family definition, not stronger: the agent
had more capability than the spec allows, and still scored 0.0. The anti-shortcut
conclusion is therefore conservative. Whether this substitution is acceptable in place of
a faithful `frame_dump_no_tools` run is a maintainer call.

### Ablation audit

Every ablation was scanned with the same rules as the calibration runs: search/browse tool
invocations across all three vendor spellings, dataset and annotation markers, and
credential material. All four are clean on all three, with zero hits. `net_guard` passed
both before and after each run (8 passes total), each on a dedicated egress gate
(`avb-netgate-abl`) held separate from the calibration run's gate so that one run's
install phase could never widen the other's allowlist during scoring.

### Claude Code trajectories

Both sessions of the reported run are committed, so the whole 123-turn count is
auditable in-repo without leaving the PR.

| segment | session_id | turns | transcript | bytes |
|---|---|---:|---|---:|
| 1 (2026-08-30 23:20Z) | `40ddfba8…` | 86 | `rollouts/claude_claude-opus-4-8.jsonl` | 26,061,905 |
| 2 (2026-08-31 04:03Z) | `40ddfba8…` | 37 | `rollouts/claude_claude-opus-4-8.seg2.jsonl` | 14,568,640 |

Both are complete raw `stream-json` transcripts, byte-for-byte as the harness wrote
them -- not excerpts, and not stripped of the base64 frame captures that make up most
of their size. Scanned before commit with base64 blocks removed: no API keys, OAuth
tokens, environment-variable assignments, host paths, dataset-source markers, or
search-tool invocations.

## Isolation, and what "no internet" means here

Every scored run executed **inside the frozen task image**, on a container that never had
the repository mounted. `runpack/stage_workspace.sh` provides only `game.mp4` and
`instruction.md`, and scans the whole filesystem to prove no reference, judge, or
annotation file is reachable.

Network egress is default-DROP with an allowlist, held in a sidecar network namespace the
run container joins (`runpack/netgate.sh`). `runpack/net_guard.sh` re-proves the policy
from inside that namespace **before and after every run** and logs the result.

| run | pre | post |
|---|---|---|
| Codex | PASSED | PASSED |
| Antigravity | PASSED | PASSED |
| Claude Code segment 1 | PASSED | PASSED |
| Claude Code segment 2 | PASSED | PASSED |

Blocked and verified per run: `github.com`, `raw.githubusercontent.com`, `lab.osai.ai`,
`www.google.com`.

**This differs from a literal `allow_internet = false` trial, and the difference is
deliberate.** Harbor's installed-agent adapters execute the CLI *inside* the container and
inject provider credentials as environment variables (`harbor/agents/installed/base.py`);
there is no host-side model proxy. A strictly no-network container therefore cannot
complete any agent run at all. What is enforced here is: **task and ground-truth data
paths blocked; model transport open.** Reaching the model endpoint is inference, not
lookup. `task.toml` still declares `allow_internet = false`, which Harbor 0.22.0 maps to
`network_mode = "no-network"`; that field is deprecated in 0.22.0 and is left untouched so
the frozen task contract is not modified for calibration convenience.

Resource budget is enforced from `task.toml` rather than left unlimited: the scored
container runs with `--memory=8192m --memory-swap=8192m --cpus=4`, verified from inside
the container's cgroup (`memory.max = 8192 MiB`, `cpu.max = 4.0`). Peak usage, read from
each container's `memory.peak` after its run: Codex **8034 MiB of 8192** (98%, thin but
`oom_kill = 0` and `OOMKilled=false`), Claude Code **3184 MiB**, Antigravity **4377 MiB**.
No scored run was OOM-killed.

## Lookup audit

`runpack/audit_and_grade.sh` scans each trajectory for dataset, annotation, answer-key and
search-tool markers, with base64 image blocks stripped first so that random base64 cannot
match a short marker by chance. All three reported runs are clean:

| marker | Codex | Antigravity | Claude Code |
|---|---:|---:|---:|
| `moamal01` / `table_tennis_data` / `game_2.json` / `openttgames` | 0 | 0 | 0 |
| `lab.osai.ai` / `raw.githubusercontent` | 0 | 0 | 0 |
| `reference.json` / `judge.py` / `/tests/` | 0 | 0 | 0 |
| search-tool invocations | 0 | 0 | 0 |
| Google grounding redirects | 0 | 0 | 0 |

**The scanner matches invocations, not mentions, and covers every harness's spelling.**

This matters. An **early, discarded** Antigravity attempt used the CLI's `search_web` tool
11 times and was handed `https://github.com/moamal01/table_tennis_data` through 8 Vertex AI
grounding redirects — it had located the ground-truth repository by name and was searching
it for `game_2.json`. **That attempt was terminated, never graded, and is reported nowhere
in this file as a score.** It is retained locally under `rollouts/aborted/` as evidence and
is not the run in the table above. The accepted Antigravity result is a separate,
later run on `gemini-3.1-pro-high` whose scan is clean on every marker.

`search_web` executes server-side at Google, so a container network policy cannot observe
or block it. In the CLI version used here (Antigravity CLI 1.1.22) no reliable per-tool
disable was found: the documented settings surface exposes `toolPermission`,
`enableTerminalSandbox` and `allowNonWorkspaceAccess`, none of which removes the tool, and
the CLI offers no `--disallowed-tools` equivalent. A newer version or an undocumented
setting may well provide one. Two controls are therefore in place:

1. a harness-level rules file (`runpack/AGENTS.md`, staged as `AGENTS.md` / `GEMINI.md` /
   `CLAUDE.md`, following the merged `lacrosse-mich-jhu-2024` precedent) forbidding any
   network tool and any attempt to identify the video's source;
2. a watchdog (`runpack/watchdog.sh`) that voids the run immediately if the native
   transcript shows a search invocation or a grounding redirect.

With the rules file in place, the same model on the same task went from 11 search calls to
**zero**. All three reported runs above ran under it.

Codex additionally ran with `--config tools.web_search=false`.

## Reachable ceiling

Rally 8 contains a documented video-gap exclusion: a second point is played inside the same
serve-defined window, but its serve's racket-ball contact is not resolvable in the source
video, so that segment is excluded from the reference (see
`calibration/source-exception-audit.md`). The segment is otherwise visible, so an agent may
report it.

Measured against the frozen verifier, a submission identical to the reference **plus** that
segment reported as a rally scores **0.962008** (rally-discovery F1 0.994595, stroke-timing
F1 0.983482 on 400 predicted vs 387 reference strokes, ending accuracy 1.0). This is a
deterministic property of the reference, not an agent measurement. Whether agents actually
report the segment is visible per run above; neither accepted run got close enough for it
to matter.

## Reproducing

`runpack/` contains the full harness: `netgate.sh` (egress gate), `net_guard.sh` (per-run
proof), `stage_workspace.sh` (harness-specific credential staging), `run_codex.sh` /
`run_claude.sh` / `run_antigravity.sh`, `resume_claude.sh`, `run_ablation.sh`,
`audit_and_grade.sh`, `liveness.sh`, `error_signature.sh`, `watchdog.sh`. See
`runpack/README.md`.

`resume_claude.sh` is the one worth reading closely, because it produced segment 2 of the
reported Claude row. It runs `claude --continue` in the same container against the same
workspace, and its continuation prompt is a single neutral sentence -- "Continue the task
from where you stopped. Write the final answer to /workspace/output/solution.json." -- with
no restatement of the task and no hint about approach. It deliberately never calls
`netgate.sh up` (that subcommand recreates the gate container, which would permanently
break the run container's borrowed network namespace) and never re-stages the workspace
(which would delete the intermediate files the resume exists to build on).

## Calibration notes

- **Earlier Claude attempts** terminated before producing a score and are excluded from
  every reported metric. They are retained locally under `rollouts/aborted/` as debugging
  evidence only. One of them writes a file with the same basename as the reported run's
  first segment, which is why segments here are matched by `session_id`.
- **Antigravity rules parity** — Antigravity used the pre-finalization shared rules
  rather than the finalized minimal rules (sha256 `779eec27…`) that the Codex and Claude
  Code rows used. The measured result is reported as-is; a strict-parity rerun can be
  provided if requested.
- **Peak memory** — the reported Codex run peaked at 8034 MiB against the task's 8192 MiB
  budget (98%), with `oom_kill = 0` and `OOMKilled=false`. Most of that is reclaimable page
  cache from decoding an 11 GB source, but the margin is thin enough to record.
- **Staging note for the Antigravity run** — it was started under an earlier staging step
  that cleared the pre-warmed page cache with a VM-global `drop_caches`. The runner now
  verifies the media SHA in a short-lived out-of-band container and symlinks it into the
  scored container instead, which leaves the scored cgroup cold without touching the VM
  (`memory.current` 2 MiB, `file` cache 0 MiB at stage time). The two staging paths leave
  the scored container in the same state; the run is reported as accepted, with this noted
  for the reviewer to judge whether a canonical rerun is wanted.
