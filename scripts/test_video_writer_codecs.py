#!/usr/bin/env python3
"""Synthetic OpenCV VideoWriter codec probe.

Generated files are written under logs/codec_tests/ and should never be staged.
"""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "logs" / "codec_tests"


def probe_codec(cv2, np, codec: str) -> dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ext = ".avi" if codec == "MJPG" else ".mp4"
    output = OUTPUT_DIR / f"codec_{codec.lower()}{ext}"
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*codec), 12, (160, 90))
    opened = bool(writer.isOpened())
    if opened:
        for index in range(12):
            frame = np.zeros((90, 160, 3), dtype=np.uint8)
            frame[:, :, 0] = (index * 20) % 255
            frame[:, :, 1] = 80
            frame[:, :, 2] = 180
            writer.write(frame)
    writer.release()

    cap = cv2.VideoCapture(str(output))
    read_ok, _ = cap.read()
    cap.release()
    return {
        "codec": codec,
        "opened": opened,
        "readback": bool(read_ok),
        "path": str(output),
        "size": output.stat().st_size if output.exists() else 0,
        "ok": opened and bool(read_ok),
    }


def main() -> int:
    try:
        import cv2
        import numpy as np
    except Exception as exc:  # noqa: BLE001 - diagnostics should be explicit.
        print(json.dumps({"ok": False, "error": repr(exc)}, indent=2, sort_keys=True))
        return 1

    results = [probe_codec(cv2, np, codec) for codec in ("mp4v", "avc1", "H264", "MJPG")]
    report = {"output_dir": str(OUTPUT_DIR), "results": results, "ok": any(r["ok"] for r in results)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
