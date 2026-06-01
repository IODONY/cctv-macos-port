#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python - <<'PY'
import importlib.util
from pathlib import Path

root = Path.cwd().resolve()

for package in ("torch", "ultralytics", "cv2", "pythonosc"):
    state = "available" if importlib.util.find_spec(package) else "missing"
    print(f"DEPENDENCY_{package}={state}")

for path in (
    root / "src" / "live_topk_bridge.py",
    root / "scripts" / "run_live_from_camera_csv.py",
    root / "touchdesigner" / "touchdesigner_topk_callbacks.py",
):
    assert path.exists(), path

print("SMOKE_OK")
PY
