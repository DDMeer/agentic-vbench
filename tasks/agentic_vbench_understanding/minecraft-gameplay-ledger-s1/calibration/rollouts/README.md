# Calibration trajectories — POL-1 raw archives

The **audit record** for each strong-agent row in `../scores.md` is the agent's **full raw session
transcript** — every tool call, tool output, turn, and frame kept intact. Only credentials and
home-directory prefixes were redacted (`sanitize_raw.py`: masks API keys / tokens / `Bearer` /
private keys / `/home/<user>`; re-scanned to 0 residual secrets). The archives are tens of MB of
base64 frames, so they are hosted immutably on HF (this repo has no git-LFS) and pinned by revision,
with whole-file SHA256 recorded here:

```
REV=4a1142050c59375a7a833d7253549eb6205a7119
base=https://huggingface.co/datasets/explcre/agenticvbench-understanding-materials/resolve/$REV/minecraft-gameplay-ledger-s1/calibration/raw
```
| row | raw archive (`$base/…`) | sha256 |
|---|---|---|
| Codex CLI · gpt-5.6-sol (xhigh) | `mc_codex_gpt-5.6-sol_raw.jsonl` | `6b06c5b04a44ac61565a3631fa3ff767896ca3dc0b191cebbf375c61aedf7140` |
| Claude Code CLI · claude-opus-4-8 | `mc_claude_opus-4.8_raw.jsonl` | `12b7f002cca798f34a41ff41a1ceaaf6cccd4358cda75224101febbb06c682c7` |

The Gemini row's raw archive is on a later revision:
```
REV=ea7b9d908d6c4d834276ed85656fc00d63f65fb1
```
| row | raw archive (`.../resolve/$REV/minecraft-gameplay-ledger-s1/calibration/raw/…`) | sha256 |
|---|---|---|
| Gemini CLI · gemini-3.5-flash | `mc_gemini_3.5-flash_raw.jsonl` | `8543567791b77d7a7ad88b6cae6230381760ceee078f9cba405c023c6efd0d79` |

The reward/solution JSON dumps for each run are alongside at `.../calibration/` (same pinned revision).
