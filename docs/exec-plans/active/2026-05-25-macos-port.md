# macOS Port Active Plan

## Objective

Prepare the project for safe macOS diagnostics and compatibility patches without changing core tracking logic.

## Tasks

- [x] Verify import files and canonical placement.
- [x] Ignore raw import staging area.
- [x] Create compact agent harness docs.
- [ ] Add diagnostics scripts.
- [ ] Add validation scripts.
- [ ] Patch device selection, camera backend, and project-root paths.
- [ ] Validate, commit, push, and report.

## Constraints

- No package installation.
- No camera, RTSP, or TouchDesigner GUI tests without approval.
- No force push or destructive cleanup.
- No biometric identification features.
