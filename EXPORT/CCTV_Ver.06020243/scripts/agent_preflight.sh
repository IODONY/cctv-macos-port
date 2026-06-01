#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required=(
  "src/live_topk_bridge.py"
  "src/visual_reid.py"
  "scripts/run_live_from_camera_csv.py"
  "touchdesigner/touchdesigner_topk_callbacks.py"
  "models/yolov8n.pt"
  "models/yolov8n-pose.pt"
  "config/cameras/cameras.production.template.csv"
)

for path in "${required[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "Missing required runtime file: $path" >&2
    exit 1
  fi
done

mkdir -p logs snapshots data
echo "PREFLIGHT_OK $ROOT"
