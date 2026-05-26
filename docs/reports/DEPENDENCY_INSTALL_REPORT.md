# Dependency Install Report

## Summary

- Created local virtual environment: `.venv/`
- Installed dependencies from `requirements.txt` into `.venv/`
- Used `--no-cache-dir` for package installation.
- Wrote package freeze to ignored `logs/pip_freeze.txt`.
- Forced pip cache and Ultralytics config paths under ignored `logs/` for follow-up diagnostics.

## Versions

- Python: `3.11.9`
- pip: `26.1.1`
- torch: `2.12.0`
- ultralytics: `8.4.54`
- OpenCV: `4.13.0`
- numpy: `2.4.6`
- python-osc: installed
- Pillow: `12.2.0`
- scikit-learn: `1.8.0`

## Acceleration And Backends

- CUDA available: `false`
- MPS built: `true`
- MPS available: `false`
- Preferred runtime device from diagnostics: `cpu`
- OpenCV AVFoundation backend constant: present
- OpenCV FFmpeg backend constant: present
- OpenCV build reports FFmpeg enabled: `true`

## Model Files

- `models/yolov8n.pt`: present, non-empty
- `models/yolov8n-pose.pt`: present, non-empty

## Warnings

- The first `pip freeze` emitted a cache warning for the default user cache. It was rerun with `PIP_CACHE_DIR` inside `logs/pip_cache`.
- The first Ultralytics import attempted a fallback config path before `logs/ultralytics/Ultralytics` existed. The project-local config directory was created and subsequent diagnostics used it.

## Result

Dependency installation succeeded. The project is ready for safe non-camera diagnostics and later manual camera/RTSP/TouchDesigner checks when explicitly approved.
