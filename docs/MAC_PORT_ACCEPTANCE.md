# macOS Port Acceptance

## Required Before Manual Runtime Tests

- [ ] `python3 scripts/mac_diagnostics.py` completes without crashing.
- [ ] `scripts/agent_validate.sh` passes.
- [ ] YOLO model paths resolve under `/Users/fullcodex/CCTV_Project/models`.
- [ ] Logs and snapshots resolve under project-local ignored folders.
- [ ] Importing project modules does not start camera, RTSP, or TouchDesigner loops.
- [ ] Apple Silicon MPS is detected when torch supports it, with CPU fallback.
- [ ] macOS webcam backend uses AVFoundation where applicable.

## Manual Approval Gates

- [ ] Webcam capture test.
- [ ] RTSP capture test with approved URL.
- [ ] TouchDesigner OSC / GUI playback test.
- [ ] Long-running multi-camera tracking test.
