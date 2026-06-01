#!/usr/bin/env python3
"""Manual, short macOS webcam capture probe.

Do not run this automatically. It opens one camera briefly with AVFoundation.
"""

from __future__ import annotations

import argparse
import json
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera-index", "--index", dest="camera_index", type=int, default=0)
    parser.add_argument("--frames", type=int, default=1)
    args = parser.parse_args()

    import cv2

    cap = cv2.VideoCapture(args.camera_index, cv2.CAP_AVFOUNDATION)
    try:
        opened = bool(cap.isOpened())
        captured = 0
        last_shape = None
        started = time.monotonic()
        for _ in range(max(1, args.frames)):
            ok, frame = cap.read()
            if ok and frame is not None:
                captured += 1
                last_shape = list(frame.shape)
            if time.monotonic() - started > 5.0:
                break

        backend_name = None
        if opened and hasattr(cap, "getBackendName"):
            try:
                backend_name = cap.getBackendName()
            except cv2.error:
                backend_name = None

        report = {
            "camera_index": args.camera_index,
            "backend": "CAP_AVFOUNDATION",
            "backend_name": backend_name,
            "opened": opened,
            "requested_frames": max(1, args.frames),
            "captured_frames": captured,
            "frame_read": captured > 0,
            "shape": last_shape,
            "width": cap.get(cv2.CAP_PROP_FRAME_WIDTH) if opened else 0,
            "height": cap.get(cv2.CAP_PROP_FRAME_HEIGHT) if opened else 0,
            "fps": cap.get(cv2.CAP_PROP_FPS) if opened else 0,
            "permission_may_be_required": not opened or captured == 0,
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["opened"] and report["frame_read"] else 1
    finally:
        cap.release()


if __name__ == "__main__":
    if sys.platform != "darwin":
        print(json.dumps({"ok": False, "error": "macOS only"}))
        raise SystemExit(1)
    raise SystemExit(main())
