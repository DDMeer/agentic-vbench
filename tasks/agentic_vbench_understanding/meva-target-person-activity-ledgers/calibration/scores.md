# Calibration

The frozen verifier scores 29 activity assignments for ten video-local roster
targets.

## Submission status

All three required rows clear the measured difficulty gate. The maintainer
approved the VS Code Claude Agent SDK session as equivalent to Claude Code for
this contribution. The Antigravity score uses an adjudicated schema-only repair:
the repair changed three key names and no references, activities, or times.

## Anchors

| harness | version | run | score |
|---|---|---|---:|
| Harbor | 0.6.6 | exact oracle | 1.000000 |
| Harbor | 0.6.6 | empty submission | 0.000000 |

## Required agent calibration

| harness | harness version | model | reasoning | score | tool-call turns | trajectory |
|---|---|---|---|---:|---:|---|
| Codex CLI | 0.147.0 | GPT-5.6 Sol | high | 0.009443 | 80 | `rollouts/codex-gpt-5.6-sol.jsonl` |
| VS Code Claude Agent SDK | Copilot Chat 0.60.0 | Claude Opus 4.8 | high | 0.004100 | 115 parent; 554 including nested agents | `rollouts/claude-opus-4.8-vscode-agent-sdk.jsonl` |
| Antigravity CLI | 1.1.12 | Gemini 3.6 Flash High | high | 0.003459 | 220 | `rollouts/antigravity-gemini-3.6-flash-high.jsonl` |

The Codex run used the frozen task image with four CPUs, 8 GB memory, blocked
model-issued shell egress, no prior history, and a complete native JSONL
trajectory. Its solution contained nine assignments and the verifier returned
`reason: ok`.

The Claude run used a fresh folder-isolated session with no prior history. The
raw AHP stream records the exact `claude-opus-4.8` model and high thinking level,
115 parent tool calls, ten nested agent channels, and 439 nested tool calls. All
ten nested turns completed. Audit of parent and nested inputs found no verifier,
ground-truth, sibling-row, or public-network access.

The Antigravity run used GCP Agent Platform ADC billing and the frozen task image
with four CPUs, 8 GB memory, blocked model-issued shell egress, hidden ADC
credentials, no prior Antigravity history, and a complete native JSONL
trajectory. The primary trajectory ended `SUCCESS` after 220 tool calls. Its
populated output used `ledger`, `start_time`, and `end_time` instead of the three
required schema keys. A narrowly scoped follow-up changed only those key names;
canonical JSON comparison proved all semantic values unchanged, and the verifier
then returned `reason: ok` with score `0.003459`. Both supplemental trajectories
ended with a post-response sandbox transport error and remain flagged for manual
review in the managed result package.

## Required degraded-input runs

| ablation | model / harness | score | trajectory |
|---|---|---:|---|
| no media | GPT-5.6 Sol / GitHub Copilot CLI 1.0.79-9 | 0.000000 | `rollouts/ablation-no-media.jsonl` |
| single frame | GPT-5.6 Sol / GitHub Copilot CLI 1.0.79-9 | 0.000000 | `rollouts/ablation-single-frame.jsonl` |
| one-frame-per-second dump, no inspection tools | GPT-5.6 Sol / GitHub Copilot CLI 1.0.79-9 | 0.001106 | `rollouts/ablation-frame-dump-no-tools.jsonl` |

## Deterministic identity shortcuts

| submission | score |
|---|---:|
| all gold-timed events assigned to one target | 0.003344 |
| all gold-timed events copied to every target | 0.032963 |
| correct target activity types at wrong times | 0.000116 |
| all events shifted by five seconds | 0.000470 |

Per-run rewards, solutions, audits, hashes, commands, and failed attempts remain
in the managed result package outside the contribution. The PR tree keeps one
complete raw trajectory per accepted required harness plus the measured
degraded-input trajectories.
