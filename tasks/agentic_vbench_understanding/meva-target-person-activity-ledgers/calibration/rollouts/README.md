# Raw trajectories

Required-agent trajectories:

- `codex-gpt-5.6-sol.jsonl`: complete native Codex CLI JSONL.
- `claude-opus-4.8-vscode-agent-sdk.jsonl`: complete VS Code Claude Agent SDK
  AHP stream for the successful parent turn and all ten nested agent channels.
  The maintainer approved this wrapper as Claude Code-equivalent for this task.
- `antigravity-gemini-3.6-flash-high.jsonl`: complete native Antigravity CLI
  `stream-json` trajectory. The primary run completed successfully with 220
  tool calls. Its populated output used three incorrect schema key names; the
  managed result package retains the original file and raw schema-only repair
  and validation trajectories. The repaired file changed no semantic values.

The remaining JSONL files are measured degraded-input trajectories. These files
are raw auditable streams, not summaries or reconstructed transcripts.
Personal home paths and task-specific calibration workspace roots are
deterministically redacted. Redaction replaces path strings only; no events,
tool inputs, tool results, or model messages are removed.
