# macOS Port Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Torch installed without MPS support | Slow CPU-only runtime | Detect MPS and report fallback clearly. |
| OpenCV lacks FFmpeg RTSP support | RTSP test fails | Keep RTSP test gated and report backend build info. |
| macOS camera permission denial | Webcam test fails | Keep webcam test manual and short. |
| VideoWriter codec mismatch | Clip recording fails | Probe local codecs under ignored `logs/codec_tests/`. |
| CWD-dependent paths | Models or outputs misplaced | Resolve paths relative to project root. |
| Import side effects | Cameras start during validation | Keep entrypoints under `if __name__ == "__main__"`. |
| Identity over-optimization | Artwork intent is flattened | Preserve ambiguous and low-confidence outcomes. |
