# Calibration

The frozen verifier scores 29 activity assignments for ten video-local roster
targets.

## Anchors

| harness | version | run | score |
|---|---|---|---:|
| Harbor | 0.6.6 | exact oracle | 1.000000 |
| Harbor | 0.6.6 | empty submission | 0.000000 |

## Fixed-harness model comparison

Calibration uses GitHub Copilot CLI as one consistent harness while changing the
underlying model. Each run uses a fresh task container, four CPUs, 8 GB memory,
disabled public internet, an allowlisted Copilot API proxy, and a complete raw
trajectory.

This contributor-selected methodology differs from the current family README's
native Antigravity, Codex CLI, and Claude Code routing. Any future PR must request
explicit maintainer acceptance of the fixed-harness comparison.

| harness | version | model | reasoning | score | tool calls | assistant turns | trajectory |
|---|---|---|---|---:|---:|---:|---|
| GitHub Copilot CLI | 1.0.79-9 | Claude Opus 4.8 | xhigh | 0.000000 | 39 | 28 | `rollouts/claude-opus-4.8_copilot.jsonl` |
| GitHub Copilot CLI | 1.0.79-9 | Claude Sonnet 5 | xhigh | 0.000000 | 70 | 59 | `rollouts/claude-sonnet-5_copilot.jsonl` |
| GitHub Copilot CLI | 1.0.79-9 | Gemini 3.1 Pro Preview | high | 0.000000 | 65 | 65 | `rollouts/gemini-3.1-pro-preview_copilot.jsonl` |

Gemini's provider accepts at most ten images. Its run used a provider-only
runtime constraint limiting the run to nine image views. Opus and Sonnet used
a 30-minute runtime constraint requiring a best-effort submission by 20
minutes. These constraints contain no answer information.

Failed GPT and initial Gemini attempts are preserved in the managed result
ledger but excluded from the successful comparison table. Their exact failure
reasons are summarized in `harness_status.json`.

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

Per-run rewards, solutions, proxy audits, hashes, commands, and failed attempts
are persisted in the managed result package. The contribution keeps one raw
trajectory per successful model plus the required degraded-input trajectories.
