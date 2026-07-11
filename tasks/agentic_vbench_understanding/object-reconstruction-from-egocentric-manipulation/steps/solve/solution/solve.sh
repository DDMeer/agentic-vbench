#!/bin/bash
# Oracle: emit the verified reference mesh for each clip's target object as clip_XX.obj.
#
# The reference meshes are the scanned 3D models of the interacted objects, baked into
# the image. Exporting them (in an arbitrary pose) is the answer key — the scorer aligns
# shape scale-free, so any pose/scale of the correct shape scores 1.0. The agent never
# sees these meshes.
set -euo pipefail

mkdir -p /workspace/output

python3 - <<'PY'
import json
from pathlib import Path
import trimesh

objs = json.loads(Path("/baked/objects.json").read_text())
for cid in objs:
    m = trimesh.load(f"/baked/ref_{cid}.glb", force="mesh")
    m.export(f"/workspace/output/{cid}.obj")
    print(f"oracle: wrote /workspace/output/{cid}.obj ({len(m.vertices)} verts)")
PY
