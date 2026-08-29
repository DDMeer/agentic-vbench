#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FPS = 120.0

ENDING_SUFFIXES = (
    "_out",
    "_winner",
    "_double_bounce",
    "_not_hitting_ball",
    "_miss_on_own_side",
)

STROKE_TYPES = (
    "_serve",
    "_loop",
    "_block",
    "_push",
    "_flick",
    "_lob",
    "_smash",
    "_chop",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def frame_to_time(frame: int) -> float:
    return round(frame / FPS, 3)


def is_stroke(label: str) -> bool:
    first = label.split()[0]
    return any(x in first for x in STROKE_TYPES)


def is_serve(label: str) -> bool:
    return is_stroke(label) and "_serve" in label.split()[0]


def is_ending(label: str) -> bool:
    if label in ("left_net", "right_net"):
        return True
    return any(label.endswith(x) for x in ENDING_SUFFIXES)


def parse_stroke(frame: int, label: str) -> dict:
    first = label.split()[0]
    parts = first.split("_")

    player = parts[0]
    hand = parts[1]
    stroke = "_".join(parts[2:])

    return {
        "frame": frame,
        "time_sec": frame_to_time(frame),
        "player": player,
        "hand": hand,
        "stroke": stroke,
    }


def dedup_endings(
    endings: list[tuple[int, str]],
    max_gap: int = 2,
) -> list[tuple[int, str]]:
    if not endings:
        return []

    result = [endings[0]]

    for frame, label in endings[1:]:
        prev_frame, prev_label = result[-1]

        if label == prev_label and frame - prev_frame <= max_gap:
            continue

        result.append((frame, label))

    return result


def build_reference(input_path: Path) -> tuple[dict, dict]:
    with input_path.open() as f:
        raw = json.load(f)

    data = {int(k): v for k, v in raw.items()}
    events = sorted(data.items())

    serves = [(f, l) for f, l in events if is_serve(l)]

    valid = []
    excluded = []

    for i, (serve_frame, _) in enumerate(serves):
        next_serve = (
            serves[i + 1][0]
            if i + 1 < len(serves)
            else float("inf")
        )

        window = [
            (f, l)
            for f, l in events
            if serve_frame <= f < next_serve
        ]

        strokes = [
            parse_stroke(f, l)
            for f, l in window
            if is_stroke(l)
        ]

        endings_raw = [
            (f, l)
            for f, l in window
            if is_ending(l)
        ]

        endings = dedup_endings(endings_raw)

        if len(endings) != 1:
            excluded.append({
                "rally_id": i + 1,
                "serve_frame": serve_frame,
                "serve_time_sec": frame_to_time(serve_frame),
                "reason": f"{len(endings)} endings after dedup",
                "raw_endings": endings_raw,
            })
            continue

        ending_frame, ending_label = endings[0]

        valid.append({
            "rally_id": i + 1,
            "serve_frame": serve_frame,
            "serve_time_sec": frame_to_time(serve_frame),
            "server": strokes[0]["player"],
            "strokes": strokes,
            "ending_frame": ending_frame,
            "ending_time_sec": frame_to_time(ending_frame),
            "ending": ending_label,
        })

    reference = {
        "source": "Extended OpenTTGames annotations",
        "video": {
            "filename": "game_2.mp4",
            "fps": FPS,
            "width": 1920,
            "height": 1080,
            "duration_sec": 1435.0,
            "frame_count": 172200,
        },
        "valid_rallies": len(valid),
        "excluded_rallies": len(excluded),
        "rallies": valid,
        "excluded": excluded,
    }

    audit = {
        "annotation_sha256": sha256_file(input_path),
        "total_annotation_events": len(events),
        "total_serves": len(serves),
        "valid_rallies": len(valid),
        "excluded_rallies": len(excluded),
        "excluded_rally_ids": [
            item["rally_id"] for item in excluded
        ],
        "benchmark_strokes": sum(
            len(rally["strokes"]) for rally in valid
        ),
        "dedup_rule": {
            "type": "adjacent identical ending labels",
            "max_gap_frames": 2,
        },
        "valid_rally_rule": (
            "exactly one ending after dedup within each "
            "serve-defined rally window"
        ),
    }

    return reference, audit


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--audit",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    reference, audit = build_reference(args.input)

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.audit.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(reference, indent=2) + "\n"
    )

    args.audit.write_text(
        json.dumps(audit, indent=2) + "\n"
    )

    print("Wrote reference:", args.output)
    print("Wrote audit:", args.audit)


if __name__ == "__main__":
    main()
