#!/bin/bash

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
JUDGE="$HERE/judge.py"
REFERENCE="$HERE/reference.json"
TMP="$HERE/tmp_test_cases"

rm -rf "$TMP"
mkdir -p "$TMP"

python - "$REFERENCE" "$TMP" <<'PY'
import json
import sys
from copy import deepcopy
from pathlib import Path

reference_path = Path(sys.argv[1])
tmp = Path(sys.argv[2])

ref = json.loads(reference_path.read_text())

# Oracle
(tmp / "oracle.json").write_text(
    json.dumps(ref, indent=2) + "\n"
)

# Empty
(tmp / "empty.json").write_text(
    json.dumps({"rallies": []}, indent=2) + "\n"
)

# Malformed
(tmp / "malformed.json").write_text(
    '{"rallies": ['
)

# All timestamps shifted beyond nominal tolerance.
shifted = deepcopy(ref)
for rally in shifted["rallies"]:
    rally["serve_time_sec"] += 5.0
    rally["ending_time_sec"] += 5.0
    for stroke in rally["strokes"]:
        stroke["time_sec"] += 5.0

(tmp / "shifted.json").write_text(
    json.dumps(shifted, indent=2) + "\n"
)

# Correct timing, corrupted categorical labels.
wrong = deepcopy(ref)
for rally in wrong["rallies"]:
    rally["ending"] = "wrong_label"
    for stroke in rally["strokes"]:
        stroke["player"] = "wrong"
        stroke["hand"] = "wrong"
        stroke["stroke"] = "wrong"

(tmp / "wrong_labels.json").write_text(
    json.dumps(wrong, indent=2) + "\n"
)

# Shortcut attempt: only submit the serve stroke for each rally.
sparse = {"rallies": []}
for rally in ref["rallies"]:
    sparse["rallies"].append({
        "serve_time_sec": rally["serve_time_sec"],
        "server": rally["server"],
        "strokes": [rally["strokes"][0]],
        "ending_time_sec": rally["ending_time_sec"],
        "ending": rally["ending"],
    })

(tmp / "sparse_one_stroke.json").write_text(
    json.dumps(sparse, indent=2) + "\n"
)
PY

run_case() {
    local name="$1"

    python "$JUDGE" \
        --solution "$TMP/$name.json" \
        --reference "$REFERENCE" \
        --output "$TMP/$name.result.json" \
        > /dev/null
}

for case in \
    oracle \
    empty \
    malformed \
    shifted \
    wrong_labels \
    sparse_one_stroke
do
    run_case "$case"
done

python - "$TMP" <<'PY'
import json
import sys
from pathlib import Path

tmp = Path(sys.argv[1])

def result(name):
    return json.loads(
        (tmp / f"{name}.result.json").read_text()
    )

oracle = result("oracle")
empty = result("empty")
malformed = result("malformed")
shifted = result("shifted")
wrong = result("wrong_labels")
sparse = result("sparse_one_stroke")

assert oracle["reward"] == 1.0, oracle

assert empty["reward"] == 0.0, empty
assert malformed["reward"] == 0.0, malformed

# A global 5-second shift must not receive meaningful credit.
assert shifted["reward"] == 0.0, shifted

# Perfect timing with entirely incorrect semantic labels must fail.
assert wrong["reward"] == 0.0, wrong

# Reporting only one stroke per rally must be strongly penalized.
assert sparse["reward"] < 0.15, sparse
assert sparse["stroke_semantic_mean"] < 0.40, sparse

print("All verifier regression tests passed.")
print(f"oracle reward: {oracle['reward']:.6f}")
print(f"empty reward: {empty['reward']:.6f}")
print(f"malformed reward: {malformed['reward']:.6f}")
print(f"shifted reward: {shifted['reward']:.6f}")
print(f"wrong-label reward: {wrong['reward']:.6f}")
print(f"sparse-one-stroke reward: {sparse['reward']:.6f}")
PY

mkdir -p /logs/verifier /logs/artifacts

if [ -d /workspace/output ]; then
    cp -a /workspace/output/. /logs/artifacts/ 2>/dev/null || true
fi

python "$JUDGE" \
    --solution /workspace/output/solution.json \
    --reference "$REFERENCE" \
    --reward-json /logs/verifier/reward.json \
    --reward-txt /logs/verifier/reward.txt \
    --details-json /logs/verifier/reward-details.json \
    > /dev/null

rm -rf "$TMP"
