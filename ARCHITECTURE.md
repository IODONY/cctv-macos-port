# Architecture

This project is a macOS-isolated port of a CCTV / MTMC / TouchDesigner visitor tracking artwork.

## Components

- `src/walnut_core.py`: YOLO pose and object analysis, visitor profiling, and local track state.
- `src/rtsp_osc_bridge.py`: multi-camera capture, Type A/B/C orchestration, clip recording, and OSC output.
- `src/pose_color_detection_v2.py`: webcam-oriented local pose/color demo and CSV visitor logging.
- `touchdesigner/`: callback scripts for OSC In DAT / playback integration.
- `models/`: local YOLO model files used by diagnostics and runtime.
- `logs/` and `snapshots/`: ignored runtime output.

## Porting Direction

The macOS port should separate environment checks from runtime behavior, prefer project-root-relative paths, and support Apple Silicon MPS when available. Camera, RTSP, and TouchDesigner checks remain opt-in.

## Artwork Invariant

Tracking should not collapse to a single "correct identity" result. The system must keep room for control, exclusion, distortion, and reconstruction by preserving outcomes including `matched`, `ambiguous`, `low_confidence`, and `no_match`.
