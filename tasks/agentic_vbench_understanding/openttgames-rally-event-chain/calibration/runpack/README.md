# Calibration runpack

Reproducible harness for the calibration numbers in `../scores.md`. Every scored
run happens **inside the frozen task image** so the agent sees exactly the shipped
libraries, and inside a restricted network namespace so the ground-truth source is
provably unreachable.

## Why this shape

The ground truth is derived from a public GitHub repository, so "the agent did not
look it up" has to be enforced, not asserted. Three independent layers do that:

1. **Container** — the run container is built from the frozen image and never has
   the repo mounted. `stage_workspace.sh` copies in only `game.mp4` and
   `instruction.md`, re-verifies the media against the pinned SHA-256, and scans
   the whole filesystem to prove no reference, judge, or annotation file exists.
2. **Network** — `netgate.sh` holds a network namespace whose OUTPUT policy is
   DROP, with an allowlist of the endpoints a run genuinely needs. Run containers
   join that namespace with `--network container:avb-netgate`, so they inherit the
   policy without the frozen image being modified and without relying on any CLI
   honouring proxy environment variables. `net_guard.sh` re-proves the blocks from
   inside the namespace before and after every run and logs the result.

   The allowlist is deliberate. A denylist keyed on resolved IPs cannot be
   complete: GitHub and the dataset host answer with different addresses on
   different lookups, so a host blocked at setup silently becomes reachable later.
   That was observed while building this runpack. Default-DROP inverts the failure
   mode — a rotated address breaks the run, which is visible, rather than exposing
   the ground truth, which is not.

   The gate runs in two phases. `up` additionally allows the Debian and npm hosts
   needed to install a CLI into the run container; `lock` drops back to the model
   endpoints alone and is called by every runner after install and before the
   scored run begins.
3. **Harness** — each CLI is additionally run with its own network and web-search
   restrictions (`--sandbox workspace-write` and `tools.web_search=false` for Codex,
   `--disallowedTools WebFetch,WebSearch` for Claude Code).

The model endpoint stays reachable: the agent harness cannot run without it. That
is inference, not lookup, and `audit_and_grade.sh` enforces the distinction on the
trajectory. Note that Gemini's Search grounding happens server-side and no network
policy can block it, which is why the trajectory scan and the telltale check exist.

Agent CLIs are installed into the *run* container at calibration time. They are
deliberately absent from the shipped image so that no harness is privileged.

## Use

```bash
./netgate.sh up
./calibrate.sh codex
./audit_and_grade.sh codex ../rollouts/codex_gpt-5.6-sol.jsonl

./calibrate.sh claude opus-4.8
./calibrate.sh antigravity gemini-3.5-flash

./run_ablation.sh single-frame
./run_ablation.sh no-media
./run_ablation.sh frame-dump

./netgate.sh down
```

Requires `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` in the environment.

## Gates

| check | threshold |
|---|---|
| each agent reward | < 0.10 |
| tool-call turns | > 50 |
| each ablation reward | <= 0.15 |
| oracle / empty | 1.0 / 0.0 |
