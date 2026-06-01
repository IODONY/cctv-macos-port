#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/fullcodex/CCTV_Project"
cd "$ROOT"

mkdir -p docs/reports

{
  echo "# Autonomy Snapshot"
  echo
  echo "- Generated: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "- User: $(whoami)"
  echo "- Root: $(git rev-parse --show-toplevel)"
  echo "- Branch: $(git branch --show-current)"
  echo "- HEAD: $(git rev-parse --short HEAD)"
  echo
  echo "## Git Status"
  echo
  echo '```text'
  git status --short --branch
  echo '```'
  echo
  echo "## Recent Commits"
  echo
  echo '```text'
  git log --oneline -8
  echo '```'
} > docs/reports/AUTONOMY_SNAPSHOT.md

echo "WROTE docs/reports/AUTONOMY_SNAPSHOT.md"
