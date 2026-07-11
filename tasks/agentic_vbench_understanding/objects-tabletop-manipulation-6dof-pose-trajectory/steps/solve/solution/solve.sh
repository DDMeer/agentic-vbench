#!/bin/bash
# Oracle: write the verified object 6DoF pose trajectory as solution.json.
#
# The reference answer is the capture rig's logged object pose, expressed in each clip's
# RGB camera frame. This is the verified answer key baked into the image, not something
# read from the clips. The agent never sees this file.
set -euo pipefail

mkdir -p /workspace/output

python3 - <<'PY'
import json
from pathlib import Path

gt = json.loads(Path("/baked/ground_truth.json").read_text())
clips = {}
for clip in gt["clips"]:
    clips[clip["clip"]] = [
        {"frame": q["frame"], "t_xyz_m": q["t_xyz_m"], "q_wxyz": q["q_wxyz"]}
        for q in clip["queries"]
    ]
Path("/workspace/output/solution.json").write_text(json.dumps({"clips": clips}, indent=2))
PY

n=$(python3 -c "import json;d=json.load(open('/workspace/output/solution.json'));print(sum(len(v) for v in d['clips'].values()))")
echo "oracle: wrote /workspace/output/solution.json (${n} query frames)"
