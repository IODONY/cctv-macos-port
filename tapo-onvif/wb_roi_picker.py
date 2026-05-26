#!/usr/bin/env python3
"""Pick and store a white/neutral reference ROI for a camera angle.

Camera-less examples:
  python wb_roi_picker.py --camera c210_1f --angle entrance --mock
  python wb_roi_picker.py --camera c210_1f --angle entrance --mock --headless-save --x 640 --y 360 --size 21
  python wb_roi_picker.py --camera c210_1f --angle entrance --image ./sample.jpg
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

import cv2

from wb_core import (
    DEFAULT_ALGORITHM,
    create_mock_frame,
    ensure_camera_angle,
    load_profiles_or_empty,
    make_roi,
    read_frame_from_image,
    read_frame_from_rtsp,
    resolve_roi,
    resolve_rtsp_url,
    sample_roi_from_frame,
    save_profiles,
)
from tapo_wb_client import load_dotenv_if_available


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pick an ROI used as a white/neutral WB reference.")
    parser.add_argument("--profile", default="wb_profiles.json", help="Profile JSON path")
    parser.add_argument("--camera", required=True, help="Camera ID in profile, e.g. c210_1f")
    parser.add_argument("--angle", required=True, help="Angle ID in profile, e.g. entrance")
    parser.add_argument("--image", help="Use a still image instead of a camera stream")
    parser.add_argument("--mock", action="store_true", help="Use a generated mock frame")
    parser.add_argument("--rtsp-url", help="Explicit RTSP URL. Avoid saving passwords in profile JSON.")
    parser.add_argument("--x", type=int, help="Headless ROI center x")
    parser.add_argument("--y", type=int, help="Headless ROI center y")
    parser.add_argument("--size", type=int, default=21, help="ROI size in pixels; odd values are preferred")
    parser.add_argument("--headless-save", action="store_true", help="Save ROI from --x/--y/--size without opening UI")
    return parser


def load_frame(args: argparse.Namespace, camera: Dict[str, Any]) -> Any:
    if args.mock:
        return create_mock_frame()
    if args.image:
        return read_frame_from_image(args.image)
    rtsp_url = resolve_rtsp_url(camera, args.rtsp_url)
    return read_frame_from_rtsp(rtsp_url)


def save_roi_to_profile(profile_path: Path, profiles: Dict[str, Any], camera_id: str, angle_id: str, frame: Any, x: int, y: int, size: int) -> Dict[str, Any]:
    height, width = frame.shape[:2]
    _, angle = ensure_camera_angle(profiles, camera_id, angle_id)
    angle["roi"] = make_roi(x=x, y=y, size=size, frame_width=width, frame_height=height)
    angle.setdefault("gains", {"R": 50, "G": 50, "B": 50})
    save_profiles(profile_path, profiles)
    return angle["roi"]


def overlay(frame, roi: Dict[str, Any], stats: Optional[Dict[str, Any]], dirty: bool) -> Any:
    vis = frame.copy()
    height, width = vis.shape[:2]
    resolved = resolve_roi(roi, width, height)
    x, y, size = resolved["x"], resolved["y"], resolved["size"]
    half = size // 2
    cv2.rectangle(vis, (x - half, y - half), (x + half, y + half), (255, 255, 255), 1)
    cv2.drawMarker(vis, (x, y), (255, 255, 255), cv2.MARKER_CROSS, 12, 1)

    lines = [
        "click: select white/neutral ROI",
        "[/]: size  |  s: save  |  c: sample  |  q: quit",
        f"ROI x={x} y={y} size={size}" + ("  *unsaved" if dirty else ""),
    ]
    if stats:
        rgb = stats["median_rgb"]
        lines.extend(
            [
                f"median RGB: R={rgb[0]:.1f} G={rgb[1]:.1f} B={rgb[2]:.1f}",
                f"neutral_error={stats['neutral_error']:.4f} valid={stats['valid_ratio']:.2f} std={stats['patch_std']:.1f}",
                "OK to adjust" if stats["ok_to_adjust"] else "BLOCKED: " + ", ".join(stats["reasons"]),
            ]
        )

    for i, line in enumerate(lines):
        y0 = 24 + i * 22
        cv2.putText(vis, line, (16, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(vis, line, (16, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 1, cv2.LINE_AA)
    return vis


def main() -> int:
    load_dotenv_if_available()
    args = build_parser().parse_args()
    profile_path = Path(args.profile)
    profiles = load_profiles_or_empty(profile_path)
    camera, angle = ensure_camera_angle(profiles, args.camera, args.angle)
    frame = load_frame(args, camera)
    height, width = frame.shape[:2]

    if args.headless_save:
        if args.x is None or args.y is None:
            raise SystemExit("--headless-save requires --x and --y")
        roi = save_roi_to_profile(profile_path, profiles, args.camera, args.angle, frame, args.x, args.y, args.size)
        print(json.dumps({"saved_roi": roi, "profile": str(profile_path)}, ensure_ascii=False, indent=2))
        return 0

    existing_roi = angle.get("roi") or make_roi(width // 2, height // 2, args.size, width, height)
    resolved = resolve_roi(existing_roi, width, height)
    state = {"x": resolved["x"], "y": resolved["y"], "size": resolved["size"], "stats": None, "dirty": False}
    window = f"WB ROI Picker - {args.camera}/{args.angle}"

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state["x"] = int(x)
            state["y"] = int(y)
            state["dirty"] = True
            roi = make_roi(state["x"], state["y"], state["size"], width, height)
            state["stats"] = sample_roi_from_frame(frame, roi, DEFAULT_ALGORITHM)

    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window, on_mouse)

    while True:
        roi = make_roi(state["x"], state["y"], state["size"], width, height)
        cv2.imshow(window, overlay(frame, roi, state["stats"], state["dirty"]))
        key = cv2.waitKey(30) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("["):
            state["size"] = max(3, int(state["size"]) - 2)
            state["dirty"] = True
        elif key == ord("]"):
            state["size"] = int(state["size"]) + 2
            state["dirty"] = True
        elif key == ord("c"):
            state["stats"] = sample_roi_from_frame(frame, roi, DEFAULT_ALGORITHM)
            print(json.dumps(state["stats"], ensure_ascii=False, indent=2))
        elif key == ord("s"):
            saved = save_roi_to_profile(profile_path, profiles, args.camera, args.angle, frame, state["x"], state["y"], state["size"])
            state["dirty"] = False
            print(json.dumps({"saved_roi": saved, "profile": str(profile_path)}, ensure_ascii=False, indent=2))

    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
