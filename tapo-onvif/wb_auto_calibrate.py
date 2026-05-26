#!/usr/bin/env python3
"""Compute ROI-based WB gains, with dry-run mode by default.

Camera-less examples:
  python wb_auto_calibrate.py --profile wb_profiles.example.json --camera c210_1f --angle entrance --mock
  python wb_auto_calibrate.py --camera c210_1f --angle entrance --image ./sample.jpg --write-profile

Real-camera application, later, after account unlock:
  python wb_auto_calibrate.py --camera c210_1f --angle entrance --apply --iterations 5
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

from wb_core import (
    compute_next_gains,
    create_mock_frame,
    get_camera_angle,
    load_profiles,
    merged_algorithm,
    parse_rgb,
    read_frame_from_image,
    read_frame_from_rtsp,
    resolve_roi,
    resolve_rtsp_url,
    sample_roi_from_frame,
    save_profiles,
)
from tapo_wb_client import client_from_camera_profile, load_dotenv_if_available, print_dry_run_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ROI-based automatic manual-WB gain calculator for Tapo cameras.")
    parser.add_argument("--profile", default="wb_profiles.json", help="Profile JSON path")
    parser.add_argument("--camera", required=True, help="Camera ID in profile")
    parser.add_argument("--angle", required=True, help="Angle ID in profile")
    parser.add_argument("--image", help="Use a still image as frame source")
    parser.add_argument("--mock", action="store_true", help="Use generated mock frame")
    parser.add_argument("--mock-rgb", default="176,162,130", help="Mock patch RGB, e.g. 176,162,130")
    parser.add_argument("--rtsp-url", help="Explicit RTSP URL")
    parser.add_argument("--apply", action="store_true", help="Actually apply gains to Tapo local API. Default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Apply even if ROI safety checks fail")
    parser.add_argument("--write-profile", action="store_true", help="Save proposed/last gains and report into profile JSON")
    parser.add_argument("--iterations", type=int, default=1, help="Number of feedback iterations. Use >1 only with RTSP")
    parser.add_argument("--settle", type=float, default=1.5, help="Seconds to wait after applying gains")
    parser.add_argument("--k", type=float, help="Override controller strength")
    parser.add_argument("--max-step", type=float, help="Override max gain step per iteration")
    return parser


def read_frame(args: argparse.Namespace, camera: Dict[str, Any], angle: Dict[str, Any]):
    if args.mock:
        rgb = parse_rgb(args.mock_rgb)
        roi = angle.get("roi") or {"x": 640, "y": 360, "size": 5, "base_width": 1280, "base_height": 720}
        resolved = resolve_roi(roi, 1280, 720)
        return create_mock_frame(patch_center=(resolved["x"], resolved["y"]), patch_rgb=rgb)
    if args.image:
        return read_frame_from_image(args.image)
    rtsp_url = resolve_rtsp_url(camera, args.rtsp_url)
    return read_frame_from_rtsp(rtsp_url)


def main() -> int:
    load_dotenv_if_available()
    args = build_parser().parse_args()
    profiles = load_profiles(args.profile)
    camera, angle = get_camera_angle(profiles, args.camera, args.angle)
    algorithm = merged_algorithm(profiles, camera, angle)
    if args.k is not None:
        algorithm["k"] = args.k
    if args.max_step is not None:
        algorithm["max_step"] = args.max_step

    if args.apply and (args.mock or args.image) and args.iterations > 1:
        print("[WARN] Static image/mock cannot reflect camera changes. Forcing iterations=1.")
        args.iterations = 1

    gains = dict(angle.get("gains") or camera.get("gains") or {"R": 50, "G": 50, "B": 50})
    report = {"camera": args.camera, "angle": args.angle, "apply": bool(args.apply), "iterations": []}

    client = None
    if args.apply:
        client = client_from_camera_profile(camera)
        backup = client.backup_image_common()
        print(f"[BACKUP] image.common saved to {backup}")

    for i in range(max(1, args.iterations)):
        frame = read_frame(args, camera, angle)
        stats = sample_roi_from_frame(frame, angle.get("roi", {}), algorithm)
        proposed, details = compute_next_gains(stats["median_rgb"], gains, algorithm)
        row = {"iteration": i + 1, "stats": stats, "details": details, "proposed_gains": proposed}
        report["iterations"].append(row)

        print("\n=== WB calibration step ===")
        print(json.dumps(row, ensure_ascii=False, indent=2))

        if not stats["ok_to_adjust"] and not args.force:
            print("\n[BLOCKED] ROI safety checks failed. Not applying. Reasons:")
            for reason in stats["reasons"]:
                print(f"  - {reason}")
            print_dry_run_payload(proposed, camera.get("setter_method", "setDayNightModeConfig"))
            return 2

        if not args.apply:
            print_dry_run_payload(proposed, camera.get("setter_method", "setDayNightModeConfig"))
            gains = proposed
            break

        assert client is not None
        print(f"[APPLY] gains {gains} -> {proposed}")
        result = client.apply_manual_wb_gains(proposed)
        print(json.dumps({"set_response": result}, ensure_ascii=False, indent=2))
        gains = proposed
        time.sleep(max(0.0, args.settle))

        if float(stats["neutral_error"]) <= float(algorithm["neutral_error_threshold"]):
            print("[OK] Neutral error is already under threshold.")
            break

    if args.write_profile:
        angle["gains"] = gains
        angle["last_calibration"] = report
        save_profiles(args.profile, profiles)
        print(f"[PROFILE] Updated {args.profile}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
