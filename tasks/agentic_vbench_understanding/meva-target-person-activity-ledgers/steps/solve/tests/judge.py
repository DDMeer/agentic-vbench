#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REFERENCE_IDS = tuple(f"reference_{index:03d}" for index in range(1, 11))
ACTIVITY_TYPES = {
    "person_picks_up_object",
    "person_carries_heavy_object",
    "person_puts_down_object",
    "person_opens_vehicle_door",
    "person_enters_vehicle",
    "person_closes_vehicle_door",
}
MIDPOINT_TOLERANCE_S = 3.0
MEDIA_DURATION_S = 600.133333


@dataclass(frozen=True)
class Event:
    reference_id: str
    activity_type: str
    start_time_s: float
    end_time_s: float


def _parse(path: Path, strict: bool) -> list[Event]:
    value: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"ledgers"}:
        raise ValueError("top level must contain only ledgers")
    if not isinstance(value["ledgers"], list):
        raise ValueError("ledgers must be a list")

    seen_references: set[str] = set()
    events: list[Event] = []
    for ledger in value["ledgers"]:
        if not isinstance(ledger, dict) or set(ledger) != {
            "reference_id",
            "events",
        }:
            raise ValueError("each ledger must contain reference_id and events")
        reference_id = ledger["reference_id"]
        if reference_id not in REFERENCE_IDS:
            raise ValueError("unknown reference_id")
        if reference_id in seen_references:
            raise ValueError("duplicate reference_id")
        seen_references.add(reference_id)
        if not isinstance(ledger["events"], list):
            raise ValueError("events must be a list")
        for raw_event in ledger["events"]:
            if not isinstance(raw_event, dict) or set(raw_event) != {
                "activity_type",
                "start_time_s",
                "end_time_s",
            }:
                raise ValueError("invalid event schema")
            activity_type = raw_event["activity_type"]
            if activity_type not in ACTIVITY_TYPES:
                raise ValueError("unknown activity_type")
            if isinstance(raw_event["start_time_s"], bool) or isinstance(
                raw_event["end_time_s"], bool
            ):
                raise ValueError("times must be numeric")
            start = float(raw_event["start_time_s"])
            end = float(raw_event["end_time_s"])
            if (
                not math.isfinite(start)
                or not math.isfinite(end)
                or start < 0
                or start >= end
                or end > MEDIA_DURATION_S + 0.001
            ):
                raise ValueError("invalid event interval")
            events.append(
                Event(
                    reference_id=reference_id,
                    activity_type=activity_type,
                    start_time_s=start,
                    end_time_s=end,
                )
            )
    if strict and seen_references != set(REFERENCE_IDS):
        raise ValueError("ground truth must contain every reference")
    return events


def _temporal_weight(prediction: Event, gold: Event) -> float:
    prediction_duration = prediction.end_time_s - prediction.start_time_s
    gold_duration = gold.end_time_s - gold.start_time_s
    intersection = max(
        0.0,
        min(prediction.end_time_s, gold.end_time_s)
        - max(prediction.start_time_s, gold.start_time_s),
    )
    union = max(prediction.end_time_s, gold.end_time_s) - min(
        prediction.start_time_s, gold.start_time_s
    )
    iou = intersection / union if union else 0.0
    duration_ratio = min(prediction_duration, gold_duration) / max(
        prediction_duration, gold_duration
    )
    prediction_midpoint = (
        prediction.start_time_s + prediction.end_time_s
    ) / 2
    gold_midpoint = (gold.start_time_s + gold.end_time_s) / 2
    midpoint_error = abs(prediction_midpoint - gold_midpoint)
    midpoint_score = max(
        0.0, 1.0 - midpoint_error / MIDPOINT_TOLERANCE_S
    )
    if midpoint_error > MIDPOINT_TOLERANCE_S + 1e-9:
        return 0.0
    return 0.5 * midpoint_score + 0.3 * iou + 0.2 * duration_ratio


def _maximum_monotonic_weight(
    predictions: list[Event], gold: list[Event]
) -> float:
    predictions = sorted(
        predictions,
        key=lambda event: (
            (event.start_time_s + event.end_time_s) / 2,
            event.start_time_s,
            event.end_time_s,
        ),
    )
    gold = sorted(
        gold,
        key=lambda event: (
            (event.start_time_s + event.end_time_s) / 2,
            event.start_time_s,
            event.end_time_s,
        ),
    )
    dp = [
        [0.0 for _ in range(len(gold) + 1)]
        for _ in range(len(predictions) + 1)
    ]
    for prediction_index, prediction in enumerate(predictions, start=1):
        for gold_index, expected in enumerate(gold, start=1):
            dp[prediction_index][gold_index] = max(
                dp[prediction_index - 1][gold_index],
                dp[prediction_index][gold_index - 1],
                dp[prediction_index - 1][gold_index - 1]
                + _temporal_weight(prediction, expected),
            )
    return dp[-1][-1]


def score(predictions: list[Event], gold: list[Event]) -> dict[str, Any]:
    prediction_groups: dict[tuple[str, str], list[Event]] = defaultdict(list)
    gold_groups: dict[tuple[str, str], list[Event]] = defaultdict(list)
    for event in predictions:
        prediction_groups[(event.reference_id, event.activity_type)].append(
            event
        )
    for event in gold:
        gold_groups[(event.reference_id, event.activity_type)].append(event)

    matched_by_reference = {reference_id: 0.0 for reference_id in REFERENCE_IDS}
    for key in set(prediction_groups) | set(gold_groups):
        weight = _maximum_monotonic_weight(
            prediction_groups[key], gold_groups[key]
        )
        matched_by_reference[key[0]] += weight

    matched_weight = sum(matched_by_reference.values())
    micro_f1 = (
        2 * matched_weight / (len(predictions) + len(gold))
        if predictions or gold
        else 1.0
    )
    macro_values = []
    for reference_id in REFERENCE_IDS:
        prediction_count = sum(
            event.reference_id == reference_id for event in predictions
        )
        gold_count = sum(event.reference_id == reference_id for event in gold)
        denominator = prediction_count + gold_count
        macro_values.append(
            2 * matched_by_reference[reference_id] / denominator
            if denominator
            else 1.0
        )
    macro_target_f1 = sum(macro_values) / len(macro_values)
    reward = max(0.0, min(1.0, micro_f1 * macro_target_f1))
    return {
        "reward": round(reward, 6),
        "details": {
            "reason": "ok",
            "predicted_assignments": len(predictions),
            "gold_assignments": len(gold),
            "matched_weight": round(matched_weight, 6),
            "micro_soft_f1": round(micro_f1, 6),
            "macro_target_soft_f1": round(macro_target_f1, 6),
            "midpoint_tolerance_s": MIDPOINT_TOLERANCE_S,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", required=True, type=Path)
    parser.add_argument("--ground-truth", required=True, type=Path)
    parser.add_argument("--reward-json", required=True, type=Path)
    parser.add_argument("--reward-txt", required=True, type=Path)
    args = parser.parse_args()

    reason = "ok"
    try:
        predictions = _parse(args.solution, strict=False)
    except Exception as exc:
        predictions = []
        reason = f"invalid solution: {exc}"
    gold = _parse(args.ground_truth, strict=True)
    result = score(predictions, gold)
    result["details"]["reason"] = reason
    args.reward_json.parent.mkdir(parents=True, exist_ok=True)
    args.reward_txt.parent.mkdir(parents=True, exist_ok=True)
    args.reward_json.write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    args.reward_txt.write_text(f"{result['reward']}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
