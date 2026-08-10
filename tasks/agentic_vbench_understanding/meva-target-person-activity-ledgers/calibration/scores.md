# Calibration

The frozen verifier scores 29 activity assignments for ten video-local roster
targets.

## Anchors

| harness | version | run | score | trajectory |
|---|---|---|---:|---|
| Harbor | 0.6.6 | exact oracle | 1.000000 | job `meva-oracle-artifact-fixed` |
| Harbor | 0.6.6 | empty submission | 0.000000 | job `meva-empty-final` |

## Strong-agent attempts

The required native CLIs are installed, but no authenticated native account is
available in this environment. `harness_status.json` records the exact blockers.
The auditable fallback runs below use GitHub Copilot CLI without relabeling them
as native trajectories.

Each fallback run uses a fresh task container, four CPUs, 8 GB memory, disabled
public internet, an allowlisted Copilot API proxy, and a complete raw trajectory.

| harness | version | model | reasoning | score | tool calls | assistant turns | trajectory |
|---|---|---|---|---:|---:|---:|---|
| GitHub Copilot CLI | 1.0.79-9 | GPT-5.6 Sol | xhigh | 0.000494 | 166 | 62 | `rollouts/gpt-5.6-sol_copilot.jsonl` |
| GitHub Copilot CLI | 1.0.79-9 | Claude Opus 4.8 | xhigh | 0.003116 | 87 | 49 | `rollouts/claude-opus-4.8_copilot.jsonl` |
| GitHub Copilot CLI | 1.0.79-9 | Gemini 3.5 Flash | high | 0.000000 | 50 | 51 | `rollouts/gemini-3.5-flash_copilot.jsonl` |

Gemini created a pure-Python image matcher whose ffmpeg subprocess deadlocked
because stderr was piped but never consumed. It produced no solution and was
terminated after 52 minutes of inactivity. The raw failed trajectory, proxy log,
and machine-readable termination record are retained.

## Required degraded-input runs

| ablation | model / harness | score | trajectory |
|---|---|---:|---|
| no media | GPT-5.6 Sol / GitHub Copilot CLI 1.0.79-9 | 0.000000 | `rollouts/ablation-no-media.jsonl` |
| single frame | GPT-5.6 Sol / GitHub Copilot CLI 1.0.79-9 | 0.000000 | `rollouts/ablation-single-frame.jsonl` |
| one-frame-per-second dump, no inspection tools | GPT-5.6 Sol / GitHub Copilot CLI 1.0.79-9 | 0.000000 | `rollouts/ablation-frame-dump-no-tools.jsonl` |

## Deterministic identity shortcuts

| submission | score |
|---|---:|
| all gold-timed events assigned to one target | 0.003344 |
| all gold-timed events copied to every target | 0.032963 |
| correct target activity types at wrong times | 0.000116 |
| all events shifted by five seconds | 0.000470 |

Per-run rewards, solutions, proxy audits, hashes, and command receipts are
persisted in the managed result package. This contribution keeps only the raw
trajectories and this score table, following the family artifact policy.
