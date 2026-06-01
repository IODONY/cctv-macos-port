#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/fullcodex/CCTV_Project"
BRANCH="mac-port/fullcodex-autonomy"

if [[ "$(whoami)" != "fullcodex" ]]; then
  echo "Wrong user. Please run Codex from the fullcodex account." >&2
  exit 1
fi

if id -Gn | tr ' ' '\n' | grep -qx admin; then
  echo "This account appears to have administrator privileges. Please switch to a standard user before continuing." >&2
  exit 1
fi

if [[ "$(pwd)" != "$ROOT" ]]; then
  echo "Wrong working directory: $(pwd)" >&2
  exit 1
fi

if [[ "$(git rev-parse --show-toplevel)" != "$ROOT" ]]; then
  echo "Wrong repository root." >&2
  exit 1
fi

if [[ "$(git branch --show-current)" != "$BRANCH" ]]; then
  echo "Wrong branch: $(git branch --show-current)" >&2
  exit 1
fi

echo "PREFLIGHT_OK $ROOT $BRANCH"
