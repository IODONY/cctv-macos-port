# Agent State

## Current Branch

- `mac-port/fullcodex-autonomy`

## Completed

- [x] Verified startup user, repository root, branch, remote, and fast-forward pull.
- [x] Confirmed imported files in `import_here/` match canonical files.
- [x] Added `import_here/` to `.gitignore`.
- [x] Added compact harness and acceptance docs.
- [x] Added macOS diagnostics scripts.
- [x] Added validation harness scripts.
- [x] Applied safe macOS device/backend/path compatibility patches.
- [x] Validated and pushed stable milestones.
- [x] Wrote autonomy report.

## Active

- [ ] Install project dependencies later only after explicit human approval.
- [ ] Run manual camera, RTSP, and TouchDesigner tests only after explicit human approval.

## Notes

- Do not run camera, RTSP, or TouchDesigner GUI tests without human approval.
- Runtime artifacts belong in ignored paths under `logs/` and `snapshots/`.
- Current blocker for runtime validation: missing Python packages `torch`, `ultralytics`, `cv2`, and `python-osc`.
