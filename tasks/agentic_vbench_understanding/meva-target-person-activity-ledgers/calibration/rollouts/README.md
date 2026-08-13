# Raw trajectories

Required-agent trajectories:

- `codex-gpt-5.6-sol.jsonl`: complete native Codex CLI JSONL.
- `claude-opus-4.8-vscode-agent-sdk.jsonl`: complete VS Code Claude Agent SDK
  AHP stream for the successful parent turn and all ten nested agent channels.
- `antigravity-gemini-3.6-flash-high.jsonl`: complete native Antigravity CLI
  `stream-json` trajectory.

The remaining JSONL files are measured degraded-input trajectories. These files
are raw auditable streams, not summaries or reconstructed transcripts.
Personal home paths and task-specific calibration workspace roots are
deterministically redacted. Redaction replaces path strings only; no events,
tool inputs, tool results, or model messages are removed.
