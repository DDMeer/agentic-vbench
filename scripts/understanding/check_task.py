#!/usr/bin/env python3
"""Pre-submission checker for AgenticVBench video-understanding tasks.

Validates the three things every task in this area must satisfy:

  1. INPUT VIDEO   reachable + downloadable, length 10-300 min, height >= 720p.
  2. ROLLOUT       a strong agent's run took > 50 tool-call turns (long-horizon).
  3. CALIBRATION   oracle reward == 1.0, null/empty baseline <= 0.10, strong
                   agent reward < 0.50.

Each check runs only if you give it the inputs; skipped checks are reported. Exit
status is non-zero if any provided check FAILS, so it drops into CI.

Examples
--------
  # video only (needs ffprobe on PATH; yt-dlp for YouTube links)
  python tools/check_task.py --video-url "https://archive.org/download/.../game.mp4"

  # full check after a run
  python tools/check_task.py \
      --task-dir tasks/agentic_vbench_sports/gsw-cle-2018-finals-g4-boxscore \
      --video-url "https://..." \
      --oracle-reward jobs/<job>/reward.json \
      --baseline-reward jobs/<empty>/reward.json \
      --agent-reward jobs/<agent>/reward.json \
      --agent-turns 73
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

MIN_MINUTES = 10
MAX_MINUTES = 300
MIN_HEIGHT = 720
ORACLE_MIN = 0.999          # oracle must score 1.0
BASELINE_MAX = 0.10         # null/empty baseline must be ~0
AGENT_MAX = 0.10            # a strong agent must stay below this (hard task)
MIN_TURNS = 50              # rollout must be long-horizon

REQUIRED_FILES = [
    "task.toml",
    "environment/Dockerfile",
    "steps/solve/instruction.md",
    "steps/solve/solution/solve.sh",
    "steps/solve/tests/judge.py",
    "steps/solve/tests/test.sh",
]

results = []  # (name, status, message); status in {"PASS","FAIL","SKIP","WARN"}


def record(name, status, message):
    results.append((name, status, message))


def read_reward(path):
    return float(json.loads(Path(path).read_text())["reward"])


def probe_archive_or_direct(url):
    """Return (duration_s, height) via ffprobe, or raise."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "format=duration:stream=height",
         "-of", "json", url],
        capture_output=True, text=True, timeout=120,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or "ffprobe failed")
    data = json.loads(out.stdout)
    dur = float(data["format"]["duration"])
    height = max(int(s.get("height", 0)) for s in data.get("streams", [{}]))
    return dur, height


def probe_youtube(url):
    out = subprocess.run(
        ["yt-dlp", "-J", "--no-warnings", url],
        capture_output=True, text=True, timeout=120,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or "yt-dlp failed")
    data = json.loads(out.stdout)
    dur = float(data.get("duration") or 0)
    heights = [int(f["height"]) for f in data.get("formats", []) if f.get("height")]
    return dur, (max(heights) if heights else 0)


def check_video(url):
    is_yt = "youtube.com" in url or "youtu.be" in url
    tool = "yt-dlp" if is_yt else "ffprobe"
    if shutil.which(tool) is None:
        record("input video", "WARN", f"{tool} not on PATH; cannot probe {url}")
        return
    try:
        dur, height = probe_youtube(url) if is_yt else probe_archive_or_direct(url)
    except Exception as exc:  # noqa: BLE001
        record("input video", "FAIL", f"not reachable / not probeable: {exc}")
        return
    mins = dur / 60.0
    ok_len = MIN_MINUTES <= mins <= MAX_MINUTES
    ok_res = height >= MIN_HEIGHT
    status = "PASS" if (ok_len and ok_res) else "FAIL"
    record("input video", status,
           f"{mins:.1f} min (need {MIN_MINUTES}-{MAX_MINUTES}), "
           f"{height}p (need >= {MIN_HEIGHT}p)")


def check_structure(task_dir):
    missing = [f for f in REQUIRED_FILES if not (Path(task_dir) / f).is_file()]
    if missing:
        record("task structure", "FAIL", "missing: " + ", ".join(missing))
    else:
        record("task structure", "PASS", "all required files present")


def check_calibration(oracle, baseline, agent):
    if oracle is not None:
        try:
            r = read_reward(oracle)
            record("oracle == 1.0", "PASS" if r >= ORACLE_MIN else "FAIL", f"reward = {r}")
        except Exception as exc:  # noqa: BLE001
            record("oracle == 1.0", "FAIL", f"unreadable: {exc}")
    if baseline is not None:
        try:
            r = read_reward(baseline)
            record("baseline ~ 0", "PASS" if r <= BASELINE_MAX else "FAIL",
                   f"reward = {r} (need <= {BASELINE_MAX})")
        except Exception as exc:  # noqa: BLE001
            record("baseline ~ 0", "FAIL", f"unreadable: {exc}")
    if agent is not None:
        try:
            r = read_reward(agent)
            record(f"strong agent < {AGENT_MAX}", "PASS" if r < AGENT_MAX else "FAIL",
                   f"reward = {r} (need < {AGENT_MAX})")
        except Exception as exc:  # noqa: BLE001
            record("strong agent < 0.5", "FAIL", f"unreadable: {exc}")


def check_rollout(turns):
    if turns is None:
        return
    record("rollout > 50 turns", "PASS" if turns > MIN_TURNS else "FAIL",
           f"{turns} tool-call turns (need > {MIN_TURNS})")


# Anti-shortcut ablations: a strong model run under each degraded input must score
# near the null baseline. If it scores well, the task has a shortcut (one frame, one
# modality, recall, or a guessable schema carries the answer).
ABLATION_MAX = 0.15
ABLATIONS = {
    "single_frame": "one representative frame only",
    "video_only": "video with audio stripped",
    "audio_only": "audio only",
    "no_media": "prompt + schema, no media (recall/guess check)",
    "frame_dump_no_tools": "all frames pasted, no tool use (agency check)",
}


def check_ablations(paths):
    for key, desc in ABLATIONS.items():
        path = paths.get(key)
        if path is None:
            continue
        name = f"ablation {key} ~ 0"
        try:
            r = read_reward(path)
            record(name, "PASS" if r <= ABLATION_MAX else "FAIL",
                   f"reward = {r} (need <= {ABLATION_MAX}; {desc})")
        except Exception as exc:  # noqa: BLE001
            record(name, "FAIL", f"unreadable: {exc}")


def main():
    ap = argparse.ArgumentParser(description="Check a video-understanding task.")
    ap.add_argument("--task-dir", help="task directory to structure-check")
    ap.add_argument("--video-url", help="archive.org/direct mp4 or YouTube URL")
    ap.add_argument("--oracle-reward", help="reward.json from `--agent oracle`")
    ap.add_argument("--baseline-reward", help="reward.json from an empty submission")
    ap.add_argument("--agent-reward", help="reward.json from a strong agent run")
    ap.add_argument("--agent-turns", type=int,
                    help="tool-call turns from the strong agent's trajectory")
    for key, desc in ABLATIONS.items():
        ap.add_argument(f"--ablation-{key.replace('_', '-')}", dest=f"ablation_{key}",
                        help=f"reward.json from the '{desc}' ablation run")
    args = ap.parse_args()

    ablation_paths = {k: getattr(args, f"ablation_{k}") for k in ABLATIONS}
    if not any([args.task_dir, args.video_url, args.oracle_reward,
                args.baseline_reward, args.agent_reward, args.agent_turns,
                *ablation_paths.values()]):
        ap.error("give at least one thing to check (see --help)")

    if args.task_dir:
        check_structure(args.task_dir)
    if args.video_url:
        check_video(args.video_url)
    check_calibration(args.oracle_reward, args.baseline_reward, args.agent_reward)
    check_rollout(args.agent_turns)
    check_ablations(ablation_paths)

    width = max(len(n) for n, _, _ in results)
    print()
    for name, status, message in results:
        print(f"  [{status:4}] {name.ljust(width)}  {message}")
    failed = [n for n, s, _ in results if s == "FAIL"]
    skipped = [n for n, s, _ in results if s in ("SKIP", "WARN")]
    print()
    if failed:
        print(f"FAILED: {len(failed)} check(s): {', '.join(failed)}")
        sys.exit(1)
    print("All provided checks passed." + (f" ({len(skipped)} warned/skipped)" if skipped else ""))


if __name__ == "__main__":
    main()
