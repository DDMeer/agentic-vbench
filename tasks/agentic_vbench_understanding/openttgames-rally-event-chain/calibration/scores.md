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
| Codex CLI | 0.147.0 | `gpt-5.6-sol` | high | **0.001858** | **53** | 40 min | `rollouts/codex_gpt-5.6-sol.jsonl` |
| Antigravity CLI | 1.1.22 | `gemini-3.1-pro-high` | high | **0.000000** | **164** | 42 min | `rollouts/antigravity_gemini-3.1-pro-high.native.jsonl` |
| Claude Code CLI | 2.1.251 | `claude-opus-4-8` | — | **pending** | **pending** | — | — |

**Not yet complete: Claude Code, and all three required ablations** (single-frame,
no-media, frame-dump). This task is therefore not yet fully calibrated.

Both completed runs clear the family gates: reward < 0.10 and more than 50 tool-call turns.

Only these two runs are reported as results. Earlier attempts that were truncated by
provider errors, resource limits, harness defects, or a contamination detection were
discarded, never graded, and are not represented in any number above; they are retained
locally under `rollouts/aborted/` and are available on request.

### Per-field diagnostics

| | Codex | Antigravity |
|---|---:|---:|
| rally-discovery F1 | 0.530387 | 0.020000 |
| stroke-timing F1 | 0.312860 | 0.009195 |
| stroke-semantic joint F1 | 0.067179 | 0.000000 |
| rally-ending joint accuracy | 0.166667 | 1.000000 |
| rallies predicted / matched (ref 92) | 89 / 48 | 8 / 1 |
| strokes predicted / matched (ref 387) | 655 / 163 | 48 / 2 |

Antigravity's ending accuracy of 1.0 is a one-of-one artefact: it matched a single rally
and happened to get that ending right. It does not survive the product, and the run
reconstructed 8 of 92 rallies.

### How tool-call turns were counted

Each harness records work differently, so each is counted with its own rule and the rule
is stated rather than assumed:

- **Codex CLI** — distinct `item.started` records of type `command_execution`: **53**.
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
the container's cgroup (`memory.max = 8192 MiB`, `cpu.max = 4.0`). Peak usage: Codex not
instrumented, Antigravity **4377 MiB of 8192**, `oom_kill = 0`.

## Lookup audit

`runpack/audit_and_grade.sh` scans each trajectory for dataset, annotation, answer-key and
search-tool markers. Both accepted runs are clean:

| marker | Codex | Antigravity |
|---|---:|---:|
| `moamal01` / `table_tennis_data` / `game_2.json` / `openttgames` | 0 | 0 |
| `lab.osai.ai` / `raw.githubusercontent` | 0 | 0 |
| `reference.json` / `judge.py` / `/tests/` | 0 | 0 |
| search-tool invocations | 0 | 0 |
| Google grounding redirects | 0 | 0 |

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
**zero**. Both accepted runs above ran under it.

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
proof), `stage_workspace.sh` (key-free staging), `run_codex.sh` / `run_claude.sh` /
`run_antigravity.sh`, `run_ablation.sh`, `audit_and_grade.sh`, `liveness.sh`,
`error_signature.sh`, `watchdog.sh`. See `runpack/README.md`.

## Open items

- **Claude Code** — not yet calibrated. Two attempts on `claude-opus-4-8` were truncated by
  API credit exhaustion, the second after $122.40 and 84 minutes having reconstructed 9 of
  92 rallies; a third halted immediately because Claude Code in `-p` mode requires an
  explicit permission mode. The harness issue is fixed (`--allowedTools`); the budget is not.
- **Ablations** — single-frame, no-media and frame-dump runs are not yet done.
  `video_only` / `audio_only` do not apply: this task declares audio as not required.
- **Staging note for the Antigravity run** — it was started under an earlier staging step
  that cleared the pre-warmed page cache with a VM-global `drop_caches`. The runner now
  verifies the media SHA in a short-lived out-of-band container and symlinks it into the
  scored container instead, which leaves the scored cgroup cold without touching the VM
  (`memory.current` 2 MiB, `file` cache 0 MiB at stage time). The two staging paths leave
  the scored container in the same state; the run is reported as accepted, with this noted
  for the reviewer to judge whether a canonical rerun is wanted.
