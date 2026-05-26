#!/usr/bin/env python3
"""Pick and store a white/neutral reference ROI for a camera angle.

Camera-less examples:
  python wb_roi_picker.py --camera c210_1f --angle entrance --mock
  python wb_roi_picker.py --camera c210_1f --angle entrance --mock --headless-save --x 640 --y 360 --size 5
  python wb_roi_picker.py --camera c210_1f --angle entrance --image ./sample.jpg
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import cv2

from wb_core import (
    DEFAULT_ALGORITHM,
    compute_next_gains,
    create_mock_frame,
    ensure_camera_angle,
    load_profiles_or_empty,
    make_roi,
    merged_algorithm,
    read_frame_from_image,
    read_frame_from_rtsp,
    resolve_roi,
    resolve_rtsp_url,
    sample_roi_from_frame,
    save_profiles,
)
from tapo_wb_client import (
    DEFAULT_EXPOSURE_MAX,
    DEFAULT_EXPOSURE_MIN,
    clamp_exposure_level,
    client_from_camera_profile,
    load_dotenv_if_available,
)


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
    parser.add_argument("--size", type=int, default=5, help="ROI size in pixels; odd values are preferred")
    parser.add_argument("--headless-save", action="store_true", help="Save ROI from --x/--y/--size without opening UI")
    parser.add_argument("--apply-on-save", action="store_true", help="When s is pressed, save the ROI, apply proposed WB gains, and refresh the preview frame")
    parser.add_argument("--force", action="store_true", help="With --apply-on-save, apply even if ROI safety checks fail")
    parser.add_argument("--settle", type=float, default=1.5, help="Seconds to wait after applying gains before refreshing preview")
    parser.add_argument("--k", type=float, help="Override controller strength for --apply-on-save")
    parser.add_argument("--max-step", type=float, help="Override max gain step per save for --apply-on-save")
    parser.add_argument("--exposure-step", type=int, default=1, help="Exposure compensation step for -/= keys")
    parser.add_argument("--exposure-min", type=int, default=DEFAULT_EXPOSURE_MIN, help="Minimum exposure compensation level")
    parser.add_argument("--exposure-max", type=int, default=DEFAULT_EXPOSURE_MAX, help="Maximum exposure compensation level")
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


def overlay(
    frame,
    roi: Dict[str, Any],
    stats: Optional[Dict[str, Any]],
    dirty: bool,
    apply_on_save: bool = False,
    message: str = "",
) -> Any:
    vis = frame.copy()
    height, width = vis.shape[:2]
    resolved = resolve_roi(roi, width, height)
    x, y, size = resolved["x"], resolved["y"], resolved["size"]
    half = size // 2
    cv2.rectangle(vis, (x - half, y - half), (x + half, y + half), (255, 255, 255), 1)
    cv2.drawMarker(vis, (x, y), (255, 255, 255), cv2.MARKER_CROSS, 12, 1)

    lines = [
        "click: select white/neutral ROI",
        "[/]: size  |  -/=: exposure  |  s: save/apply/preview  |  c: sample  |  r: refresh  |  q: quit"
        if apply_on_save
        else "[/]: size  |  -/=: exposure  |  s: save  |  c: sample  |  r: refresh  |  q: quit",
        f"ROI x={x} y={y} size={size}" + ("  *unsaved" if dirty else ""),
    ]
    if message:
        lines.append(message)
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


def ensure_client(camera: Dict[str, Any], state: Dict[str, Any]):
    if state.get("client") is None:
        state["client"] = client_from_camera_profile(camera)
    if state.get("backup_path") is None:
        state["backup_path"] = state["client"].backup_image_common()
        print(f"[BACKUP] image.common saved to {state['backup_path']}")
    return state["client"]


def refresh_frame(args: argparse.Namespace, camera: Dict[str, Any], roi: Dict[str, Any], state: Dict[str, Any]) -> None:
    refreshed = load_frame(args, camera)
    state["frame"] = refreshed
    state["height"], state["width"] = refreshed.shape[:2]
    refreshed_roi = resolve_roi(roi, state["width"], state["height"])
    state["x"] = refreshed_roi["x"]
    state["y"] = refreshed_roi["y"]
    state["size"] = refreshed_roi["size"]


def adjust_exposure(
    args: argparse.Namespace,
    camera: Dict[str, Any],
    roi: Dict[str, Any],
    state: Dict[str, Any],
    direction: int,
) -> None:
    if args.mock or args.image:
        state["message"] = "exposure apply requires live camera"
        return

    client = ensure_client(camera, state)
    current = state.get("exposure_level")
    if current is None:
        current = client.get_exposure_level()

    step = max(1, abs(int(args.exposure_step)))
    proposed = clamp_exposure_level(
        int(current) + (step * int(direction)),
        min_level=int(args.exposure_min),
        max_level=int(args.exposure_max),
    )
    if proposed == current:
        state["message"] = f"exposure at limit: {current}"
        return

    print(f"[APPLY] exposure {current} -> {proposed}")
    result = client.apply_exposure_level(
        proposed,
        min_level=int(args.exposure_min),
        max_level=int(args.exposure_max),
    )
    print(json.dumps({"set_response": result}, ensure_ascii=False, indent=2))
    state["exposure_level"] = proposed
    time.sleep(max(0.0, min(float(args.settle), 1.5)))
    refresh_frame(args, camera, roi, state)
    state["stats"] = sample_roi_from_frame(state["frame"], roi, DEFAULT_ALGORITHM)
    state["message"] = f"exposure applied: {proposed}"


def apply_saved_roi(
    args: argparse.Namespace,
    profile_path: Path,
    profiles: Dict[str, Any],
    camera: Dict[str, Any],
    angle: Dict[str, Any],
    roi: Dict[str, Any],
    frame: Any,
    state: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    algorithm = merged_algorithm(profiles, camera, angle)
    if args.k is not None:
        algorithm["k"] = args.k
    if args.max_step is not None:
        algorithm["max_step"] = args.max_step

    stats = sample_roi_from_frame(frame, roi, algorithm)
    gains = dict(angle.get("gains") or camera.get("gains") or {"R": 50, "G": 50, "B": 50})
    proposed, details = compute_next_gains(stats["median_rgb"], gains, algorithm)
    row = {"stats": stats, "details": details, "proposed_gains": proposed}
    print("\n=== ROI save/apply preview ===")
    print(json.dumps(row, ensure_ascii=False, indent=2))

    if not stats["ok_to_adjust"] and not args.force:
        state["message"] = "saved; apply blocked: " + ", ".join(stats["reasons"])
        print("[BLOCKED] ROI safety checks failed. Not applying. Use --force to override.")
        return stats

    ensure_client(camera, state)

    print(f"[APPLY] gains {gains} -> {proposed}")
    result = state["client"].apply_manual_wb_gains(proposed)
    print(json.dumps({"set_response": result}, ensure_ascii=False, indent=2))

    angle["gains"] = proposed
    angle["last_roi_picker_apply"] = row
    save_profiles(profile_path, profiles)
    time.sleep(max(0.0, args.settle))

    refresh_frame(args, camera, roi, state)
    state["message"] = f"applied preview: R={proposed['R']} G={proposed['G']} B={proposed['B']}"
    return sample_roi_from_frame(state["frame"], roi, algorithm)


def main() -> int:
    load_dotenv_if_available()
    args = build_parser().parse_args()
    if args.apply_on_save and (args.mock or args.image):
        raise SystemExit("--apply-on-save requires a live camera frame; do not use --mock or --image")

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
    state = {
        "x": resolved["x"],
        "y": resolved["y"],
        "size": resolved["size"],
        "stats": None,
        "dirty": False,
        "frame": frame,
        "width": width,
        "height": height,
        "message": "",
        "client": None,
        "backup_path": None,
        "exposure_level": None,
    }
    window = f"WB ROI Picker - {args.camera}/{args.angle}"

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state["x"] = int(x)
            state["y"] = int(y)
            state["dirty"] = True
            state["message"] = ""
            roi = make_roi(state["x"], state["y"], state["size"], state["width"], state["height"])
            state["stats"] = sample_roi_from_frame(state["frame"], roi, DEFAULT_ALGORITHM)

    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window, on_mouse)

    while True:
        roi = make_roi(state["x"], state["y"], state["size"], state["width"], state["height"])
        cv2.imshow(window, overlay(state["frame"], roi, state["stats"], state["dirty"], args.apply_on_save, state["message"]))
        key = cv2.waitKey(30) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("["):
            state["size"] = max(3, int(state["size"]) - 2)
            state["dirty"] = True
            state["message"] = ""
        elif key == ord("]"):
            state["size"] = int(state["size"]) + 2
            state["dirty"] = True
            state["message"] = ""
        elif key == ord("-"):
            adjust_exposure(args, camera, roi, state, direction=-1)
        elif key in (ord("="), ord("+")):
            adjust_exposure(args, camera, roi, state, direction=1)
        elif key == ord("c"):
            state["stats"] = sample_roi_from_frame(state["frame"], roi, DEFAULT_ALGORITHM)
            print(json.dumps(state["stats"], ensure_ascii=False, indent=2))
        elif key == ord("r"):
            refresh_frame(args, camera, roi, state)
            state["stats"] = None
            state["message"] = "preview refreshed"
        elif key == ord("s"):
            saved = save_roi_to_profile(
                profile_path,
                profiles,
                args.camera,
                args.angle,
                state["frame"],
                state["x"],
                state["y"],
                state["size"],
            )
            state["dirty"] = False
            print(json.dumps({"saved_roi": saved, "profile": str(profile_path)}, ensure_ascii=False, indent=2))
            state["stats"] = sample_roi_from_frame(state["frame"], saved, DEFAULT_ALGORITHM)
            if args.apply_on_save:
                state["stats"] = apply_saved_roi(args, profile_path, profiles, camera, angle, saved, state["frame"], state)

    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
