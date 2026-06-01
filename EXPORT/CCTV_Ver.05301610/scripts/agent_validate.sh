#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/fullcodex/CCTV_Project"
cd "$ROOT"

scripts/agent_preflight.sh

python3 -m py_compile src/*.py
python3 -m py_compile scripts/*.py
python3 -m py_compile touchdesigner/*.py

scripts/agent_smoke_test.sh

python3 scripts/mac_diagnostics.py || {
  echo "mac_diagnostics reported missing runtime dependencies or environment support." >&2
}

staged_generated="$(git diff --cached --name-only -- 'logs/**' 'snapshots/**' '*.mp4' '*.mov' '*.avi' '*.mkv' '*.m4v' || true)"
if [[ -n "$staged_generated" ]]; then
  echo "Generated logs/videos are staged:" >&2
  echo "$staged_generated" >&2
  exit 1
fi

changed_docs_scripts="$(git diff --name-only --cached -- scripts docs AGENTS.md ARCHITECTURE.md || true)"
changed_docs_scripts+=$'\n'
changed_docs_scripts+="$(git diff --name-only -- scripts docs AGENTS.md ARCHITECTURE.md || true)"
changed_docs_scripts="$(echo "$changed_docs_scripts" | sed '/^$/d' | sort -u)"

if [[ -n "$changed_docs_scripts" ]]; then
  while IFS= read -r file; do
    case "$file" in
      docs/GIT_SAFETY.md|docs/AGENT_STATE.md|docs/QUALITY_GATES.md|AGENTS.md)
        continue
        ;;
    esac
    if grep -E '/Users/Donoyung|/Users/Shared|/Applications|/Library|/System|/usr/local|/opt/homebrew|iCloud Drive|Dropbox|Google Drive' "$file" >/dev/null 2>&1; then
      echo "Forbidden external path reference in $file" >&2
      exit 1
    fi
  done <<< "$changed_docs_scripts"
fi

git status --short --branch
echo "VALIDATE_OK"
