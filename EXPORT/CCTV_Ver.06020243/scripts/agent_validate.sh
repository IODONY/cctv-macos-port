#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

scripts/agent_preflight.sh
python -m py_compile src/*.py scripts/*.py touchdesigner/*.py run/*.py
python scripts/test_live_topk_units.py
scripts/agent_smoke_test.sh
python scripts/mac_diagnostics.py || {
  echo "mac_diagnostics reported missing runtime dependencies or environment support." >&2
}

echo "VALIDATE_OK"
