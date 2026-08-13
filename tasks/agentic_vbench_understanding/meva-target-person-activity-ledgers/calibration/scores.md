# Calibration

The frozen verifier scores 29 activity assignments for ten video-local roster
targets.

## Submission status

All three required rows clear the measured difficulty gate.

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

The PR tree keeps one complete trajectory per required harness plus the measured
degraded-input trajectories.
