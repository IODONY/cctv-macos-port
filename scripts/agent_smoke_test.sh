#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import importlib.util
from pathlib import Path

root = Path("/Users/fullcodex/CCTV_Project").resolve()
assert Path.cwd().resolve() == root

spec = importlib.util.spec_from_file_location("mac_diagnostics", root / "scripts" / "mac_diagnostics.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
assert module.PROJECT_ROOT == root

for package in ("torch", "ultralytics", "cv2", "pythonosc"):
    state = "available" if importlib.util.find_spec(package) else "missing"
    print(f"DEPENDENCY_{package}={state}")

print("SMOKE_OK")
PY
