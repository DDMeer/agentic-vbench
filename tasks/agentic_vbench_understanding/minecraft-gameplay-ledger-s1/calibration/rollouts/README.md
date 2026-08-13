# Raw rollouts: one full trajectory per harness.

Each `codex_<render>_solution.json` is the agent's submitted ledger for that render and
`codex_<render>_reward.json` the judge's score. The shipped task is **v38 + timestamp**:
`codex_v38ts_solution.json` / `codex_v38ts_reward.json` (reward 0.0196, 103 of 1995 events).

**Calibration history on HF** (agent narration + this rollout, secret-free — encrypted reasoning,
tool I/O and all environment/credentials stripped at extraction and re-scanned for keys, 0 hits):

<https://huggingface.co/datasets/explcre/agenticvbench-understanding-materials/tree/main/minecraft-gameplay-ledger-s1/calibration>

Agent: Codex CLI `gpt-5.6-sol`, `model_reasoning_effort=xhigh`, run locally (ChatGPT login).
