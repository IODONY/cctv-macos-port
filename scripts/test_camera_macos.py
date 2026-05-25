#!/usr/bin/env python3
"""Manual, short macOS webcam capture probe.

Do not run this automatically. It opens one camera briefly with AVFoundation.
"""

from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera-index", type=int, default=0)
    args = parser.parse_args()

    import cv2

    cap = cv2.VideoCapture(args.camera_index, cv2.CAP_AVFOUNDATION)
    try:
        ok, frame = cap.read()
        report = {
            "camera_index": args.camera_index,
            "backend": "CAP_AVFOUNDATION",
            "opened": bool(cap.isOpened()),
            "frame_read": bool(ok),
            "shape": list(frame.shape) if ok and frame is not None else None,
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
