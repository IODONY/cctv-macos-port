# CCTV / MTMC / TouchDesigner Tracking System

## Purpose

A macOS-isolated development workspace for a CCTV-based visitor tracking artwork using YOLO pose detection, appearance-based visitor profiling, OSC communication, clip recording, and TouchDesigner playback.

## Workspace Root

`/Users/fullcodex/CCTV_Project`

## Main Folders

- `src/`: Python tracking and bridge code
- `models/`: YOLO model files
- `touchdesigner/`: TouchDesigner callback scripts
- `data/`: sample CSV or non-sensitive test data
- `snapshots/`: generated visitor clips, ignored by Git
- `logs/`: diagnostic and runtime logs, ignored by Git
- `scripts/`: diagnostic and setup scripts
- `docs/`: documentation

## Safety Rules

- Work only inside this project folder.
- Do not use `sudo`.
- Do not modify original user files.
- Do not access `/Users/Donoyung` or other user folders.
- Use Git commits before large changes.

## Next Expected Manual Actions

1. Place project source files in `import_here/` if not already imported.
2. Add YOLO model files to `models/`.
3. Later, create a Python virtual environment.
4. Later, run macOS diagnostics.
5. Later, test camera, RTSP, OSC, codec, and TouchDesigner playback.
