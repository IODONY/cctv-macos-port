# Dependency Session Report

## Install Status

- `.venv/` created inside `/Users/fullcodex/CCTV_Project`.
- `pip`, `setuptools`, and `wheel` upgraded inside `.venv/`.
- `requirements.txt` installed successfully inside `.venv/`.
- No `sudo`, `brew`, `npm`, or global install was used.
- `.venv/`, logs, generated videos, and raw import files remain ignored.

## Diagnostics Run

- `python scripts/mac_diagnostics.py`: passed inside `.venv/`.
- `scripts/agent_validate.sh`: passed with `.venv/` active.
- `python scripts/test_video_writer_codecs.py`: passed; generated videos are under ignored `logs/codec_tests/`.
- `python scripts/test_osc_loopback.py`: passed on `127.0.0.1`.

## Pass / Fail

- Passed: Python environment and dependency imports.
- Passed: model file existence and project-local path checks.
- Passed: logs and snapshots writability.
- Passed: OpenCV AVFoundation and FFmpeg backend availability checks.
- Passed: codec probes for `mp4v`, `avc1`, `H264`, and `MJPG`.
- Passed: OSC loopback.
- Not run: camera, RTSP, TouchDesigner GUI, full tracking, or long tests.

## MPS Status

- MPS is built into the installed torch package.
- MPS is not available in this runtime.
- Current diagnostics select CPU fallback.

## Changes Made

- Added project-local Ultralytics config guard in diagnostics and `walnut_core.py`.
- Adjusted `mac_diagnostics.py` so MPS absence is a reported CPU fallback, not a failing diagnostic.
- Wrote dependency install and session reports.

## Next Tests

1. Run the short webcam AVFoundation probe only after explicit approval.
2. Run RTSP capture only after an approved URL is provided.
3. Open TouchDesigner manually and run OSC/playback checks only after explicit approval.
4. Run the full tracking system only after manual camera and RTSP gates pass.
