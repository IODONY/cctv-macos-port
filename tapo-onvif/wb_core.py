#!/usr/bin/env python3
"""Core utilities for ROI-based white-balance calibration.

This module contains no Tapo login code. It can be tested without a camera
using --mock frames or still images.
"""

from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

DEFAULT_GAINS: Dict[str, int] = {"R": 50, "G": 50, "B": 50}
DEFAULT_ROI_SIZE = 5
DEFAULT_TARGET_KELVIN = 6500
DEFAULT_ALGORITHM: Dict[str, Any] = {
    "k": 18.0,
    "max_step": 4,
    "min_gain": 0,
    "max_gain": 100,
    "target_channel": "G",
    "dark_threshold": 10,
    "clip_threshold": 245,
    "min_valid_ratio": 0.5,
    "max_clipped_ratio": 0.2,
    "max_dark_ratio": 0.5,
    "max_patch_std": 35.0,
    "neutral_error_threshold": 0.04,
    "target_kelvin": None,
}


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def clamp_gain(value: float, min_gain: int = 0, max_gain: int = 100) -> int:
    value_i = int(round(float(value)))
    return max(min_gain, min(max_gain, value_i))


def normalize_gains(gains: Optional[Dict[str, Any]]) -> Dict[str, int]:
    src = dict(DEFAULT_GAINS)
    if gains:
        src.update(gains)
    return {ch: clamp_gain(src[ch]) for ch in ("R", "G", "B")}


def load_profiles(path: str | Path) -> Dict[str, Any]:
    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")
    return json.loads(profile_path.read_text(encoding="utf-8"))


def save_profiles(path: str | Path, profiles: Dict[str, Any]) -> None:
    profile_path = Path(path)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = profile_path.with_suffix(profile_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(profile_path)


def load_profiles_or_empty(path: str | Path) -> Dict[str, Any]:
    profile_path = Path(path)
    if profile_path.exists():
        return load_profiles(profile_path)
    return {"version": 1, "defaults": {"algorithm": DEFAULT_ALGORITHM}, "cameras": {}}


def get_camera_angle(profiles: Dict[str, Any], camera_id: str, angle_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    try:
        camera = profiles["cameras"][camera_id]
    except KeyError as exc:
        raise KeyError(f"Camera not found in profile: {camera_id}") from exc
    try:
        angle = camera.setdefault("angles", {})[angle_id]
    except KeyError as exc:
        raise KeyError(f"Angle not found in camera profile: {camera_id}/{angle_id}") from exc
    return camera, angle


def ensure_camera_angle(profiles: Dict[str, Any], camera_id: str, angle_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    profiles.setdefault("version", 1)
    profiles.setdefault("defaults", {"algorithm": DEFAULT_ALGORITHM})
    profiles.setdefault("cameras", {})
    camera = profiles["cameras"].setdefault(
        camera_id,
        {
            "model": "Tapo",
            "ip": "",
            "rtsp_url_env": "",
            "tapo_username_env": "TAPO_CAMERA_ID",
            "tapo_password_env": "TAPO_CAMERA_PW",
            "setter_method": "setDayNightModeConfig",
            "angles": {},
        },
    )
    angle = camera.setdefault("angles", {}).setdefault(
        angle_id,
        {"label": angle_id, "roi": {}, "gains": dict(DEFAULT_GAINS)},
    )
    return camera, angle


def merged_algorithm(profiles: Dict[str, Any], camera: Optional[Dict[str, Any]] = None, angle: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    algo = dict(DEFAULT_ALGORITHM)
    algo.update(profiles.get("defaults", {}).get("algorithm", {}))
    if camera:
        algo.update(camera.get("algorithm", {}))
    if angle:
        algo.update(angle.get("algorithm", {}))
    return algo


def make_roi(
    x: int,
    y: int,
    size: int,
    frame_width: int,
    frame_height: int,
    note: str = "",
) -> Dict[str, Any]:
    size = int(size)
    if size % 2 == 0:
        size += 1
    return {
        "x": int(x),
        "y": int(y),
        "size": int(size),
        "nx": round(float(x) / float(frame_width), 6),
        "ny": round(float(y) / float(frame_height), 6),
        "size_ratio": round(float(size) / float(min(frame_width, frame_height)), 6),
        "base_width": int(frame_width),
        "base_height": int(frame_height),
        "note": note,
        "updated_at": now_stamp(),
    }


def resolve_roi(roi: Dict[str, Any], frame_width: int, frame_height: int) -> Dict[str, int]:
    if not roi:
        raise ValueError("ROI is empty. Run wb_roi_picker.py first or provide --x/--y/--size.")

    if "nx" in roi and "ny" in roi:
        x = int(round(float(roi["nx"]) * frame_width))
        y = int(round(float(roi["ny"]) * frame_height))
        if "size_ratio" in roi:
            size = int(round(float(roi["size_ratio"]) * min(frame_width, frame_height)))
        else:
            size = int(roi.get("size", DEFAULT_ROI_SIZE))
    else:
        base_w = int(roi.get("base_width", frame_width))
        base_h = int(roi.get("base_height", frame_height))
        x = int(round(float(roi["x"]) * frame_width / max(1, base_w)))
        y = int(round(float(roi["y"]) * frame_height / max(1, base_h)))
        size = int(round(float(roi.get("size", DEFAULT_ROI_SIZE)) * min(frame_width, frame_height) / max(1, min(base_w, base_h))))

    size = max(3, size)
    if size % 2 == 0:
        size += 1
    x = max(0, min(frame_width - 1, x))
    y = max(0, min(frame_height - 1, y))
    return {"x": x, "y": y, "size": size}


def roi_bounds(resolved_roi: Dict[str, int], frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
    x, y, size = resolved_roi["x"], resolved_roi["y"], resolved_roi["size"]
    half = size // 2
    x0 = max(0, x - half)
    y0 = max(0, y - half)
    x1 = min(frame_width, x + half + 1)
    y1 = min(frame_height, y + half + 1)
    return x0, y0, x1, y1


def sample_roi_from_frame(frame_bgr: np.ndarray, roi: Dict[str, Any], algorithm: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if frame_bgr is None or frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
        raise ValueError("frame_bgr must be a BGR image with shape HxWx3")
    algo = dict(DEFAULT_ALGORITHM)
    if algorithm:
        algo.update(algorithm)

    height, width = frame_bgr.shape[:2]
    resolved = resolve_roi(roi, width, height)
    x0, y0, x1, y1 = roi_bounds(resolved, width, height)
    patch_bgr = frame_bgr[y0:y1, x0:x1]
    if patch_bgr.size == 0:
        raise ValueError(f"ROI patch is empty: {resolved}")

    patch_rgb = patch_bgr[:, :, ::-1].reshape(-1, 3).astype(np.float32)
    dark_threshold = float(algo["dark_threshold"])
    clip_threshold = float(algo["clip_threshold"])

    clipped_mask = np.any(patch_rgb >= clip_threshold, axis=1)
    dark_mask = np.max(patch_rgb, axis=1) <= dark_threshold
    valid_mask = (~clipped_mask) & (~dark_mask) & (np.min(patch_rgb, axis=1) > dark_threshold)

    valid_ratio = float(valid_mask.mean()) if patch_rgb.shape[0] else 0.0
    clipped_ratio = float(clipped_mask.mean()) if patch_rgb.shape[0] else 0.0
    dark_ratio = float(dark_mask.mean()) if patch_rgb.shape[0] else 0.0

    valid_pixels = patch_rgb[valid_mask]
    if valid_pixels.shape[0] == 0:
        valid_pixels = patch_rgb

    median_rgb = np.median(valid_pixels, axis=0)
    mean_rgb = np.mean(valid_pixels, axis=0)
    std_rgb = np.std(valid_pixels, axis=0)
    patch_std = float(np.mean(std_rgb))
    target_kelvin = algo.get("target_kelvin")
    neutral = neutral_error(median_rgb, target_kelvin=target_kelvin)

    reasons = []
    if valid_ratio < float(algo["min_valid_ratio"]):
        reasons.append(f"valid_ratio_low:{valid_ratio:.3f}")
    if clipped_ratio > float(algo["max_clipped_ratio"]):
        reasons.append(f"clipped_ratio_high:{clipped_ratio:.3f}")
    if dark_ratio > float(algo["max_dark_ratio"]):
        reasons.append(f"dark_ratio_high:{dark_ratio:.3f}")
    if patch_std > float(algo["max_patch_std"]):
        reasons.append(f"patch_std_high:{patch_std:.2f}")

    return {
        "frame_width": int(width),
        "frame_height": int(height),
        "roi": resolved,
        "bounds": {"x0": int(x0), "y0": int(y0), "x1": int(x1), "y1": int(y1)},
        "median_rgb": [round(float(v), 3) for v in median_rgb],
        "mean_rgb": [round(float(v), 3) for v in mean_rgb],
        "std_rgb": [round(float(v), 3) for v in std_rgb],
        "patch_std": round(patch_std, 3),
        "valid_ratio": round(valid_ratio, 4),
        "clipped_ratio": round(clipped_ratio, 4),
        "dark_ratio": round(dark_ratio, 4),
        "neutral_error": round(float(neutral["error"]), 6),
        "r_over_g_minus_1": round(float(neutral["r_over_g_minus_1"]), 6),
        "b_over_g_minus_1": round(float(neutral["b_over_g_minus_1"]), 6),
        "target_kelvin": target_kelvin,
        "target_r_over_g": round(float(neutral["target_r_over_g"]), 6),
        "target_b_over_g": round(float(neutral["target_b_over_g"]), 6),
        "ok_to_adjust": len(reasons) == 0,
        "reasons": reasons,
    }


def kelvin_to_rgb(kelvin: Any) -> Tuple[float, float, float]:
    """Approximate color temperature as sRGB values in 0..255.

    The camera API exposes RGB gain, not Kelvin directly, so this is used only
    to derive target R/G and B/G ratios for the feedback controller.
    """
    temp = max(1000.0, min(40000.0, float(kelvin))) / 100.0
    if temp <= 66.0:
        red = 255.0
        green = 99.4708025861 * math.log(temp) - 161.1195681661
        blue = 0.0 if temp <= 19.0 else 138.5177312231 * math.log(temp - 10.0) - 305.0447927307
    else:
        red = 329.698727446 * ((temp - 60.0) ** -0.1332047592)
        green = 288.1221695283 * ((temp - 60.0) ** -0.0755148492)
        blue = 255.0
    return tuple(max(1.0, min(255.0, float(v))) for v in (red, green, blue))


def target_ratios_for_kelvin(kelvin: Any = None) -> Dict[str, float]:
    if kelvin is None:
        return {"r_over_g": 1.0, "b_over_g": 1.0}
    r, g, b = kelvin_to_rgb(kelvin)
    return {"r_over_g": r / g, "b_over_g": b / g}


def neutral_error(rgb: Any, target_kelvin: Any = None) -> Dict[str, float]:
    arr = np.asarray(rgb, dtype=np.float32)
    r, g, b = [max(1.0, float(v)) for v in arr[:3]]
    target = target_ratios_for_kelvin(target_kelvin)
    r_err = (r / g) - target["r_over_g"]
    b_err = (b / g) - target["b_over_g"]
    return {
        "r_over_g_minus_1": r_err,
        "b_over_g_minus_1": b_err,
        "target_r_over_g": target["r_over_g"],
        "target_b_over_g": target["b_over_g"],
        "error": max(abs(r_err), abs(b_err)),
    }


def compute_next_gains(
    rgb: Any,
    current_gains: Optional[Dict[str, Any]] = None,
    algorithm: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, int], Dict[str, Any]]:
    algo = dict(DEFAULT_ALGORITHM)
    if algorithm:
        algo.update(algorithm)

    current = normalize_gains(current_gains)
    r, g, b = [max(1.0, float(v)) for v in np.asarray(rgb, dtype=np.float32)[:3]]
    k = float(algo["k"])
    max_step = float(algo["max_step"])
    min_gain = int(algo["min_gain"])
    max_gain = int(algo["max_gain"])
    target_kelvin = algo.get("target_kelvin")
    target = target_ratios_for_kelvin(target_kelvin)

    # Keep G fixed. Move R/B toward the target R/G and B/G ratios.
    raw_delta_r = math.log((g * target["r_over_g"]) / r) * k
    raw_delta_b = math.log((g * target["b_over_g"]) / b) * k
    delta_r = max(-max_step, min(max_step, raw_delta_r))
    delta_b = max(-max_step, min(max_step, raw_delta_b))

    next_gains = {
        "R": clamp_gain(current["R"] + delta_r, min_gain, max_gain),
        "G": clamp_gain(current["G"], min_gain, max_gain),
        "B": clamp_gain(current["B"] + delta_b, min_gain, max_gain),
    }
    details = {
        "current_gains": current,
        "next_gains": next_gains,
        "delta": {"R": round(delta_r, 3), "G": 0, "B": round(delta_b, 3)},
        "raw_delta": {"R": round(raw_delta_r, 3), "G": 0, "B": round(raw_delta_b, 3)},
        "neutral_error": neutral_error([r, g, b], target_kelvin=target_kelvin),
        "target_kelvin": target_kelvin,
        "target_ratios": target,
        "algorithm": {k: algo[k] for k in ("k", "max_step", "min_gain", "max_gain", "neutral_error_threshold", "target_kelvin")},
    }
    return next_gains, details


def read_frame_from_image(path: str | Path) -> np.ndarray:
    import cv2

    frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if frame is None:
        raise RuntimeError(f"Could not read image: {path}")
    return frame


def read_frame_from_rtsp(rtsp_url: str, warmup_frames: int = 10, timeout_sec: float = 8.0) -> np.ndarray:
    import cv2

    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError("Could not open RTSP stream.")

    start = time.time()
    last_frame = None
    grabbed = 0
    try:
        while time.time() - start < timeout_sec:
            ok, frame = cap.read()
            if not ok:
                continue
            grabbed += 1
            last_frame = frame
            if grabbed > warmup_frames:
                return frame
    finally:
        cap.release()

    if last_frame is not None:
        return last_frame
    raise RuntimeError("Could not read any frame from RTSP stream.")


def resolve_rtsp_url(camera: Dict[str, Any], explicit_url: Optional[str] = None) -> str:
    if explicit_url:
        return explicit_url
    env_name = camera.get("rtsp_url_env")
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    if camera.get("rtsp_url"):
        return str(camera["rtsp_url"])
    raise ValueError("No RTSP URL. Provide --rtsp-url or set camera.rtsp_url_env in wb_profiles.json.")


def parse_rgb(text: str) -> Tuple[int, int, int]:
    parts = [int(p.strip()) for p in text.split(",")]
    if len(parts) != 3:
        raise ValueError("RGB must be formatted as R,G,B, e.g. 176,162,130")
    return parts[0], parts[1], parts[2]


def create_mock_frame(
    width: int = 1280,
    height: int = 720,
    patch_center: Tuple[int, int] = (640, 360),
    patch_size: int = 81,
    patch_rgb: Tuple[int, int, int] = (176, 162, 130),
    background_rgb: Tuple[int, int, int] = (42, 45, 50),
) -> np.ndarray:
    """Create a BGR mock frame with a tinted reference patch.

    patch_rgb deliberately defaults to a warm/yellow cast so the calibrator
    should lower R slightly and raise B.
    """
    frame_rgb = np.zeros((height, width, 3), dtype=np.uint8)
    frame_rgb[:, :] = np.array(background_rgb, dtype=np.uint8)

    # Add subtle horizontal gradient so the frame is visually legible.
    gradient = np.linspace(0, 24, width, dtype=np.uint8)
    frame_rgb[:, :, 0] = np.clip(frame_rgb[:, :, 0].astype(np.int16) + gradient, 0, 255).astype(np.uint8)

    x, y = patch_center
    half = patch_size // 2
    x0, x1 = max(0, x - half), min(width, x + half + 1)
    y0, y1 = max(0, y - half), min(height, y + half + 1)
    frame_rgb[y0:y1, x0:x1] = np.array(patch_rgb, dtype=np.uint8)

    # BGR for OpenCV.
    return frame_rgb[:, :, ::-1].copy()
