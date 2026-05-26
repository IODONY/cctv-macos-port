# Webcam Probe Report

## Command

```sh
source .venv/bin/activate
python scripts/test_camera_macos.py --index 0 --frames 30
```

## Result

- Camera opened: `false`
- Backend requested: `CAP_AVFOUNDATION`
- Backend name: not available because the camera did not open
- Actual width: `0`
- Actual height: `0`
- Actual fps: `0`
- Requested frames: `30`
- Captured frames: `0`
- Frame captured: `false`

## Blocker

OpenCV reported that macOS camera access was denied for the current application/session. Manual camera permission approval is required before rerunning the short webcam probe.

## Notes

- No RTSP, TouchDesigner, full tracking, or long-running tests were run.
- Probe JSON was written to ignored `logs/webcam_probe.json`.
- No generated frames, images, or videos were committed.
