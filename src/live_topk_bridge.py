#!/usr/bin/env python3
"""Live YOLO person clips -> appearance embedding -> Top-K OSC bridge.

This runtime is intentionally track-centric:
- Gallery cameras record one full-frame clip per detected local person track.
- Recording starts when YOLO first sees the person and ends when that track
  disappears for a small grace window.
- Each finished track stores a cropped best ReID frame and an appearance embedding.
- Query cameras periodically embed the current target person and send ranked
  clip paths to TouchDesigner.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import queue
import re
import shutil
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import cv2
import numpy as np
from pythonosc.udp_client import SimpleUDPClient

from live_session_grouping import regroup_live_session
from visual_reid import (
    crop_candidate_to_json,
    create_visual_embedder,
    crop_person as visual_crop_person,
    crop_quality as visual_crop_quality,
    make_crop_candidate,
    resize_with_padding as visual_resize_with_padding,
    select_diverse_crop_candidates,
)
from walnut_core import WalnutAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_CACHE_ROOT = PROJECT_ROOT / "logs" / "model_cache" / "torch"
GALLERY_TYPES = {"A", "B", "G"}
QUERY_TYPES = {"C", "Q"}
PREVIEW_LOCK = threading.Lock()
PREVIEW_QUEUE: queue.Queue[tuple[str, np.ndarray, float]] = queue.Queue(maxsize=12)
PREVIEW_DISABLED = False
PREVIEW_ERROR_REPORTED = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Live gallery/query bridge for YOLO person clips and Top-K TouchDesigner playback."
    )
    parser.add_argument(
        "--rtsp",
        default="",
        help='Comma-separated video sources. Supports RTSP URLs, files, and webcam:N tokens.',
    )
    parser.add_argument(
        "--rtsp-envs",
        default="",
        help="Comma-separated environment variable names containing RTSP URLs.",
    )
    parser.add_argument(
        "--cam-types",
        default="",
        help=(
            "Comma-separated camera roles matching source order. "
            "Use G/A/B for gallery cameras and Q/C for query cameras."
        ),
    )
    parser.add_argument(
        "--cam-labels",
        default="",
        help='Comma-separated physical/source labels matching source order. Example: "tapo_1,tapo_2,macbook_query".',
    )
    parser.add_argument("--osc-host", default="127.0.0.1")
    parser.add_argument("--osc-port", type=int, default=7000)
    parser.add_argument("--osc-dry-run", action="store_true", help="Print OSC payloads instead of sending UDP.")
    parser.add_argument("--disable-osc", action="store_true", help="Do not send OSC messages.")
    parser.add_argument("--frame-width", type=int, default=1280)
    parser.add_argument("--frame-height", type=int, default=720)
    parser.add_argument("--inference-interval", type=int, default=2)
    parser.add_argument("--print-interval-frames", type=int, default=60)
    parser.add_argument(
        "--tracker-backend",
        choices=("custom", "botsort", "bytetrack"),
        default="botsort",
        help="Person tracker backend. botsort is the default for 9-camera live operation.",
    )
    parser.add_argument(
        "--tracker-config-path",
        default="",
        help="Optional project-local Ultralytics tracker YAML. Empty uses the backend default.",
    )
    parser.add_argument("--snapshot-dir", default="snapshots/live_topk")
    parser.add_argument(
        "--record-video-mode",
        choices=("full-frame", "person-crop"),
        default="full-frame",
        help="Record full original frames per track, or the older cropped person video.",
    )
    parser.add_argument(
        "--recording-fps",
        type=float,
        default=25.0,
        help="FPS written into recorded mp4 files. Default is 25fps for exhibition playback.",
    )
    parser.add_argument(
        "--recording-stale-frame-seconds",
        type=float,
        default=1.0,
        help="During active recording, reuse the latest captured frame only while it is newer than this age.",
    )
    parser.add_argument(
        "--recording-reconnect-grace-seconds",
        type=float,
        default=3.0,
        help="Keep active recorders open this long while capture is stale, so short RTSP reconnects do not split clips.",
    )
    parser.add_argument(
        "--min-recorded-frames",
        type=int,
        default=0,
        help="Minimum written frames before gallery registration. 0 derives it from --min-clip-seconds and --recording-fps.",
    )
    parser.add_argument(
        "--min-unique-frames",
        type=int,
        default=5,
        help="Minimum distinct source frames before gallery registration, preventing duplicated-frame clips from entering ReID.",
    )
    parser.add_argument("--show-preview", action="store_true", help="Show live annotated camera preview windows.")
    parser.add_argument(
        "--preview-scale",
        type=float,
        default=0.65,
        help="Scale factor for preview windows.",
    )
    parser.add_argument(
        "--preview-reid-crops",
        action="store_true",
        help="Show the latest selected ReID crop when a gallery track is embedded.",
    )
    parser.add_argument(
        "--storage-layout",
        choices=("camera", "similarity"),
        default="camera",
        help="Use camera folders only, or add a similarity-grouped review view for gallery clips.",
    )
    parser.add_argument(
        "--similarity-group-threshold",
        type=float,
        default=0.72,
        help="Cosine threshold for assigning gallery clips to the same temporary appearance group.",
    )
    parser.add_argument(
        "--similarity-export-mode",
        choices=("symlink", "copy", "path"),
        default="symlink",
        help="How to place gallery clips in similarity group folders.",
    )
    parser.add_argument(
        "--similarity-min-frames",
        type=int,
        default=1,
        help="Minimum recorded frames required before a clip is mirrored into a similarity group folder.",
    )
    parser.add_argument(
        "--no-session-end-merge",
        action="store_true",
        help="Skip final session-end regrouping when --storage-layout similarity is active.",
    )
    parser.add_argument(
        "--merge-method",
        choices=("connected", "reciprocal"),
        default="reciprocal",
        help="Final session-end grouping method for similarity_groups_merged.",
    )
    parser.add_argument(
        "--merge-threshold",
        type=float,
        default=0.65,
        help="Cosine threshold for final session-end merged similarity groups.",
    )
    parser.add_argument(
        "--merge-reciprocal-topn",
        type=int,
        default=4,
        help="Mutual top-N neighborhood size for reciprocal final grouping.",
    )
    parser.add_argument(
        "--merge-output-subdir",
        default="similarity_groups_merged",
        help="Subdirectory under snapshots/live_topk/<session> for final merged groups.",
    )
    parser.add_argument("--clip-width", type=int, default=320)
    parser.add_argument("--clip-height", type=int, default=640)
    parser.add_argument("--track-missing-grace", type=int, default=8)
    parser.add_argument(
        "--post-roll-seconds",
        type=float,
        default=2.0,
        help="Keep writing a gallery clip this long after the tracker stops seeing the person.",
    )
    parser.add_argument(
        "--disable-tracklet-stitching",
        action="store_true",
        help="Disable conservative same-person recorder stitching when tracker ids briefly split.",
    )
    parser.add_argument(
        "--stitch-window-seconds",
        type=float,
        default=1.5,
        help="Seconds to keep a missing track eligible for conservative same-person stitching.",
    )
    parser.add_argument(
        "--stitch-reid-threshold",
        type=float,
        default=0.76,
        help="Minimum OSNet cosine similarity required to stitch a new track into a recent recorder.",
    )
    parser.add_argument(
        "--stitch-ambiguous-margin",
        type=float,
        default=0.08,
        help="Required score gap between the best and second-best stitch candidate.",
    )
    parser.add_argument(
        "--stitch-max-center-distance-ratio",
        type=float,
        default=0.35,
        help="Maximum bbox center movement as a ratio of frame diagonal for stitching.",
    )
    parser.add_argument(
        "--stitch-spatial-resume-window-seconds",
        type=float,
        default=1.5,
        help="Allow a lower-score stitch within this gap when bbox continuity is extremely strong.",
    )
    parser.add_argument(
        "--stitch-spatial-resume-max-distance-ratio",
        type=float,
        default=0.02,
        help="BBox center distance for strong spatial-continuity stitching.",
    )
    parser.add_argument(
        "--stitch-spatial-resume-min-score",
        type=float,
        default=0.55,
        help="Minimum ReID score for strong spatial-continuity stitching.",
    )
    parser.add_argument(
        "--stitch-micro-gap-seconds",
        type=float,
        default=0.35,
        help="Allow a very short track-id split to stitch with a lower ReID score when not crowded.",
    )
    parser.add_argument(
        "--stitch-micro-gap-max-distance-ratio",
        type=float,
        default=0.06,
        help="BBox center distance for very short track-id split stitching.",
    )
    parser.add_argument(
        "--stitch-micro-gap-min-score",
        type=float,
        default=0.35,
        help="Minimum ReID score for very short track-id split stitching.",
    )
    parser.add_argument(
        "--stitch-crowded-window-seconds",
        type=float,
        default=2.0,
        help="Reject stitching for this long after multi-person/overlap frames unless crowded stitching is allowed.",
    )
    parser.add_argument(
        "--stitch-crowded-near-distance-ratio",
        type=float,
        default=0.08,
        help=(
            "Allow stitching through a recent crowded/duplicate-detection window when bbox centers are this close. "
            "This keeps single-person duplicate boxes from splitting clips."
        ),
    )
    parser.add_argument(
        "--disable-duplicate-track-suppression",
        action="store_true",
        help="Disable low-quality duplicate person-track suppression before starting a new recorder.",
    )
    parser.add_argument(
        "--duplicate-absorb-reid-threshold",
        type=float,
        default=0.76,
        help="Minimum prototype ReID score for absorbing a simultaneous duplicate track into an active recorder.",
    )
    parser.add_argument(
        "--duplicate-absorb-max-center-distance-ratio",
        type=float,
        default=0.12,
        help="Maximum bbox center distance for duplicate track absorption.",
    )
    parser.add_argument(
        "--duplicate-absorb-min-iou",
        type=float,
        default=0.50,
        help="IoU threshold for geometry-only duplicate track absorption.",
    )
    parser.add_argument(
        "--duplicate-absorb-min-containment",
        type=float,
        default=0.85,
        help="Intersection-over-smaller-box threshold for duplicate track absorption.",
    )
    parser.add_argument(
        "--duplicate-absorb-low-quality-max",
        type=float,
        default=0.45,
        help="Max crop quality for low-quality duplicate absorption by geometry.",
    )
    parser.add_argument(
        "--duplicate-absorb-low-quality-distance-ratio",
        type=float,
        default=0.08,
        help="Center-distance threshold for low-quality duplicate absorption.",
    )
    parser.add_argument(
        "--duplicate-track-max-quality",
        type=float,
        default=0.45,
        help="Only suppress a new duplicate-looking track when its crop quality is at or below this value.",
    )
    parser.add_argument(
        "--duplicate-track-min-iou",
        type=float,
        default=0.12,
        help="Suppress low-quality duplicate tracks when they overlap an active track by at least this IoU.",
    )
    parser.add_argument(
        "--duplicate-track-max-center-distance-ratio",
        type=float,
        default=0.10,
        help="Suppress low-quality duplicate tracks when centers are this close to an active track.",
    )
    parser.add_argument(
        "--stitch-allow-crowded",
        action="store_true",
        help="Allow stitching even after recent crowded frames. Default is conservative rejection.",
    )
    parser.add_argument(
        "--min-clip-seconds",
        type=float,
        default=1.5,
        help=(
            "Closed gallery clips with encoded playback duration shorter than this are kept on disk "
            "but not added to the ReID gallery."
        ),
    )
    parser.add_argument(
        "--min-gallery-crop-quality",
        type=float,
        default=0.45,
        help=(
            "Closed clips with best ReID crop quality below this are kept in _discarded "
            "instead of being registered in the Top-K gallery."
        ),
    )
    parser.add_argument(
        "--max-clip-seconds",
        type=float,
        default=30.0,
        help="Safety cutoff for a single person track clip; disappearance still ends clips earlier.",
    )
    parser.add_argument("--reconnect-delay", type=float, default=2.0)
    parser.add_argument("--max-read-failures", type=int, default=10)
    parser.add_argument(
        "--rtsp-open-timeout-ms",
        type=int,
        default=5000,
        help="OpenCV/FFmpeg RTSP open timeout. Lower values keep failed cameras from starving recorder threads.",
    )
    parser.add_argument(
        "--rtsp-read-timeout-ms",
        type=int,
        default=5000,
        help="OpenCV/FFmpeg RTSP read timeout.",
    )
    parser.add_argument(
        "--max-open-retry-delay",
        type=float,
        default=30.0,
        help="Maximum exponential backoff delay after a camera open failure.",
    )
    parser.add_argument("--query-interval-seconds", type=float, default=1.0)
    parser.add_argument("--topk", type=int, default=7)
    parser.add_argument("--candidate-pool", type=int, default=12)
    parser.add_argument(
        "--live-visual-top-n",
        type=int,
        default=6,
        help="Number of diverse live person crops to store as gallery tracklet prototypes.",
    )
    parser.add_argument(
        "--crop-selection-strategy",
        choices=("diverse-quality", "quality-only"),
        default="diverse-quality",
        help="How to select best ReID crops from a clip or live tracklet.",
    )
    parser.add_argument(
        "--prototype-score-mode",
        choices=("max", "top2-mean", "mean"),
        default="max",
        help="How query/gallery and similarity grouping compare crop prototype embeddings.",
    )
    parser.add_argument(
        "--crop-diversity-min-frame-gap",
        type=int,
        default=15,
        help="Preferred minimum source-frame gap between selected diverse crops.",
    )
    parser.add_argument(
        "--crop-diversity-max-similarity",
        type=float,
        default=0.92,
        help="Color-histogram similarity above which nearby crop candidates are considered duplicate-like.",
    )
    parser.add_argument(
        "--crop-min-quality-ratio",
        type=float,
        default=0.70,
        help="Minimum quality ratio to the best crop before a candidate is considered for diversity selection.",
    )
    parser.add_argument(
        "--embedding-model",
        choices=("osnet_x0_25", "mobilenet_v3_large", "mobilenet_v3_small", "efficientnet_b0", "hsv_histogram"),
        default="osnet_x0_25",
        help="Appearance embedding backend for ReID ranking and similarity grouping.",
    )
    parser.add_argument(
        "--skip-webcam-preflight",
        action="store_true",
        help="Skip the main-thread webcam open/release used to trigger macOS camera authorization.",
    )
    parser.add_argument("--export-topk-dir", default="", help="Optional directory for query-by-query Top-K exports.")
    parser.add_argument(
        "--export-mode",
        choices=("symlink", "copy", "path"),
        default="symlink",
        help="How to place selected clips in the Top-K export folder.",
    )
    parser.add_argument(
        "--fallback-score",
        type=float,
        default=0.55,
        help="Results below this cosine score are still returned but marked as fallback.",
    )
    parser.add_argument(
        "--max-runtime-seconds",
        type=float,
        default=0.0,
        help="Optional smoke-test timeout. 0 means run until interrupted.",
    )
    return parser.parse_args()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    resolved = path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"Path must stay inside project root: {resolved}") from exc
    return resolved


def display_project_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def resolve_tracker_config_path(tracker_backend: str, tracker_config_path: str = "") -> Path | None:
    normalized = str(tracker_backend or "").strip().lower()
    if tracker_config_path:
        return resolve_project_path(tracker_config_path)
    if normalized in {"botsort", "bytetrack"}:
        candidate = PROJECT_ROOT / "config" / "trackers" / f"{normalized}.yaml"
        if candidate.is_file():
            return candidate.resolve()
    return None


def tracker_config_with_reid(config_path: Path | None) -> bool | None:
    if config_path is None or not config_path.is_file():
        return None
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip() != "with_reid":
            continue
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return None


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def split_sources(rtsp_arg: str, rtsp_envs_arg: str = "") -> list[str]:
    sources: list[str] = []
    for env_name in split_csv(rtsp_envs_arg):
        env_value = os.environ.get(env_name)
        if not env_value:
            raise ValueError(f"RTSP environment variable is empty or missing: {env_name}")
        sources.append(env_value.strip())

    sources.extend(split_csv(rtsp_arg))
    if not sources:
        raise ValueError("No video sources were provided. Use --rtsp-envs and/or --rtsp.")
    return sources


def normalize_cam_type(cam_type: str) -> str:
    normalized = str(cam_type or "G").strip().upper()
    if normalized in QUERY_TYPES:
        return "Q"
    if normalized in GALLERY_TYPES:
        return "G"
    raise ValueError(f"Unsupported cam type '{cam_type}'. Use G/A/B for gallery or Q/C for query.")


def split_cam_types(cam_types_arg: str, camera_count: int) -> list[str]:
    if not cam_types_arg.strip():
        return ["G"] * camera_count

    cam_types = [normalize_cam_type(item) for item in split_csv(cam_types_arg)]
    if len(cam_types) != camera_count:
        raise ValueError(f"--cam-types count ({len(cam_types)}) must match source count ({camera_count}).")
    return cam_types


def split_cam_labels(cam_labels_arg: str, camera_count: int) -> list[str]:
    if not cam_labels_arg.strip():
        return [f"cam_{index}" for index in range(1, camera_count + 1)]
    labels = [sanitize_id(item) for item in split_csv(cam_labels_arg)]
    if len(labels) != camera_count:
        raise ValueError(f"--cam-labels count ({len(labels)}) must match source count ({camera_count}).")
    if len(set(labels)) != len(labels):
        raise ValueError("--cam-labels values must be unique.")
    return labels


def parse_video_source(source: str) -> dict[str, object]:
    normalized = source.strip()
    lower_source = normalized.lower()

    for prefix in ("webcam:", "usb:", "camera:"):
        if lower_source.startswith(prefix):
            camera_id_text = normalized.split(":", 1)[1].strip()
            if not camera_id_text:
                raise ValueError(f"Missing camera id in source '{source}'. Use webcam:0, webcam:1, ...")
            camera_id = int(camera_id_text)
            return {"kind": "webcam", "capture_source": camera_id, "display": f"webcam:{camera_id}"}

    if lower_source.isdigit():
        camera_id = int(lower_source)
        return {"kind": "webcam", "capture_source": camera_id, "display": f"webcam:{camera_id}"}

    parsed = urlparse(normalized)
    if parsed.scheme.lower() == "rtsp":
        return {"kind": "rtsp", "capture_source": normalized, "display": redact_source(normalized)}

    return {"kind": "video", "capture_source": normalized, "display": normalized}


def redact_source(source: str) -> str:
    parsed = urlparse(source)
    if parsed.password is None:
        return source
    username = parsed.username or ""
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{username}:***@{host}{port}" if username else f"***@{host}{port}"
    return parsed._replace(netloc=netloc).geturl()


def create_capture(
    video_source: str,
    frame_width: int,
    frame_height: int,
    requested_fps: float = 25.0,
    open_timeout_ms: int = 5000,
    read_timeout_ms: int = 5000,
) -> cv2.VideoCapture:
    source_info = parse_video_source(video_source)
    if source_info["kind"] == "webcam":
        if sys.platform == "darwin":
            backend = cv2.CAP_AVFOUNDATION
        elif sys.platform == "win32":
            backend = cv2.CAP_DSHOW
        elif sys.platform.startswith("linux"):
            backend = cv2.CAP_V4L2
        else:
            backend = 0
        cap = cv2.VideoCapture(source_info["capture_source"], backend)
        if not cap.isOpened():
            cap = cv2.VideoCapture(source_info["capture_source"])
        cap.set(cv2.CAP_PROP_FPS, max(1.0, float(requested_fps)))
    else:
        params = []
        if hasattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC"):
            params.extend([cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, max(1000, int(open_timeout_ms))])
        if hasattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC"):
            params.extend([cv2.CAP_PROP_READ_TIMEOUT_MSEC, max(1000, int(read_timeout_ms))])
        try:
            cap = cv2.VideoCapture(source_info["capture_source"], cv2.CAP_FFMPEG, params)
        except cv2.error:
            cap = cv2.VideoCapture()
            if hasattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC"):
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, max(1000, int(open_timeout_ms)))
            if hasattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC"):
                cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, max(1000, int(read_timeout_ms)))
            cap.open(source_info["capture_source"], cv2.CAP_FFMPEG)
        if not cap.isOpened() and source_info["kind"] != "rtsp":
            cap = cv2.VideoCapture(source_info["capture_source"])

    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def preflight_webcams(sources: list[str], frame_width: int, frame_height: int, requested_fps: float) -> None:
    for source in sources:
        source_info = parse_video_source(source)
        if source_info["kind"] != "webcam":
            continue
        print(f"[preflight] Opening {source_info['display']} on main thread for camera authorization.")
        cap = create_capture(source, frame_width, frame_height, requested_fps)
        if not cap.isOpened():
            print(
                f"[preflight] Could not open {source_info['display']}. "
                "If macOS asks for camera access, allow it and rerun."
            )
        else:
            ok, _frame = cap.read()
            print(f"[preflight] {source_info['display']} opened; first_read={bool(ok)}")
        cap.release()


def create_clip_writer(clip_path: Path, fps: float, frame_size: tuple[int, int]):
    clip_path.parent.mkdir(parents=True, exist_ok=True)
    for codec in ("mp4v", "avc1", "H264", "MJPG"):
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(str(clip_path), fourcc, fps, frame_size)
        if writer.isOpened():
            return writer, codec
        writer.release()
    return None, None


def normalize_vector(vector: np.ndarray | None) -> np.ndarray | None:
    if vector is None:
        return None
    array = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(array))
    if norm <= 1e-8:
        return None
    return array / norm


def sanitize_id(value: object) -> str:
    text = str(value)
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return text.strip("_") or "unknown"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def compact_event_token(event_id: object, digits: int = 6) -> str:
    text = re.sub(r"\D+", "", str(event_id))
    if not text:
        return "e000000"
    return f"e{text[-max(1, int(digits)):]}"


def box_center(box: Iterable[float]) -> tuple[float, float]:
    x1, y1, x2, y2 = [float(value) for value in box]
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def box_iou(box_a: Iterable[float], box_b: Iterable[float]) -> float:
    ax1, ay1, ax2, ay2 = [float(value) for value in box_a]
    bx1, by1, bx2, by2 = [float(value) for value in box_b]
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection
    if union <= 1e-8:
        return 0.0
    return float(intersection / union)


def box_intersection_over_min_area(box_a: Iterable[float], box_b: Iterable[float]) -> float:
    ax1, ay1, ax2, ay2 = [float(value) for value in box_a]
    bx1, by1, bx2, by2 = [float(value) for value in box_b]
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    min_area = max(1e-8, min(area_a, area_b))
    return float(intersection / min_area)


def box_center_distance_ratio(
    box_a: Iterable[float],
    box_b: Iterable[float],
    frame_shape: tuple[int, ...],
) -> float:
    ax, ay = box_center(box_a)
    bx, by = box_center(box_b)
    height = float(frame_shape[0]) if frame_shape else 1.0
    width = float(frame_shape[1]) if len(frame_shape) > 1 else 1.0
    diagonal = max(1.0, math.sqrt((width * width) + (height * height)))
    return float(math.sqrt(((ax - bx) ** 2) + ((ay - by) ** 2)) / diagonal)


def has_crowded_overlap(people: list[dict[str, object]], iou_threshold: float = 0.03) -> bool:
    if len(people) < 2:
        return False
    return True


def source_is_finite_video(source_info: dict[str, object]) -> bool:
    return str(source_info.get("kind") or "") == "video"


def video_source_frame_interval(source_info: dict[str, object], requested_fps: float) -> float:
    if not source_is_finite_video(source_info):
        return 0.0
    fps = max(1.0, float(requested_fps))
    return 1.0 / fps


def sleep_for_finite_video_frame(next_frame_at: float, interval: float, stop_event: threading.Event) -> float:
    if interval <= 0:
        return next_frame_at
    next_frame_at = max(next_frame_at + interval, time.monotonic())
    while not stop_event.is_set():
        delay = next_frame_at - time.monotonic()
        if delay <= 0:
            break
        time.sleep(min(0.02, delay))
    return next_frame_at


def should_allow_crowded_stitch_by_geometry(
    candidates: list[tuple[str, int, "PersonClipRecorder", float, tuple[int, ...]]],
    person: dict[str, object],
    frame_shape: tuple[int, ...],
    max_distance_ratio: float,
) -> bool:
    if not candidates:
        return False
    nearest = min(
        box_center_distance_ratio(old_box, person["box"], frame_shape)
        for _source, _old_track_id, _recorder, _time_gap, old_box in candidates
    )
    return nearest <= max(0.0, float(max_distance_ratio))


def spatial_continuity_stitch_reason(
    score: float,
    time_gap_seconds: float,
    center_distance_ratio: float,
    args: argparse.Namespace,
    crowded_recent: bool,
) -> str:
    if crowded_recent:
        return ""
    score_value = float(score)
    time_gap = float(time_gap_seconds)
    distance = float(center_distance_ratio)

    if (
        time_gap <= float(getattr(args, "stitch_spatial_resume_window_seconds", 1.5))
        and distance <= float(getattr(args, "stitch_spatial_resume_max_distance_ratio", 0.02))
        and score_value >= float(getattr(args, "stitch_spatial_resume_min_score", 0.55))
    ):
        return "spatial_continuity_stitched"

    if (
        time_gap <= float(getattr(args, "stitch_micro_gap_seconds", 0.35))
        and distance <= float(getattr(args, "stitch_micro_gap_max_distance_ratio", 0.06))
        and score_value >= float(getattr(args, "stitch_micro_gap_min_score", 0.35))
    ):
        return "micro_gap_spatial_stitched"
    return ""


@dataclass
class PendingStitchRecorder:
    recorder: "PersonClipRecorder"
    pending_since: float
    expires_at: float
    close_reason: str


@dataclass
class StitchDecision:
    accepted: bool
    reason: str
    old_track_id: int
    new_track_id: int
    source: str = ""
    score: float = 0.0
    second_score: float = 0.0
    center_distance_ratio: float = 0.0
    time_gap_seconds: float = 0.0
    embedding_method: str = ""

    def to_json(self) -> dict[str, object]:
        return {
            "accepted": bool(self.accepted),
            "reason": self.reason,
            "old_track_id": int(self.old_track_id),
            "new_track_id": int(self.new_track_id),
            "source": self.source,
            "score": round(float(self.score), 6),
            "second_score": round(float(self.second_score), 6),
            "center_distance_ratio": round(float(self.center_distance_ratio), 6),
            "time_gap_seconds": round(float(self.time_gap_seconds), 3),
            "embedding_method": self.embedding_method,
        }


def export_asset(source_path: str, destination: Path, mode: str, path_txt_name: str) -> str:
    if not str(source_path or "").strip():
        destination.parent.mkdir(parents=True, exist_ok=True)
        path_txt = destination.parent / path_txt_name
        path_txt.write_text("", encoding="utf-8")
        return str(path_txt.resolve()).replace("\\", "/")

    source = Path(str(source_path)).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    path_txt = destination.parent / path_txt_name
    path_txt.write_text(str(source), encoding="utf-8")

    if mode == "path":
        return str(path_txt.resolve()).replace("\\", "/")
    if not source.exists():
        return str(path_txt.resolve()).replace("\\", "/")

    if destination.exists() or destination.is_symlink():
        destination.unlink()

    if mode == "copy":
        shutil.copy2(source, destination)
    else:
        try:
            relative_source = os.path.relpath(source.resolve(), start=destination.parent.resolve())
            destination.symlink_to(relative_source)
        except OSError:
            shutil.copy2(source, destination)
    return str((destination.parent.resolve() / destination.name)).replace("\\", "/")


def export_similarity_group_record(
    record: GalleryRecord,
    snapshot_root: Path,
    session_id: str,
    export_mode: str,
) -> str:
    if not record.similarity_group_label:
        return ""

    group_dir = (
        snapshot_root
        / sanitize_id(session_id)
        / "similarity_groups"
        / sanitize_id(record.similarity_group_label)
    )
    group_dir.mkdir(parents=True, exist_ok=True)
    safe_clip_id = sanitize_id(record.clip_id)

    clip_suffix = Path(record.clip_path).suffix or ".mp4"
    best_suffix = Path(record.best_frame_path).suffix or ".jpg"
    exported_clip = export_asset(
        record.clip_path,
        group_dir / f"{safe_clip_id}{clip_suffix}",
        export_mode,
        f"{safe_clip_id}_clip_path.txt",
    )
    exported_best = export_asset(
        record.best_frame_path,
        group_dir / f"{safe_clip_id}_best{best_suffix}",
        export_mode,
        f"{safe_clip_id}_best_path.txt",
    )

    metadata = record.to_json()
    metadata.update({"exported_clip": exported_clip, "exported_best_frame": exported_best})
    write_json(group_dir / f"{safe_clip_id}.json", metadata)
    return str(group_dir.resolve()).replace("\\", "/")


def crop_person(frame: np.ndarray, box: Iterable[int], expand_ratio: float = 0.08) -> np.ndarray | None:
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in box]
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    pad_x = int(box_w * expand_ratio)
    pad_y = int(box_h * expand_ratio)
    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)
    x2 = min(width, x2 + pad_x)
    y2 = min(height, y2 + pad_y)
    if x2 <= x1 or y2 <= y1:
        return None
    crop = frame[y1:y2, x1:x2]
    return crop.copy() if crop.size else None


def resize_with_padding(image: np.ndarray, output_size: tuple[int, int]) -> np.ndarray:
    target_w, target_h = output_size
    height, width = image.shape[:2]
    if width <= 0 or height <= 0:
        return np.zeros((target_h, target_w, 3), dtype=np.uint8)

    scale = min(float(target_w) / float(width), float(target_h) / float(height))
    resized_w = max(1, int(round(width * scale)))
    resized_h = max(1, int(round(height * scale)))
    resized = cv2.resize(image, (resized_w, resized_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    offset_x = (target_w - resized_w) // 2
    offset_y = (target_h - resized_h) // 2
    canvas[offset_y : offset_y + resized_h, offset_x : offset_x + resized_w] = resized
    return canvas


def resize_frame_if_needed(frame: np.ndarray, output_size: tuple[int, int]) -> np.ndarray:
    target_w, target_h = output_size
    height, width = frame.shape[:2]
    if (width, height) == (target_w, target_h):
        return frame
    return cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)


def draw_analysis_overlay(
    frame: np.ndarray,
    people: list[dict[str, object]],
    cam_id: int,
    cam_label: str,
    role: str,
    gallery_count: int,
    active_recordings: int,
    inference_ms: float,
) -> np.ndarray:
    preview = frame.copy()
    for person in people:
        x1, y1, x2, y2 = [int(value) for value in person.get("box", (0, 0, 0, 0))]
        track_id = int(person.get("track_id", 0))
        confidence = float(person.get("confidence", 0.0))
        color = (40, 220, 80) if role == "G" else (70, 170, 255)
        cv2.rectangle(preview, (x1, y1), (x2, y2), color, 2)
        label = f"id {track_id} conf {confidence:.2f}"
        cv2.putText(preview, label, (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    status = (
        f"cam_{cam_id} {cam_label} role={role} people={len(people)} "
        f"recording={active_recordings} gallery={gallery_count} yolo={inference_ms:.1f}ms"
    )
    cv2.rectangle(preview, (0, 0), (preview.shape[1], 34), (0, 0, 0), -1)
    cv2.putText(preview, status, (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
    return preview


def enqueue_preview_window(window_name: str, frame: np.ndarray, scale: float) -> None:
    if PREVIEW_DISABLED:
        return
    try:
        PREVIEW_QUEUE.put_nowait((window_name, frame.copy(), scale))
    except queue.Full:
        try:
            PREVIEW_QUEUE.get_nowait()
        except queue.Empty:
            pass
        try:
            PREVIEW_QUEUE.put_nowait((window_name, frame.copy(), scale))
        except queue.Full:
            pass


def render_preview_window(window_name: str, frame: np.ndarray, scale: float) -> int:
    display = frame
    if scale > 0 and abs(scale - 1.0) > 1e-3:
        width = max(1, int(round(frame.shape[1] * scale)))
        height = max(1, int(round(frame.shape[0] * scale)))
        display = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
    cv2.imshow(window_name, display)
    return cv2.waitKey(1) & 0xFF


def process_preview_events() -> bool:
    global PREVIEW_DISABLED, PREVIEW_ERROR_REPORTED
    if PREVIEW_DISABLED:
        return False
    should_stop = False
    with PREVIEW_LOCK:
        while True:
            try:
                window_name, frame, scale = PREVIEW_QUEUE.get_nowait()
            except queue.Empty:
                break
            try:
                key = render_preview_window(window_name, frame, scale)
            except cv2.error as exc:
                PREVIEW_DISABLED = True
                if not PREVIEW_ERROR_REPORTED:
                    print(f"[preview] OpenCV window preview disabled: {exc}")
                    PREVIEW_ERROR_REPORTED = True
                break
            if key in (ord("q"), 27):
                should_stop = True
    return should_stop


def crop_quality(crop: np.ndarray | None, person: dict[str, object]) -> float:
    if crop is None or crop.size == 0:
        return 0.0
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    sharpness = min(1.0, float(cv2.Laplacian(gray, cv2.CV_64F).var()) / 900.0)
    crop_area = float(crop.shape[0] * crop.shape[1])
    area_score = min(1.0, crop_area / float(260 * 520))
    confidence = min(1.0, max(0.0, float(person.get("confidence", 0.0))))
    return (confidence * 0.45) + (sharpness * 0.30) + (area_score * 0.25)


class AppearanceEmbedder:
    def __init__(self, model_name: str = "osnet_x0_25", cache_root: Path | None = None):
        self.delegate = create_visual_embedder(
            model_name=model_name,
            cache_root=cache_root,
            color_weight=0.20,
        )

    @property
    def method(self) -> str:
        return str(getattr(self.delegate, "method", "unknown"))

    @property
    def device(self) -> str:
        return str(getattr(self.delegate, "device", "unknown"))

    def embed_bgr(self, image_bgr: np.ndarray | None) -> tuple[np.ndarray | None, str]:
        return self.delegate.embed_bgr(image_bgr)


def normalize_embedding_matrix(embeddings: object) -> np.ndarray | None:
    if embeddings is None:
        return None
    array = np.asarray(embeddings, dtype=np.float32)
    if array.size == 0:
        return None
    if array.ndim == 1:
        normalized = normalize_vector(array)
        return None if normalized is None else normalized.reshape(1, -1)
    rows = []
    for row in array:
        normalized = normalize_vector(row)
        if normalized is not None:
            rows.append(normalized)
    if not rows:
        return None
    return np.vstack(rows).astype(np.float32)


def prototype_similarity(
    query_embedding: np.ndarray | None,
    record_embedding: np.ndarray | None,
    record_prototypes: object = None,
    mode: str = "max",
) -> float:
    query = normalize_vector(query_embedding)
    if query is None:
        return 0.0
    prototypes = normalize_embedding_matrix(record_prototypes)
    normalized_mode = str(mode or "max").strip().lower()
    if prototypes is None:
        record = normalize_vector(record_embedding)
        return 0.0 if record is None else float(np.dot(query, record))
    scores = np.clip(prototypes @ query, -1.0, 1.0)
    if scores.size == 0:
        return 0.0
    if normalized_mode == "mean":
        record = normalize_vector(record_embedding)
        return 0.0 if record is None else float(np.dot(query, record))
    if normalized_mode == "top2-mean" and scores.size >= 2:
        top_scores = np.sort(scores)[-2:]
        return float(np.mean(top_scores))
    return float(np.max(scores))


def prototype_set_similarity(
    left_embedding: np.ndarray | None,
    right_embedding: np.ndarray | None,
    left_prototypes: object = None,
    right_prototypes: object = None,
    mode: str = "max",
) -> float:
    normalized_mode = str(mode or "max").strip().lower()
    if normalized_mode == "mean":
        left = normalize_vector(left_embedding)
        right = normalize_vector(right_embedding)
        return 0.0 if left is None or right is None else float(np.dot(left, right))

    left_matrix = normalize_embedding_matrix(left_prototypes)
    right_matrix = normalize_embedding_matrix(right_prototypes)
    if left_matrix is None:
        left = normalize_vector(left_embedding)
        left_matrix = None if left is None else left.reshape(1, -1)
    if right_matrix is None:
        right = normalize_vector(right_embedding)
        right_matrix = None if right is None else right.reshape(1, -1)
    if left_matrix is None or right_matrix is None:
        return 0.0
    scores = np.clip(left_matrix @ right_matrix.T, -1.0, 1.0).reshape(-1)
    if scores.size == 0:
        return 0.0
    if normalized_mode == "top2-mean" and scores.size >= 2:
        return float(np.mean(np.sort(scores)[-2:]))
    return float(np.max(scores))


@dataclass
class GalleryRecord:
    clip_id: str
    clip_path: str
    best_frame_path: str
    cam_id: str
    cam_label: str
    event_id: str
    track_id: int
    created_at: float
    embedding: np.ndarray
    quality: float
    duration_seconds: float
    frame_count: int
    writer_fps: float
    encoded_duration_seconds: float
    unique_frame_count: int
    duplicate_frame_count: int
    max_frame_age_seconds: float
    embedding_method: str
    recording_interrupted: bool = False
    embedding_aggregation: str = "single_best"
    prototype_embeddings: np.ndarray | None = None
    prototype_score_mode: str = "max"
    prototype_count: int = 0
    crop_selection_strategy: str = "diverse-quality"
    tracker_backend: str = "custom"
    tracker_config_path: str = ""
    tracker_with_reid: bool | None = None
    close_reason: str = ""
    original_track_id: int = 0
    current_track_id: int = 0
    stitched_track_ids: list[int] | None = None
    stitch_events: list[dict[str, object]] | None = None
    absorbed_track_ids: list[int] | None = None
    track_ownership_events: list[dict[str, object]] | None = None
    source_fps: float = 0.0
    analyzed_fps: float = 0.0
    dropped_frame_count: int = 0
    post_roll_seconds: float = 0.0
    top_crop_paths: list[str] | None = None
    best_crop_frame_index: int = 0
    best_crop_box: list[int] | None = None
    best_crop_confidence: float = 0.0
    best_crop_quality: float = 0.0
    top_crop_metadata: list[dict[str, object]] | None = None
    similarity_group_id: int = 0
    similarity_group_label: str = ""
    similarity_group_score: float = 0.0
    similarity_group_count: int = 0
    similarity_group_export_dir: str = ""

    def to_json(self) -> dict[str, object]:
        payload = {
            "clip_id": self.clip_id,
            "clip_path": self.clip_path,
            "best_frame_path": self.best_frame_path,
            "cam_id": self.cam_id,
            "cam_label": self.cam_label,
            "event_id": self.event_id,
            "track_id": self.track_id,
            "created_at": self.created_at,
            "quality": round(float(self.quality), 4),
            "duration_seconds": round(float(self.duration_seconds), 3),
            "frame_count": int(self.frame_count),
            "writer_fps": round(float(self.writer_fps), 3),
            "encoded_duration_seconds": round(float(self.encoded_duration_seconds), 3),
            "unique_frame_count": int(self.unique_frame_count),
            "duplicate_frame_count": int(self.duplicate_frame_count),
            "max_frame_age_seconds": round(float(self.max_frame_age_seconds), 3),
            "recording_interrupted": bool(self.recording_interrupted),
            "embedding_method": self.embedding_method,
            "embedding_aggregation": self.embedding_aggregation,
            "prototype_score_mode": self.prototype_score_mode,
            "prototype_count": int(self.prototype_count or 0),
            "crop_selection_strategy": self.crop_selection_strategy,
            "tracker_backend": self.tracker_backend,
            "close_reason": self.close_reason,
            "original_track_id": int(self.original_track_id or self.track_id),
            "current_track_id": int(self.current_track_id or self.track_id),
            "stitched_track_ids": [int(value) for value in (self.stitched_track_ids or [self.track_id])],
            "stitch_event_count": len(self.stitch_events or []),
            "stitch_events": list(self.stitch_events or []),
            "absorbed_track_ids": [int(value) for value in (self.absorbed_track_ids or [])],
            "track_ownership_event_count": len(self.track_ownership_events or []),
            "track_ownership_events": list(self.track_ownership_events or []),
            "source_fps": round(float(self.source_fps), 3),
            "analyzed_fps": round(float(self.analyzed_fps), 3),
            "dropped_frame_count": int(self.dropped_frame_count),
            "post_roll_seconds": round(float(self.post_roll_seconds), 3),
        }
        if self.tracker_config_path:
            payload["tracker_config_path"] = self.tracker_config_path
        if self.tracker_with_reid is not None:
            payload["tracker_with_reid"] = bool(self.tracker_with_reid)
        if self.top_crop_paths:
            payload["top_crop_paths"] = list(self.top_crop_paths)
        if self.best_crop_box:
            payload["best_crop"] = {
                "track_id": int(self.track_id),
                "frame_index": int(self.best_crop_frame_index),
                "box": [int(value) for value in self.best_crop_box],
                "confidence": round(float(self.best_crop_confidence), 6),
                "quality": round(float(self.best_crop_quality or self.quality), 6),
                "path": self.best_frame_path,
            }
        if self.top_crop_metadata:
            payload["top_crop_metadata"] = list(self.top_crop_metadata)
        if self.similarity_group_label:
            payload.update(
                {
                    "similarity_group_id": int(self.similarity_group_id),
                    "similarity_group_label": self.similarity_group_label,
                    "similarity_group_score": round(float(self.similarity_group_score), 6),
                    "similarity_group_count": int(self.similarity_group_count),
                    "similarity_group_export_dir": self.similarity_group_export_dir,
                }
            )
        return payload


class LiveTopKGallery:
    def __init__(self, log_dir: Path):
        self.lock = threading.Lock()
        self.records: list[GalleryRecord] = []
        self.seen_clip_ids: set[str] = set()
        self.similarity_groups: list[dict[str, object]] = []
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.gallery_log_path = self.log_dir / "gallery_events.jsonl"
        self.query_log_path = self.log_dir / "query_events.jsonl"
        self.legacy_query_log_path = self.log_dir / "query_results.jsonl"

    def add_record(self, record: GalleryRecord) -> bool:
        embedding = normalize_vector(record.embedding)
        if embedding is None:
            return False
        record.embedding = embedding
        prototypes = normalize_embedding_matrix(record.prototype_embeddings)
        if prototypes is not None:
            record.prototype_embeddings = prototypes
            record.prototype_count = int(prototypes.shape[0])
        with self.lock:
            if record.clip_id in self.seen_clip_ids:
                return False
            self.records.append(record)
            self.seen_clip_ids.add(record.clip_id)
        self._append_jsonl(self.gallery_log_path, record.to_json())
        return True

    def assign_similarity_group(self, record: GalleryRecord, threshold: float) -> dict[str, object]:
        embedding = normalize_vector(record.embedding)
        if embedding is None:
            return {"group_id": 0, "group_label": "", "score": 0.0, "count": 0}
        record_prototypes = normalize_embedding_matrix(record.prototype_embeddings)

        with self.lock:
            best_group = None
            best_score = -1.0
            for group in self.similarity_groups:
                centroid = np.asarray(group["centroid"], dtype=np.float32)
                score = prototype_set_similarity(
                    embedding,
                    centroid,
                    record_prototypes,
                    group.get("prototypes"),
                    str(record.prototype_score_mode or "max"),
                )
                if score > best_score:
                    best_score = score
                    best_group = group

            if best_group is None or best_score < float(threshold):
                group_id = len(self.similarity_groups) + 1
                best_group = {
                    "group_id": group_id,
                    "group_label": f"group_{group_id:03d}",
                    "centroid": embedding,
                    "prototypes": record_prototypes if record_prototypes is not None else embedding.reshape(1, -1),
                    "count": 0,
                }
                self.similarity_groups.append(best_group)
                best_score = 1.0

            count = int(best_group["count"]) + 1
            centroid = np.asarray(best_group["centroid"], dtype=np.float32)
            updated_centroid = normalize_vector((centroid * float(best_group["count"])) + embedding)
            best_group["centroid"] = embedding if updated_centroid is None else updated_centroid
            group_prototypes = normalize_embedding_matrix(best_group.get("prototypes"))
            incoming = record_prototypes if record_prototypes is not None else embedding.reshape(1, -1)
            if group_prototypes is None:
                best_group["prototypes"] = incoming
            else:
                merged = np.vstack([group_prototypes, incoming])
                best_group["prototypes"] = merged[:24] if merged.shape[0] > 24 else merged
            best_group["count"] = count

            return {
                "group_id": int(best_group["group_id"]),
                "group_label": str(best_group["group_label"]),
                "score": float(best_score),
                "count": count,
            }

    def rank(self, query_embedding: np.ndarray | None, k: int, candidate_pool: int, fallback_score: float):
        query = normalize_vector(query_embedding)
        if query is None:
            return []
        with self.lock:
            records = list(self.records)
        if not records:
            return []

        scored = []
        for record in records:
            score = prototype_similarity(
                query,
                record.embedding,
                record.prototype_embeddings,
                str(record.prototype_score_mode or "max"),
            )
            scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)

        limit = min(max(k, candidate_pool), len(scored))
        results = []
        for rank, (score, record) in enumerate(scored[:limit], start=1):
            results.append(
                {
                    "rank": rank,
                    "clip_id": record.clip_id,
                    "clip_path": record.clip_path,
                    "best_frame_path": record.best_frame_path,
                    "score": score,
                    "cam_id": record.cam_id,
                    "cam_label": record.cam_label,
                    "event_id": record.event_id,
                    "track_id": record.track_id,
                    "fallback": bool(score < fallback_score),
                    "quality": record.quality,
                    "embedding_aggregation": record.embedding_aggregation,
                    "prototype_score_mode": record.prototype_score_mode,
                    "prototype_count": int(record.prototype_count or 0),
                }
            )
        return results[:k]

    def log_query(self, payload: dict[str, object]) -> None:
        self._append_jsonl(self.query_log_path, payload)
        self._append_jsonl(self.legacy_query_log_path, payload)

    def count(self) -> int:
        with self.lock:
            return len(self.records)

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


class PersonClipRecorder:
    def __init__(
        self,
        session_id: str,
        snapshot_root: Path,
        cam_id: int,
        cam_label: str,
        track_id: int,
        output_size: tuple[int, int],
        fps: float,
        record_video_mode: str,
        top_n: int = 1,
        selection_strategy: str = "diverse-quality",
        diversity_min_frame_gap: int = 15,
        diversity_max_similarity: float = 0.92,
        crop_min_quality_ratio: float = 0.70,
        prototype_score_mode: str = "max",
    ):
        event_id = str(int(time.time() * 1000))
        safe_session = sanitize_id(session_id)
        safe_cam = f"cam_{cam_id}"
        safe_cam_label = sanitize_id(cam_label) or safe_cam
        event_token = compact_event_token(event_id)
        clip_id = f"live_{safe_session}_{safe_cam_label}_t{int(track_id):03d}_{event_token}"
        clip_dir = snapshot_root / safe_session / safe_cam_label
        self.clip_id = clip_id
        self.event_id = event_id
        self.cam_id = safe_cam
        self.cam_label = safe_cam_label
        self.track_id = int(track_id)
        self.original_track_id = int(track_id)
        self.current_track_id = int(track_id)
        self.owned_track_ids = {int(track_id)}
        self.absorbed_track_ids: list[int] = []
        self.track_ownership_events: list[dict[str, object]] = []
        self.stitched_track_ids = [int(track_id)]
        self.stitch_events: list[dict[str, object]] = []
        self.clip_path = clip_dir / f"{clip_id}.mp4"
        self.best_frame_path = clip_dir / f"{clip_id}_best.jpg"
        self.output_size = output_size
        self.record_video_mode = record_video_mode
        self.top_n = max(1, int(top_n))
        self.selection_strategy = str(selection_strategy or "diverse-quality")
        self.diversity_min_frame_gap = int(diversity_min_frame_gap)
        self.diversity_max_similarity = float(diversity_max_similarity)
        self.crop_min_quality_ratio = float(crop_min_quality_ratio)
        self.prototype_score_mode = str(prototype_score_mode or "max")
        self.candidate_pool_limit = max(30, self.top_n * 12)
        self.fps = max(1.0, float(fps))
        self.writer, self.codec = create_clip_writer(self.clip_path, self.fps, output_size)
        self.started_at = time.monotonic()
        self.created_at = time.time()
        self.last_observed_at = self.started_at
        self.missing_since: float | None = None
        self.last_box = None
        self.last_person: dict[str, object] | None = None
        self.missing_analyses = 0
        self.frame_count = 0
        self.unique_frame_count = 0
        self.duplicate_frame_count = 0
        self.last_written_source_frame_index = 0
        self.max_frame_age_seconds = 0.0
        self.recording_interrupted = False
        self.best_crop = None
        self.best_quality = -1.0
        self.best_candidate_metadata: dict[str, object] | None = None
        self.crop_candidates: list[dict[str, object]] = []
        self._stitch_embedding: np.ndarray | None = None
        self._stitch_embedding_method = ""
        self._stitch_embedding_signature: tuple[object, ...] | None = None
        self._stitch_prototype_embeddings: np.ndarray | None = None
        self._stitch_prototype_method = ""
        self._stitch_prototype_signature: tuple[object, ...] | None = None
        self.closed = False
        if self.writer is None:
            print(f"[gallery] Failed to open clip writer: {self.clip_path}")
        else:
            print(f"[gallery] Recording track {track_id} with {self.codec} {self.fps:.1f}fps: {self.clip_path}")

    def discard_clip(self, reason: str, details: dict[str, object] | None = None) -> None:
        if not self.clip_path.parent.exists():
            return
        discard_dir = self.clip_path.parent.parent / "_discarded" / self.cam_label
        discard_dir.mkdir(parents=True, exist_ok=True)
        moved_paths = []
        for source in sorted(self.clip_path.parent.glob(f"{self.clip_id}*")):
            destination = discard_dir / source.name
            if destination.exists() or destination.is_symlink():
                destination.unlink()
            shutil.move(str(source), str(destination))
            moved_paths.append(str(destination.resolve()).replace("\\", "/"))
            if source == self.clip_path:
                self.clip_path = destination
        payload = {
            "clip_id": self.clip_id,
            "cam_id": self.cam_id,
            "cam_label": self.cam_label,
            "track_id": int(self.track_id),
            "original_track_id": int(self.original_track_id),
            "current_track_id": int(self.current_track_id),
            "stitched_track_ids": [int(value) for value in self.stitched_track_ids],
            "owned_track_ids": sorted(int(value) for value in self.owned_track_ids),
            "absorbed_track_ids": [int(value) for value in self.absorbed_track_ids],
            "track_ownership_events": list(self.track_ownership_events),
            "reason": str(reason),
            "details": details or {},
            "moved_paths": moved_paths,
        }
        write_json(discard_dir / f"{self.clip_id}_discard.json", payload)
        print(f"[gallery] Moved invalid clip to _discarded reason={reason}: {self.clip_id}")

    def observe(self, frame: np.ndarray, person: dict[str, object], frame_index: int = 0) -> None:
        person_track_id = int(person.get("track_id", self.current_track_id) or self.current_track_id)
        if person_track_id > 0:
            self.owned_track_ids.add(person_track_id)
            self.current_track_id = person_track_id
            self.track_id = person_track_id
        self.last_box = tuple(int(value) for value in person["box"])
        self.last_person = person
        self.last_observed_at = time.monotonic()
        self.missing_since = None
        self.missing_analyses = 0
        crop = visual_crop_person(frame, self.last_box)
        quality = visual_crop_quality(crop, person, frame.shape)
        if crop is not None:
            self.crop_candidates.append(make_crop_candidate(frame_index, crop, person, frame.shape, quality))
            self.crop_candidates.sort(key=lambda item: float(item["quality"]), reverse=True)
            self.crop_candidates = self.crop_candidates[: self.candidate_pool_limit]
            best = self.crop_candidates[0]
            self.best_crop = best["crop"]
            self.best_quality = float(best["quality"])
            self.best_candidate_metadata = {
                "frame_index": int(best["frame_index"]),
                "box": [int(value) for value in best["box"]],
                "confidence": float(best["confidence"]),
                "quality": float(best["quality"]),
            }
            self._stitch_embedding = None
            self._stitch_embedding_method = ""
            self._stitch_embedding_signature = None
            self._stitch_prototype_embeddings = None
            self._stitch_prototype_method = ""
            self._stitch_prototype_signature = None

    def stitch_signature(self) -> tuple[object, ...] | None:
        if not self.best_candidate_metadata:
            return None
        return (
            int(self.best_candidate_metadata.get("frame_index") or 0),
            tuple(int(value) for value in self.best_candidate_metadata.get("box") or []),
            round(float(self.best_candidate_metadata.get("quality") or 0.0), 6),
        )

    def stitch_embedding(self, embedder: AppearanceEmbedder) -> tuple[np.ndarray | None, str]:
        if self.best_crop is None:
            return None, ""
        signature = self.stitch_signature()
        if self._stitch_embedding is not None and self._stitch_embedding_signature == signature:
            return self._stitch_embedding, self._stitch_embedding_method
        embedding, method = embedder.embed_bgr(self.best_crop)
        normalized = normalize_vector(embedding)
        self._stitch_embedding = normalized
        self._stitch_embedding_method = method
        self._stitch_embedding_signature = signature
        return normalized, method

    def stitch_prototype_embeddings(self, embedder: AppearanceEmbedder) -> tuple[np.ndarray | None, str]:
        selected = select_diverse_crop_candidates(
            self.crop_candidates,
            top_n=self.top_n,
            selection_strategy=self.selection_strategy,
            min_frame_gap=self.diversity_min_frame_gap,
            max_similarity=self.diversity_max_similarity,
            min_quality_ratio=self.crop_min_quality_ratio,
        )
        signature = tuple(
            (
                int(candidate.get("frame_index") or 0),
                tuple(int(value) for value in candidate.get("box") or []),
                round(float(candidate.get("quality") or 0.0), 6),
            )
            for candidate in selected
        )
        if (
            self._stitch_prototype_embeddings is not None
            and self._stitch_prototype_signature == signature
        ):
            return self._stitch_prototype_embeddings, self._stitch_prototype_method

        embeddings = []
        methods = []
        for candidate in selected:
            embedding, method = embedder.embed_bgr(candidate.get("crop"))
            normalized = normalize_vector(embedding)
            if normalized is not None:
                embeddings.append(normalized)
                methods.append(method)
        if not embeddings:
            embedding, method = self.stitch_embedding(embedder)
            if embedding is None:
                return None, method
            embeddings.append(embedding)
            methods.append(method)

        prototypes = np.vstack(embeddings).astype(np.float32)
        self._stitch_prototype_embeddings = prototypes
        self._stitch_prototype_method = methods[-1] if methods else embedder.method
        self._stitch_prototype_signature = signature
        return prototypes, self._stitch_prototype_method

    def reassign_track_id(self, new_track_id: int, stitch_event: dict[str, object]) -> None:
        self.track_id = int(new_track_id)
        self.current_track_id = int(new_track_id)
        self.owned_track_ids.add(int(new_track_id))
        if int(new_track_id) not in self.stitched_track_ids:
            self.stitched_track_ids.append(int(new_track_id))
        self.stitch_events.append(dict(stitch_event))

    def absorb_track_id(self, new_track_id: int, ownership_event: dict[str, object]) -> None:
        new_track_id = int(new_track_id)
        self.track_id = new_track_id
        self.current_track_id = new_track_id
        self.owned_track_ids.add(new_track_id)
        if new_track_id not in self.absorbed_track_ids:
            self.absorbed_track_ids.append(new_track_id)
        if new_track_id not in self.stitched_track_ids:
            self.stitched_track_ids.append(new_track_id)
        self.track_ownership_events.append(dict(ownership_event))

    def mark_missing(self, now: float | None = None) -> None:
        self.missing_analyses += 1
        if self.missing_since is None:
            self.missing_since = time.monotonic() if now is None else float(now)

    def should_close_after_missing(self, post_roll_seconds: float, track_missing_grace: int) -> bool:
        if self.missing_since is None:
            return False
        now = time.monotonic()
        if post_roll_seconds >= 0:
            return (now - self.missing_since) >= float(post_roll_seconds)
        return self.missing_analyses > max(1, int(track_missing_grace))

    def write_frame(
        self,
        frame: np.ndarray,
        source_frame_index: int = 0,
        frame_age_seconds: float = 0.0,
    ) -> None:
        if self.writer is None or self.last_box is None or self.closed:
            return
        if self.record_video_mode == "person-crop":
            crop = visual_crop_person(frame, self.last_box)
            if crop is None:
                return
            self.writer.write(visual_resize_with_padding(crop, self.output_size))
        else:
            self.writer.write(resize_frame_if_needed(frame, self.output_size))
        self.frame_count += 1
        source_index = int(source_frame_index)
        if source_index > 0 and source_index != self.last_written_source_frame_index:
            self.unique_frame_count += 1
            self.last_written_source_frame_index = source_index
        else:
            self.duplicate_frame_count += 1
        self.max_frame_age_seconds = max(float(self.max_frame_age_seconds), max(0.0, float(frame_age_seconds)))

    def mark_interrupted(self) -> None:
        self.recording_interrupted = True

    def should_force_close(self, max_clip_seconds: float) -> bool:
        if max_clip_seconds <= 0:
            return False
        return (time.monotonic() - self.started_at) >= max_clip_seconds

    def close(
        self,
        embedder: AppearanceEmbedder,
        reason: str,
        min_clip_seconds: float = 0.0,
        tracker_backend: str = "custom",
        tracker_config_path: str = "",
        tracker_with_reid: bool | None = None,
        source_fps: float = 0.0,
        analyzed_fps: float = 0.0,
        dropped_frame_count: int = 0,
        post_roll_seconds: float = 0.0,
        min_recorded_frames: int = 0,
        min_unique_frames: int = 0,
        min_gallery_crop_quality: float = 0.0,
    ) -> GalleryRecord | None:
        if self.closed:
            return None
        self.closed = True
        if self.writer is None:
            print(f"[gallery] Dropped track {self.track_id}; clip writer was unavailable: {reason}")
            return None
        if self.writer is not None:
            self.writer.release()

        duration = time.monotonic() - self.started_at
        encoded_duration = float(self.frame_count) / max(1.0, float(self.fps))
        required_frames = int(min_recorded_frames)
        if required_frames <= 0:
            required_frames = int(math.ceil(max(0.0, float(min_clip_seconds)) * max(1.0, float(self.fps))))
        if encoded_duration < max(0.0, float(min_clip_seconds)):
            print(
                f"[gallery] Skipped short ReID gallery track {self.track_id}: "
                f"encoded_duration={encoded_duration:.2f}s wall_duration={duration:.2f}s "
                f"frames={self.frame_count} fps={self.fps:.1f} min={float(min_clip_seconds):.2f}s reason={reason}"
            )
            self.discard_clip(
                "short_encoded_duration",
                {
                    "close_reason": reason,
                    "encoded_duration_seconds": round(encoded_duration, 3),
                    "wall_duration_seconds": round(duration, 3),
                    "frame_count": int(self.frame_count),
                    "writer_fps": round(float(self.fps), 3),
                    "min_clip_seconds": round(float(min_clip_seconds), 3),
                },
            )
            return None
        if self.frame_count < required_frames:
            print(
                f"[gallery] Skipped low-frame ReID gallery track {self.track_id}: "
                f"frames={self.frame_count} min_frames={required_frames} "
                f"encoded_duration={encoded_duration:.2f}s reason={reason}"
            )
            self.discard_clip(
                "low_recorded_frames",
                {
                    "close_reason": reason,
                    "encoded_duration_seconds": round(encoded_duration, 3),
                    "frame_count": int(self.frame_count),
                    "min_recorded_frames": int(required_frames),
                },
            )
            return None
        if self.unique_frame_count < max(0, int(min_unique_frames)):
            print(
                f"[gallery] Skipped duplicate-heavy ReID gallery track {self.track_id}: "
                f"unique_frames={self.unique_frame_count} min_unique={int(min_unique_frames)} "
                f"frames={self.frame_count} duplicates={self.duplicate_frame_count} reason={reason}"
            )
            self.discard_clip(
                "low_unique_frames",
                {
                    "close_reason": reason,
                    "encoded_duration_seconds": round(encoded_duration, 3),
                    "frame_count": int(self.frame_count),
                    "unique_frame_count": int(self.unique_frame_count),
                    "duplicate_frame_count": int(self.duplicate_frame_count),
                    "min_unique_frames": int(min_unique_frames),
                },
            )
            return None

        if self.best_crop is None:
            print(f"[gallery] Dropped empty track {self.track_id}: {reason}")
            self.discard_clip(
                "no_reid_crop",
                {
                    "close_reason": reason,
                    "encoded_duration_seconds": round(encoded_duration, 3),
                    "frame_count": int(self.frame_count),
                    "unique_frame_count": int(self.unique_frame_count),
                },
            )
            return None
        if self.best_quality < max(0.0, float(min_gallery_crop_quality)):
            print(
                f"[gallery] Skipped low-quality ReID gallery track {self.track_id}: "
                f"quality={self.best_quality:.3f} min_quality={float(min_gallery_crop_quality):.3f} "
                f"encoded_duration={encoded_duration:.2f}s reason={reason}"
            )
            self.discard_clip(
                "low_reid_crop_quality",
                {
                    "close_reason": reason,
                    "encoded_duration_seconds": round(encoded_duration, 3),
                    "frame_count": int(self.frame_count),
                    "unique_frame_count": int(self.unique_frame_count),
                    "best_crop_quality": round(float(self.best_quality), 4),
                    "min_gallery_crop_quality": round(float(min_gallery_crop_quality), 4),
                },
            )
            return None

        self.best_frame_path.parent.mkdir(parents=True, exist_ok=True)
        top_crop_paths: list[str] = []
        top_crop_metadata: list[dict[str, object]] = []
        crop_embeddings = []
        methods = []
        selected_candidates = select_diverse_crop_candidates(
            self.crop_candidates,
            top_n=self.top_n,
            selection_strategy=self.selection_strategy,
            min_frame_gap=self.diversity_min_frame_gap,
            max_similarity=self.diversity_max_similarity,
            min_quality_ratio=self.crop_min_quality_ratio,
        )
        for index, candidate in enumerate(selected_candidates, start=1):
            crop = candidate["crop"]
            if index == 1:
                crop_path = self.best_frame_path
            else:
                crop_path = self.best_frame_path.with_name(
                    f"{self.best_frame_path.stem}_crop_{index:03d}{self.best_frame_path.suffix}"
                )
            cv2.imwrite(str(crop_path), crop)
            resolved_crop_path = str(crop_path.resolve()).replace("\\", "/")
            top_crop_paths.append(resolved_crop_path)
            candidate["rank"] = int(index)
            metadata = crop_candidate_to_json(candidate, resolved_crop_path)
            metadata["track_id"] = int(self.track_id)
            top_crop_metadata.append(metadata)
            embedding, method = embedder.embed_bgr(crop)
            if embedding is not None:
                normalized = normalize_vector(embedding)
                if normalized is not None:
                    crop_embeddings.append(normalized)
                methods.append(method)

        if crop_embeddings:
            prototype_embeddings = np.vstack(crop_embeddings).astype(np.float32)
            embedding = normalize_vector(prototype_embeddings.mean(axis=0))
            method = methods[-1] if methods else embedder.method
        else:
            prototype_embeddings = None
            embedding, method = embedder.embed_bgr(self.best_crop)
        if embedding is None:
            print(f"[gallery] No embedding for track {self.track_id}: {self.clip_path}")
            self.discard_clip(
                "embedding_failed",
                {
                    "close_reason": reason,
                    "encoded_duration_seconds": round(encoded_duration, 3),
                    "frame_count": int(self.frame_count),
                    "unique_frame_count": int(self.unique_frame_count),
                },
            )
            return None

        best_metadata = top_crop_metadata[0] if top_crop_metadata else (self.best_candidate_metadata or {})
        return GalleryRecord(
            clip_id=self.clip_id,
            clip_path=str(self.clip_path.resolve()).replace("\\", "/"),
            best_frame_path=str(self.best_frame_path.resolve()).replace("\\", "/"),
            cam_id=self.cam_id,
            cam_label=self.cam_label,
            event_id=self.event_id,
            track_id=self.track_id,
            created_at=self.created_at,
            embedding=embedding,
            quality=max(0.0, float(self.best_quality)),
            duration_seconds=duration,
            frame_count=self.frame_count,
            writer_fps=self.fps,
            encoded_duration_seconds=encoded_duration,
            unique_frame_count=self.unique_frame_count,
            duplicate_frame_count=self.duplicate_frame_count,
            max_frame_age_seconds=self.max_frame_age_seconds,
            embedding_method=method,
            recording_interrupted=self.recording_interrupted,
            embedding_aggregation=f"prototype_mean_top_{len(crop_embeddings)}" if crop_embeddings else "single_best",
            prototype_embeddings=prototype_embeddings,
            prototype_score_mode=self.prototype_score_mode,
            prototype_count=len(crop_embeddings),
            crop_selection_strategy=self.selection_strategy,
            tracker_backend=str(tracker_backend),
            tracker_config_path=str(tracker_config_path),
            tracker_with_reid=tracker_with_reid,
            close_reason=str(reason),
            original_track_id=int(self.original_track_id),
            current_track_id=int(self.current_track_id),
            stitched_track_ids=[int(value) for value in self.stitched_track_ids],
            stitch_events=list(self.stitch_events),
            absorbed_track_ids=[int(value) for value in self.absorbed_track_ids],
            track_ownership_events=list(self.track_ownership_events),
            source_fps=float(source_fps),
            analyzed_fps=float(analyzed_fps),
            dropped_frame_count=int(dropped_frame_count),
            post_roll_seconds=float(post_roll_seconds),
            top_crop_paths=top_crop_paths,
            best_crop_frame_index=int(best_metadata.get("frame_index") or 0),
            best_crop_box=list(best_metadata.get("box") or []),
            best_crop_confidence=float(best_metadata.get("confidence") or 0.0),
            best_crop_quality=float(best_metadata.get("quality") or self.best_quality or 0.0),
            top_crop_metadata=top_crop_metadata,
        )


class OscSender:
    def __init__(self, host: str, port: int, dry_run: bool, disabled: bool = False):
        self.host = host
        self.port = int(port)
        self.dry_run = bool(dry_run)
        self.disabled = bool(disabled)
        self.client = None if (dry_run or disabled) else SimpleUDPClient(host, int(port))

    def send(self, address: str, payload):
        if self.disabled:
            return
        if self.dry_run:
            print(json.dumps({"osc": address, "payload": payload}, ensure_ascii=False))
            return
        self.client.send_message(address, payload)


def build_topk_payload(
    session_id: str,
    cam_id: int,
    cam_label: str,
    query_track_id: int,
    k: int,
    gallery_count: int,
    results: list[dict[str, object]],
) -> tuple[list[object], dict[str, object]]:
    event_id = str(int(time.time() * 1000))
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    query_id = f"query_{sanitize_id(session_id)}_cam_{cam_id}_track_{query_track_id}_event_{event_id}"

    flat: list[object] = [
        event_id,
        timestamp,
        query_id,
        f"cam_{cam_id}",
        int(k),
        int(len(results)),
        int(gallery_count),
    ]
    json_results = []
    for result in results:
        flat.extend(
            [
                int(result["rank"]),
                str(result["clip_id"]),
                str(result["clip_path"]),
                round(float(result["score"]), 6),
                str(result["cam_id"]),
                int(bool(result.get("fallback", False))),
            ]
        )
        json_results.append(
            {
                "rank": int(result["rank"]),
                "clip_id": str(result["clip_id"]),
                "clip_path": str(result["clip_path"]),
                "best_frame_path": str(result.get("best_frame_path", "")),
                "score": round(float(result["score"]), 6),
                "cam_id": str(result["cam_id"]),
                "cam_label": str(result.get("cam_label", "")),
                "event_id": str(result.get("event_id", "")),
                "track_id": int(result.get("track_id", 0)),
                "fallback": bool(result.get("fallback", False)),
                "quality": round(float(result.get("quality", 0.0)), 4),
                "embedding_aggregation": str(result.get("embedding_aggregation", "")),
            }
        )

    structured = {
        "event_id": event_id,
        "timestamp": timestamp,
        "query_id": query_id,
        "cam_id": f"cam_{cam_id}",
        "cam_label": sanitize_id(cam_label),
        "k": int(k),
        "result_count": int(len(results)),
        "gallery_count": int(gallery_count),
        "results": json_results,
    }
    return flat, structured


class LiveTopKCameraContext:
    def __init__(
        self,
        cam_id: int,
        cam_label: str,
        cam_type: str,
        video_source: str,
        args: argparse.Namespace,
        session_id: str,
        gallery: LiveTopKGallery,
        embedder: AppearanceEmbedder,
        osc: OscSender,
        stop_event: threading.Event,
    ):
        self.cam_id = int(cam_id)
        self.cam_label = sanitize_id(cam_label)
        self.cam_type = normalize_cam_type(cam_type)
        self.video_source = video_source
        self.source_info = parse_video_source(video_source)
        self.args = args
        self.session_id = session_id
        self.gallery = gallery
        self.embedder = embedder
        self.osc = osc
        self.stop_event = stop_event
        self.snapshot_root = resolve_project_path(args.snapshot_dir)
        self.output_size = (int(args.clip_width), int(args.clip_height))
        self.frame_index = 0
        self.analyzed_frames = 0
        self.read_failures = 0
        self.recorders: dict[int, PersonClipRecorder] = {}
        self.pending_stitch_recorders: dict[int, PendingStitchRecorder] = {}
        self.recorder_lock = threading.Lock()
        self.frame_lock = threading.Lock()
        self.latest_frame: np.ndarray | None = None
        self.latest_frame_index = 0
        self.latest_captured_at = 0.0
        self.last_analyzed_source_frame_index = 0
        self.dropped_frame_count = 0
        self.source_fps = 0.0
        self._fps_window_started_at = time.monotonic()
        self._fps_window_frames = 0
        self.started_at = time.monotonic()
        self.last_query_sent_at = 0.0
        self.crowded_until = 0.0
        self.stitch_log_path = self.gallery.log_dir / "stitch_events.jsonl"
        tracker_config_path = resolve_tracker_config_path(str(args.tracker_backend), str(args.tracker_config_path))
        self.tracker_config_path = display_project_path(tracker_config_path)
        self.tracker_with_reid = tracker_config_with_reid(tracker_config_path)

        self.analyzer = WalnutAnalyzer(
            pose_model_name="yolov8n-pose.pt",
            detect_model_name="yolov8n.pt",
            person_confidence=0.45,
            pose_confidence=0.35,
            accessory_confidence=0.18,
            model_imgsz=640,
            vote_frame_window=20,
            track_max_missing=max(5, int(args.track_missing_grace) + 2),
            tracker_backend=str(args.tracker_backend),
            tracker_config_path=tracker_config_path,
        )

    def update_latest_frame(self, frame: np.ndarray, frame_index: int, captured_at: float) -> None:
        now = time.monotonic()
        with self.frame_lock:
            if self.latest_frame is not None and self.latest_frame_index > self.last_analyzed_source_frame_index:
                self.dropped_frame_count += 1
            self.latest_frame = frame
            self.latest_frame_index = int(frame_index)
            self.latest_captured_at = float(captured_at)

        self._fps_window_frames += 1
        elapsed = now - self._fps_window_started_at
        if elapsed >= 1.0:
            self.source_fps = float(self._fps_window_frames) / max(1e-6, elapsed)
            self._fps_window_frames = 0
            self._fps_window_started_at = now

    def next_frame_for_analysis(self) -> tuple[np.ndarray, int, float] | None:
        interval = max(1, int(self.args.inference_interval))
        with self.frame_lock:
            if self.latest_frame is None:
                return None
            if self.latest_frame_index - self.last_analyzed_source_frame_index < interval:
                return None
            self.last_analyzed_source_frame_index = self.latest_frame_index
            return self.latest_frame, self.latest_frame_index, self.latest_captured_at

    def latest_frame_snapshot(self) -> tuple[np.ndarray, int, float] | None:
        with self.frame_lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame, int(self.latest_frame_index), float(self.latest_captured_at)

    def analyzed_fps(self) -> float:
        elapsed = time.monotonic() - self.started_at
        if elapsed <= 0:
            return 0.0
        return float(self.analyzed_frames) / elapsed

    def _unique_recorders_locked(self) -> list[PersonClipRecorder]:
        unique: list[PersonClipRecorder] = []
        seen: set[int] = set()
        for recorder in self.recorders.values():
            marker = id(recorder)
            if marker in seen:
                continue
            seen.add(marker)
            unique.append(recorder)
        return unique

    def _unique_pending_locked(self) -> list[tuple[int, PendingStitchRecorder]]:
        unique: list[tuple[int, PendingStitchRecorder]] = []
        seen: set[int] = set()
        for track_id, pending in self.pending_stitch_recorders.items():
            marker = id(pending.recorder)
            if marker in seen:
                continue
            seen.add(marker)
            unique.append((int(track_id), pending))
        return unique

    def _attach_recorder_aliases_locked(self, recorder: PersonClipRecorder) -> None:
        for track_id in sorted(int(value) for value in recorder.owned_track_ids if int(value) > 0):
            self.recorders[int(track_id)] = recorder

    def _detach_recorder_aliases_locked(self, recorder: PersonClipRecorder) -> list[int]:
        removed = []
        for track_id, candidate in list(self.recorders.items()):
            if candidate is recorder:
                removed.append(int(track_id))
                self.recorders.pop(track_id, None)
        return removed

    def _detach_pending_aliases_locked(self, recorder: PersonClipRecorder) -> list[int]:
        removed = []
        for track_id, pending in list(self.pending_stitch_recorders.items()):
            if pending.recorder is recorder:
                removed.append(int(track_id))
                self.pending_stitch_recorders.pop(track_id, None)
        return removed

    @staticmethod
    def _recorder_visible_track_ids(recorder: PersonClipRecorder, current_track_ids: set[int]) -> set[int]:
        return {int(track_id) for track_id in recorder.owned_track_ids if int(track_id) in current_track_ids}

    def process_next_analysis(self) -> bool:
        snapshot = self.next_frame_for_analysis()
        if snapshot is None:
            return False

        frame, source_frame_index, _captured_at = snapshot
        self.analyzed_frames += 1
        people = self.analyzer.analyze_frame(frame)
        if self.cam_type == "G":
            self._handle_gallery_people(frame, people, source_frame_index)
        else:
            self._handle_query_people(frame, people)
        self._send_status(people)
        self._show_analysis_preview(frame, people)

        if self.analyzed_frames % max(1, self.args.print_interval_frames) == 0:
            print(
                f"[cam {self.cam_id}] role={self.cam_type} people={len(people)} "
                f"gallery={self.gallery.count()} tracker={self.args.tracker_backend} "
                f"source_fps={self.source_fps:.1f} analyzed_fps={self.analyzed_fps():.1f} "
                f"dropped={self.dropped_frame_count} inference_ms={self.analyzer.last_inference_ms:.1f}"
            )
        return True

    def run(self) -> None:
        print(
            f"[cam {self.cam_id}] Starting live Top-K worker role={self.cam_type} "
            f"label={self.cam_label} source={self.source_info['display']}"
        )
        started = time.monotonic()
        open_failures = 0
        while not self.stop_event.is_set():
            if self.args.max_runtime_seconds > 0 and time.monotonic() - started >= self.args.max_runtime_seconds:
                self.stop_event.set()
                break

            cap = create_capture(
                self.video_source,
                self.args.frame_width,
                self.args.frame_height,
                float(self.args.recording_fps),
                int(self.args.rtsp_open_timeout_ms),
                int(self.args.rtsp_read_timeout_ms),
            )
            if not cap.isOpened():
                open_failures += 1
                retry_delay = self._open_retry_delay(open_failures)
                print(
                    f"[cam {self.cam_id}] Failed to open {self.source_info['display']}; "
                    f"retrying in {retry_delay:.1f}s."
                )
                time.sleep(retry_delay)
                continue
            open_failures = 0

            try:
                self._capture_loop(cap, started)
            finally:
                cap.release()
                self._close_all_recorders("capture_closed")

            if not self.stop_event.is_set():
                time.sleep(self.args.reconnect_delay)

    def _capture_loop(self, cap: cv2.VideoCapture, started: float) -> None:
        while not self.stop_event.is_set():
            if self.args.max_runtime_seconds > 0 and time.monotonic() - started >= self.args.max_runtime_seconds:
                self.stop_event.set()
                break

            ok, frame = cap.read()
            if not ok or frame is None:
                self.read_failures += 1
                if self.read_failures >= self.args.max_read_failures:
                    print(f"[cam {self.cam_id}] Read failure threshold reached.")
                    break
                time.sleep(0.05)
                continue

            self.read_failures = 0
            self.frame_index += 1
            self._write_active_recorders(frame)

            if self.frame_index % max(1, self.args.inference_interval) != 0:
                continue

            self.analyzed_frames += 1
            people = self.analyzer.analyze_frame(frame)
            if self.cam_type == "G":
                self._handle_gallery_people(frame, people, self.frame_index)
            else:
                self._handle_query_people(frame, people)
            self._send_status(people)
            self._show_analysis_preview(frame, people)

            if self.analyzed_frames % max(1, self.args.print_interval_frames) == 0:
                print(
                f"[cam {self.cam_id}] role={self.cam_type} people={len(people)} "
                f"gallery={self.gallery.count()} inference_ms={self.analyzer.last_inference_ms:.1f}"
                )

    def _open_retry_delay(self, open_failures: int) -> float:
        base = max(0.1, float(self.args.reconnect_delay))
        cap = max(base, float(self.args.max_open_retry_delay))
        return min(cap, base * (2 ** min(4, max(0, int(open_failures) - 1))))

    def _write_active_recorders(self, frame: np.ndarray) -> None:
        force_close_track_ids = []
        with self.recorder_lock:
            for recorder in self._unique_recorders_locked():
                recorder.write_frame(frame, self.frame_index, 0.0)
                if recorder.should_force_close(self.args.max_clip_seconds):
                    force_close_track_ids.append(recorder.track_id)
        for track_id in force_close_track_ids:
            self._finalize_recorder(track_id, "max_clip_seconds")

    def write_recording_tick(self) -> None:
        self._expire_pending_stitch_recorders(time.monotonic())
        snapshot = self.latest_frame_snapshot()
        if snapshot is None:
            return

        frame, source_frame_index, captured_at = snapshot
        now = time.monotonic()
        frame_age = max(0.0, now - float(captured_at))
        stale_limit = max(0.0, float(self.args.recording_stale_frame_seconds))
        reconnect_grace = max(stale_limit, float(self.args.recording_reconnect_grace_seconds))
        close_track_ids: list[tuple[int, str]] = []

        with self.recorder_lock:
            recorders = self._unique_recorders_locked()
            if frame_age > reconnect_grace:
                for recorder in recorders:
                    recorder.mark_interrupted()
                    close_track_ids.append((recorder.track_id, "recording_input_stale"))
            elif frame_age <= stale_limit:
                for recorder in recorders:
                    recorder.write_frame(frame, source_frame_index, frame_age)
                    if recorder.should_force_close(self.args.max_clip_seconds):
                        close_track_ids.append((recorder.track_id, "max_clip_seconds"))
            else:
                for recorder in recorders:
                    if recorder.should_force_close(self.args.max_clip_seconds):
                        close_track_ids.append((recorder.track_id, "max_clip_seconds"))

        for track_id, reason in close_track_ids:
            self._finalize_recorder(track_id, reason)

    def _tracklet_stitching_enabled(self) -> bool:
        return self.cam_type == "G" and not bool(getattr(self.args, "disable_tracklet_stitching", False))

    def _note_crowded_frame(self, people: list[dict[str, object]], now: float) -> None:
        if has_crowded_overlap(people):
            self.crowded_until = max(
                float(self.crowded_until),
                now + max(0.0, float(self.args.stitch_crowded_window_seconds)),
            )

    def _is_crowded_recent(self, now: float) -> bool:
        return (not bool(self.args.stitch_allow_crowded)) and now < float(self.crowded_until)

    def _log_duplicate_suppression(
        self,
        new_track_id: int,
        matched_track_id: int,
        quality: float,
        iou: float,
        containment: float,
        center_distance_ratio: float,
    ) -> None:
        self._log_stitch_event(
            {
                "accepted": False,
                "reason": "duplicate_track_suppressed",
                "old_track_id": int(matched_track_id),
                "new_track_id": int(new_track_id),
                "source": "active_recorder",
                "score": round(float(quality), 6),
                "bbox_iou": round(float(iou), 6),
                "bbox_containment": round(float(containment), 6),
                "center_distance_ratio": round(float(center_distance_ratio), 6),
            }
        )

    def _should_suppress_duplicate_track(
        self,
        person: dict[str, object],
        frame: np.ndarray,
    ) -> bool:
        if bool(getattr(self.args, "disable_duplicate_track_suppression", False)):
            return False
        new_track_id = int(person.get("track_id", 0))
        crop = visual_crop_person(frame, person["box"])
        quality = visual_crop_quality(crop, person, frame.shape)
        if quality > float(getattr(self.args, "duplicate_track_max_quality", 0.45)):
            return False

        min_iou = float(getattr(self.args, "duplicate_track_min_iou", 0.12))
        max_distance = float(getattr(self.args, "duplicate_track_max_center_distance_ratio", 0.10))
        with self.recorder_lock:
            recorders = self._unique_recorders_locked() + [
                pending.recorder for _track_id, pending in self._unique_pending_locked()
        ]
        for recorder in recorders:
            if recorder.last_box is None or new_track_id in recorder.owned_track_ids:
                continue
            iou = box_iou(recorder.last_box, person["box"])
            containment = box_intersection_over_min_area(recorder.last_box, person["box"])
            distance = box_center_distance_ratio(recorder.last_box, person["box"], frame.shape)
            if iou >= min_iou or containment >= 0.70 or distance <= max_distance:
                self._log_duplicate_suppression(
                    new_track_id,
                    int(recorder.track_id),
                    quality,
                    iou,
                    containment,
                    distance,
                )
                return True
        return False

    def _candidate_absorb_recorders(self, person: dict[str, object], frame: np.ndarray):
        new_track_id = int(person.get("track_id", 0))
        candidates = []
        with self.recorder_lock:
            active_recorders = self._unique_recorders_locked()
            pending_recorders = [
                pending.recorder for _track_id, pending in self._unique_pending_locked()
            ]
        for source, recorders in (("active_recorder", active_recorders), ("pending_recorder", pending_recorders)):
            for recorder in recorders:
                if new_track_id in recorder.owned_track_ids or recorder.last_box is None:
                    continue
                iou = box_iou(recorder.last_box, person["box"])
                containment = box_intersection_over_min_area(recorder.last_box, person["box"])
                distance = box_center_distance_ratio(recorder.last_box, person["box"], frame.shape)
                candidates.append((source, recorder, iou, containment, distance))
        return candidates

    def _try_absorb_duplicate_track(
        self,
        frame: np.ndarray,
        person: dict[str, object],
        source_frame_index: int,
        now: float,
    ) -> bool:
        if bool(getattr(self.args, "disable_duplicate_track_suppression", False)):
            return False
        new_track_id = int(person.get("track_id", 0))
        if new_track_id <= 0:
            return False
        with self.recorder_lock:
            if new_track_id in self.recorders:
                return True

        crop = visual_crop_person(frame, person["box"])
        quality = visual_crop_quality(crop, person, frame.shape)
        candidates = self._candidate_absorb_recorders(person, frame)
        if not candidates:
            return False

        max_distance = float(getattr(self.args, "duplicate_absorb_max_center_distance_ratio", 0.12))
        min_iou = float(getattr(self.args, "duplicate_absorb_min_iou", 0.50))
        min_containment = float(getattr(self.args, "duplicate_absorb_min_containment", 0.85))
        low_quality_max = float(getattr(self.args, "duplicate_absorb_low_quality_max", 0.45))
        low_quality_distance = float(getattr(self.args, "duplicate_absorb_low_quality_distance_ratio", 0.08))
        reid_threshold = float(getattr(self.args, "duplicate_absorb_reid_threshold", 0.76))

        accepted: list[tuple[float, str, str, PersonClipRecorder, float, float, float, str]] = []
        for source, recorder, iou, containment, distance in candidates:
            if distance > max_distance and not (quality <= low_quality_max and distance <= low_quality_distance):
                continue
            if containment >= min_containment and distance <= max_distance:
                accepted.append((1.0 + containment, "containment_absorbed", source, recorder, iou, containment, distance, "geometry"))
                continue
            if iou >= min_iou and distance <= max_distance:
                accepted.append((1.0 + iou, "active_duplicate_absorbed", source, recorder, iou, containment, distance, "geometry"))
                continue
            if quality <= low_quality_max and distance <= low_quality_distance and (iou >= 0.03 or containment >= 0.40):
                accepted.append((0.90 + containment, "active_duplicate_absorbed", source, recorder, iou, containment, distance, "low_quality_geometry"))

        if not accepted and crop is not None:
            new_embedding, new_method = self.embedder.embed_bgr(crop)
            new_embedding = normalize_vector(new_embedding)
            if new_embedding is not None:
                for source, recorder, iou, containment, distance in candidates:
                    if distance > max_distance or (iou < 0.03 and containment < 0.40):
                        continue
                    old_prototypes, old_method = recorder.stitch_prototype_embeddings(self.embedder)
                    if old_prototypes is None:
                        continue
                    prototype_scores = np.clip(old_prototypes @ new_embedding, -1.0, 1.0).reshape(-1)
                    score = float(np.max(prototype_scores)) if prototype_scores.size else 0.0
                    if score >= reid_threshold:
                        accepted.append(
                            (
                                score,
                                "prototype_absorbed",
                                source,
                                recorder,
                                iou,
                                containment,
                                distance,
                                old_method or new_method,
                            )
                        )

        if not accepted:
            return False

        accepted.sort(key=lambda item: item[0], reverse=True)
        score, reason, source, recorder, iou, containment, distance, method = accepted[0]
        event = {
            "accepted": True,
            "reason": reason,
            "old_track_id": int(recorder.current_track_id or recorder.track_id),
            "new_track_id": int(new_track_id),
            "source": source,
            "score": round(float(score), 6),
            "crop_quality": round(float(quality), 6),
            "bbox_iou": round(float(iou), 6),
            "bbox_containment": round(float(containment), 6),
            "center_distance_ratio": round(float(distance), 6),
            "time_gap_seconds": round(max(0.0, now - float(recorder.last_observed_at)), 3),
            "embedding_method": method,
            "source_frame_index": int(source_frame_index),
        }

        with self.recorder_lock:
            if new_track_id in self.recorders:
                return True
            if source == "pending_recorder":
                self._detach_pending_aliases_locked(recorder)
            recorder.absorb_track_id(new_track_id, event)
            recorder.observe(frame, person, source_frame_index)
            self._attach_recorder_aliases_locked(recorder)
        self._log_stitch_event(event)
        print(
            f"[absorb] cam={self.cam_label} track={new_track_id} -> recorder={event['old_track_id']} "
            f"reason={reason} score={float(score):.3f} dist={distance:.3f} iou={iou:.3f}"
        )
        return True

    def _log_stitch_event(self, payload: dict[str, object]) -> None:
        payload = dict(payload)
        payload.setdefault("session_id", self.session_id)
        payload.setdefault("cam_id", self.cam_id)
        payload.setdefault("cam_label", self.cam_label)
        payload.setdefault("created_at", round(time.time(), 3))
        self.stitch_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.stitch_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def _expire_pending_stitch_recorders(self, now: float) -> None:
        expired: list[tuple[int, str]] = []
        seen: set[int] = set()
        with self.recorder_lock:
            for track_id, pending in list(self.pending_stitch_recorders.items()):
                marker = id(pending.recorder)
                if marker in seen:
                    continue
                seen.add(marker)
                if now >= float(pending.expires_at):
                    expired.append((track_id, pending.close_reason))
        for track_id, reason in expired:
            self._finalize_recorder(track_id, reason)

    def _park_recorder_for_stitching(self, track_id: int, reason: str, now: float) -> bool:
        if not self._tracklet_stitching_enabled():
            return False
        stitch_window = max(0.0, float(self.args.stitch_window_seconds))
        if stitch_window <= 0:
            return False
        with self.recorder_lock:
            recorder = self.recorders.get(track_id)
            if recorder is None or recorder.closed:
                return False
            self._detach_recorder_aliases_locked(recorder)
            pending = PendingStitchRecorder(
                recorder=recorder,
                pending_since=float(now),
                expires_at=float(now) + stitch_window,
                close_reason=str(reason),
            )
            for owned_track_id in sorted(int(value) for value in recorder.owned_track_ids if int(value) > 0):
                self.pending_stitch_recorders[int(owned_track_id)] = pending
        self._log_stitch_event(
            {
                "accepted": False,
                "reason": "parked_for_stitch_window",
                "old_track_id": int(track_id),
                "new_track_id": 0,
                "source": "pending",
                "stitch_window_seconds": round(stitch_window, 3),
                "owned_track_ids": sorted(int(value) for value in recorder.owned_track_ids),
            }
        )
        return True

    def _candidate_stitch_recorders(self, now: float, new_track_id: int):
        stitch_window = max(0.0, float(self.args.stitch_window_seconds))
        candidates = []
        with self.recorder_lock:
            for recorder in self._unique_recorders_locked():
                old_track_id = int(recorder.current_track_id or recorder.track_id)
                if int(new_track_id) in recorder.owned_track_ids or recorder.missing_since is None:
                    continue
                time_gap = max(0.0, now - float(recorder.missing_since))
                if time_gap <= stitch_window and recorder.best_crop is not None and recorder.last_box is not None:
                    candidates.append(("active_missing", old_track_id, recorder, time_gap, tuple(recorder.last_box)))
            for old_track_id, pending in self._unique_pending_locked():
                recorder = pending.recorder
                time_gap = max(0.0, now - float(pending.pending_since))
                if time_gap <= stitch_window and recorder.best_crop is not None and recorder.last_box is not None:
                    candidates.append(("pending", int(old_track_id), recorder, time_gap, tuple(recorder.last_box)))
        return candidates

    def _try_stitch_track(
        self,
        frame: np.ndarray,
        person: dict[str, object],
        source_frame_index: int,
        now: float,
    ) -> bool:
        if not self._tracklet_stitching_enabled():
            return False
        new_track_id = int(person.get("track_id", 0))
        if new_track_id <= 0:
            return False

        with self.recorder_lock:
            if new_track_id in self.recorders:
                return True
            pending_same_track = self.pending_stitch_recorders.get(new_track_id)
            if pending_same_track is not None:
                recorder = pending_same_track.recorder
                self._detach_pending_aliases_locked(recorder)
                time_gap = max(0.0, now - float(pending_same_track.pending_since))
                distance_ratio = (
                    box_center_distance_ratio(recorder.last_box, person["box"], frame.shape)
                    if recorder.last_box is not None
                    else 0.0
                )
                payload = StitchDecision(
                    accepted=True,
                    reason="same_track_resumed",
                    old_track_id=new_track_id,
                    new_track_id=new_track_id,
                    source="pending",
                    score=1.0,
                    second_score=-1.0,
                    center_distance_ratio=distance_ratio,
                    time_gap_seconds=time_gap,
                    embedding_method="same_track_id",
                ).to_json()
                payload["source_frame_index"] = int(source_frame_index)
                recorder.reassign_track_id(new_track_id, payload)
                recorder.observe(frame, person, source_frame_index)
                self._attach_recorder_aliases_locked(recorder)
                self._log_stitch_event(payload)
                print(
                    f"[stitch] cam={self.cam_label} resumed track={new_track_id} "
                    f"gap={time_gap:.2f}s dist={distance_ratio:.3f}"
                )
                return True

        candidates = self._candidate_stitch_recorders(now, new_track_id)
        if not candidates:
            return False

        crowded_recent = self._is_crowded_recent(now)
        if crowded_recent:
            near_limit = float(getattr(self.args, "stitch_crowded_near_distance_ratio", 0.08))
            if not should_allow_crowded_stitch_by_geometry(candidates, person, frame.shape, near_limit):
                source, old_track_id, _recorder, time_gap, old_box = min(
                    candidates,
                    key=lambda item: box_center_distance_ratio(item[4], person["box"], frame.shape),
                )
                decision = StitchDecision(
                    accepted=False,
                    reason="recent_crowded_frame",
                    old_track_id=old_track_id,
                    new_track_id=new_track_id,
                    source=source,
                    center_distance_ratio=box_center_distance_ratio(old_box, person["box"], frame.shape),
                    time_gap_seconds=time_gap,
                )
                self._log_stitch_event(decision.to_json())
                return False

        new_crop = visual_crop_person(frame, person["box"])
        new_embedding, new_method = self.embedder.embed_bgr(new_crop)
        new_embedding = normalize_vector(new_embedding)
        if new_embedding is None:
            source, old_track_id, _recorder, time_gap, old_box = candidates[0]
            decision = StitchDecision(
                accepted=False,
                reason="new_track_embedding_failed",
                old_track_id=old_track_id,
                new_track_id=new_track_id,
                source=source,
                center_distance_ratio=box_center_distance_ratio(old_box, person["box"], frame.shape),
                time_gap_seconds=time_gap,
                embedding_method=new_method,
            )
            self._log_stitch_event(decision.to_json())
            return False

        max_distance = max(0.0, float(self.args.stitch_max_center_distance_ratio))
        threshold = float(self.args.stitch_reid_threshold)
        scored: list[tuple[float, str, int, PersonClipRecorder, float, float, str, str]] = []
        best_rejected: StitchDecision | None = None
        for source, old_track_id, recorder, time_gap, old_box in candidates:
            distance_ratio = box_center_distance_ratio(old_box, person["box"], frame.shape)
            if distance_ratio > max_distance:
                decision = StitchDecision(
                    accepted=False,
                    reason="bbox_center_too_far",
                    old_track_id=old_track_id,
                    new_track_id=new_track_id,
                    source=source,
                    center_distance_ratio=distance_ratio,
                    time_gap_seconds=time_gap,
                    embedding_method=new_method,
                )
                if best_rejected is None or decision.center_distance_ratio < best_rejected.center_distance_ratio:
                    best_rejected = decision
                continue

            old_prototypes, old_method = recorder.stitch_prototype_embeddings(self.embedder)
            if old_prototypes is None:
                decision = StitchDecision(
                    accepted=False,
                    reason="old_track_embedding_failed",
                    old_track_id=old_track_id,
                    new_track_id=new_track_id,
                    source=source,
                    center_distance_ratio=distance_ratio,
                    time_gap_seconds=time_gap,
                    embedding_method=old_method or new_method,
                )
                best_rejected = best_rejected or decision
                continue

            prototype_scores = np.clip(old_prototypes @ new_embedding, -1.0, 1.0).reshape(-1)
            score = float(np.max(prototype_scores)) if prototype_scores.size else 0.0
            method = old_method or new_method
            decision = StitchDecision(
                accepted=False,
                reason="reid_score_below_threshold",
                old_track_id=old_track_id,
                new_track_id=new_track_id,
                source=source,
                score=score,
                center_distance_ratio=distance_ratio,
                time_gap_seconds=time_gap,
                embedding_method=method,
            )
            if score >= threshold:
                scored.append((score, source, old_track_id, recorder, time_gap, distance_ratio, method, "stitched_tracklet"))
            elif (
                continuity_reason := spatial_continuity_stitch_reason(
                    score,
                    time_gap,
                    distance_ratio,
                    self.args,
                    crowded_recent,
                )
            ):
                scored.append((score, source, old_track_id, recorder, time_gap, distance_ratio, method, continuity_reason))
            elif best_rejected is None or score > best_rejected.score:
                best_rejected = decision

        if not scored:
            if best_rejected is not None:
                self._log_stitch_event(best_rejected.to_json())
            return False

        scored.sort(key=lambda item: item[0], reverse=True)
        best_score, source, old_track_id, recorder, time_gap, distance_ratio, method, accept_reason = scored[0]
        second_score = scored[1][0] if len(scored) > 1 else -1.0
        margin = float(self.args.stitch_ambiguous_margin)
        if len(scored) > 1 and (best_score - second_score) < margin:
            decision = StitchDecision(
                accepted=False,
                reason="ambiguous_stitch_candidate",
                old_track_id=old_track_id,
                new_track_id=new_track_id,
                source=source,
                score=best_score,
                second_score=second_score,
                center_distance_ratio=distance_ratio,
                time_gap_seconds=time_gap,
                embedding_method=method,
            )
            self._log_stitch_event(decision.to_json())
            return False

        decision = StitchDecision(
            accepted=True,
            reason=accept_reason,
            old_track_id=old_track_id,
            new_track_id=new_track_id,
            source=source,
            score=best_score,
            second_score=second_score,
            center_distance_ratio=distance_ratio,
            time_gap_seconds=time_gap,
            embedding_method=method,
        )
        payload = decision.to_json()
        payload["source_frame_index"] = int(source_frame_index)
        payload["stitch_score_mode"] = "prototype_max"

        with self.recorder_lock:
            if new_track_id in self.recorders:
                return True
            if source == "pending":
                pending = self.pending_stitch_recorders.get(old_track_id)
                if pending is None or pending.recorder is not recorder:
                    return False
                self._detach_pending_aliases_locked(recorder)
            else:
                active = self.recorders.get(old_track_id)
                if active is None or active is not recorder:
                    return False
                self._detach_recorder_aliases_locked(recorder)
            recorder.reassign_track_id(new_track_id, payload)
            recorder.observe(frame, person, source_frame_index)
            self._attach_recorder_aliases_locked(recorder)

        self._log_stitch_event(payload)
        print(
            f"[stitch] cam={self.cam_label} old_track={old_track_id} -> new_track={new_track_id} "
            f"score={best_score:.3f} gap={time_gap:.2f}s dist={distance_ratio:.3f}"
        )
        return True

    def _handle_gallery_people(
        self,
        frame: np.ndarray,
        people: list[dict[str, object]],
        source_frame_index: int = 0,
    ) -> None:
        current_track_ids = {int(person.get("track_id", 0)) for person in people}
        now = time.monotonic()
        self._note_crowded_frame(people, now)
        self._expire_pending_stitch_recorders(now)
        close_track_ids = []
        with self.recorder_lock:
            for recorder in self._unique_recorders_locked():
                if not self._recorder_visible_track_ids(recorder, current_track_ids):
                    recorder.mark_missing(now)
                    if recorder.should_close_after_missing(
                        float(self.args.post_roll_seconds),
                        int(self.args.track_missing_grace),
                    ):
                        close_track_ids.append(int(recorder.current_track_id or recorder.track_id))
        for track_id in close_track_ids:
            if not self._park_recorder_for_stitching(track_id, "person_left_frame", now):
                self._finalize_recorder(track_id, "person_left_frame")

        for person in people:
            track_id = int(person.get("track_id", 0))
            if track_id <= 0:
                continue
            with self.recorder_lock:
                recorder = self.recorders.get(track_id)
            if recorder is None and self._try_stitch_track(frame, person, source_frame_index, now):
                continue
            with self.recorder_lock:
                recorder = self.recorders.get(track_id)
            if recorder is None and self._try_absorb_duplicate_track(frame, person, source_frame_index, now):
                continue
            with self.recorder_lock:
                recorder = self.recorders.get(track_id)
            if recorder is None and self._should_suppress_duplicate_track(person, frame):
                continue
            with self.recorder_lock:
                recorder = self.recorders.get(track_id)
                if recorder is None:
                    output_size = self.output_size
                    if self.args.record_video_mode == "full-frame":
                        output_size = (int(frame.shape[1]), int(frame.shape[0]))
                    recorder = PersonClipRecorder(
                        self.session_id,
                        self.snapshot_root,
                        self.cam_id,
                        self.cam_label,
                        track_id,
                        output_size,
                        fps=float(self.args.recording_fps),
                        record_video_mode=str(self.args.record_video_mode),
                        top_n=max(1, int(self.args.live_visual_top_n)),
                        selection_strategy=str(self.args.crop_selection_strategy),
                        diversity_min_frame_gap=int(self.args.crop_diversity_min_frame_gap),
                        diversity_max_similarity=float(self.args.crop_diversity_max_similarity),
                        crop_min_quality_ratio=float(self.args.crop_min_quality_ratio),
                        prototype_score_mode=str(self.args.prototype_score_mode),
                    )
                    self.recorders[track_id] = recorder
                recorder.observe(frame, person, source_frame_index)

    def _handle_query_people(self, frame: np.ndarray, people: list[dict[str, object]]) -> None:
        if not people:
            return

        now = time.monotonic()
        if now - self.last_query_sent_at < max(0.1, float(self.args.query_interval_seconds)):
            return

        target = self._select_query_target(people, frame.shape[1], frame.shape[0])
        crop = visual_crop_person(frame, target["box"])
        embedding, method = self.embedder.embed_bgr(crop)
        results = self.gallery.rank(
            embedding,
            k=max(1, int(self.args.topk)),
            candidate_pool=max(1, int(self.args.candidate_pool)),
            fallback_score=float(self.args.fallback_score),
        )

        query_track_id = int(target.get("track_id", 0))
        flat_payload, structured_payload = build_topk_payload(
            self.session_id,
            self.cam_id,
            self.cam_label,
            query_track_id,
            max(1, int(self.args.topk)),
            self.gallery.count(),
            results,
        )
        structured_payload["embedding_method"] = method
        structured_payload["query_quality"] = round(visual_crop_quality(crop, target, frame.shape), 4)
        structured_payload["tracker_backend"] = str(self.args.tracker_backend)
        structured_payload["source_fps"] = round(float(self.source_fps), 3)
        structured_payload["analyzed_fps"] = round(float(self.analyzed_fps()), 3)
        structured_payload["dropped_frame_count"] = int(self.dropped_frame_count)
        export_dir = self._export_topk_results(crop, structured_payload)
        if export_dir:
            structured_payload["export_dir"] = export_dir
        self.gallery.log_query(structured_payload)
        self._send_topk_payload(flat_payload, structured_payload)
        self.last_query_sent_at = now

    def _select_query_target(self, people: list[dict[str, object]], frame_width: int, frame_height: int):
        frame_center_x = frame_width / 2.0
        frame_area = max(1.0, float(frame_width * frame_height))

        def target_score(person: dict[str, object]) -> float:
            x1, y1, x2, y2 = person["box"]
            box_area = max(0.0, float((x2 - x1) * (y2 - y1)))
            box_center_x = (x1 + x2) / 2.0
            center_distance_ratio = abs(box_center_x - frame_center_x) / max(1.0, frame_center_x)
            return (box_area / frame_area) - (center_distance_ratio * 0.18)

        return max(people, key=target_score)

    def _send_topk_payload(self, flat_payload: list[object], structured_payload: dict[str, object]) -> None:
        base = f"/walnut/topk/cam/{self.cam_id}"
        self.osc.send(f"{base}/results", flat_payload)
        self.osc.send(f"{base}/last/event_id", structured_payload["event_id"])
        self.osc.send(f"{base}/last/query_id", structured_payload["query_id"])
        self.osc.send(f"{base}/last/cam_label", structured_payload["cam_label"])
        self.osc.send(f"{base}/last/result_count", int(structured_payload["result_count"]))
        self.osc.send(f"{base}/last/gallery_count", int(structured_payload["gallery_count"]))
        for rank in range(1, max(1, int(self.args.topk)) + 1):
            result = next((item for item in structured_payload["results"] if item["rank"] == rank), None)
            path = "" if result is None else str(result["clip_path"])
            score = 0.0 if result is None else float(result["score"])
            cam_label = "" if result is None else str(result.get("cam_label", ""))
            self.osc.send(f"{base}/result/{rank}/path", path)
            self.osc.send(f"{base}/result/{rank}/score", score)
            self.osc.send(f"{base}/result/{rank}/cam_label", cam_label)
        print(
            f"[cam {self.cam_id} {self.cam_label}] TopK query={structured_payload['query_id']} "
            f"results={structured_payload['result_count']}/{self.args.topk} "
            f"gallery={structured_payload['gallery_count']}"
        )

    def _send_status(self, people: list[dict[str, object]]) -> None:
        base = f"/walnut/live_topk/cam/{self.cam_id}/status"
        self.osc.send(f"{base}/people_count", int(len(people)))
        self.osc.send(f"{base}/role", self.cam_type)
        self.osc.send(f"{base}/cam_label", self.cam_label)
        self.osc.send(f"{base}/gallery_count", int(self.gallery.count()))
        self.osc.send(f"{base}/active_recordings", int(self.active_recording_count()))
        self.osc.send(f"{base}/source_fps", float(self.source_fps))
        self.osc.send(f"{base}/analyzed_fps", float(self.analyzed_fps()))
        self.osc.send(f"{base}/dropped_frame_count", int(self.dropped_frame_count))

    def active_recording_count(self) -> int:
        with self.recorder_lock:
            pending_count = len(self._unique_pending_locked())
            return len(self._unique_recorders_locked()) + pending_count

    def _show_analysis_preview(self, frame: np.ndarray, people: list[dict[str, object]]) -> None:
        if not self.args.show_preview:
            return
        preview = draw_analysis_overlay(
            frame,
            people,
            self.cam_id,
            self.cam_label,
            self.cam_type,
            self.gallery.count(),
            self.active_recording_count(),
            self.analyzer.last_inference_ms,
        )
        enqueue_preview_window(
            f"YOLO/ReID analysis - cam_{self.cam_id} {self.cam_label}",
            preview,
            float(self.args.preview_scale),
        )

    def _export_topk_results(self, query_crop: np.ndarray | None, payload: dict[str, object]) -> str:
        if not str(self.args.export_topk_dir or "").strip():
            return ""

        export_root = resolve_project_path(self.args.export_topk_dir)
        query_dir = export_root / sanitize_id(self.session_id) / sanitize_id(payload["query_id"])
        query_dir.mkdir(parents=True, exist_ok=True)

        export_payload = dict(payload)
        export_payload["export_mode"] = str(self.args.export_mode)
        export_payload["export_dir"] = str(query_dir.resolve()).replace("\\", "/")
        if query_crop is not None and query_crop.size:
            query_best_path = query_dir / "query_best.jpg"
            cv2.imwrite(str(query_best_path), query_crop)
            export_payload["query_best_path"] = str(query_best_path.resolve()).replace("\\", "/")

        exported_results = []
        for result in export_payload.get("results", []):
            rank = int(result["rank"])
            rank_dir = query_dir / f"rank_{rank:02d}"
            rank_dir.mkdir(parents=True, exist_ok=True)
            exported = dict(result)

            clip_suffix = Path(str(result.get("clip_path", ""))).suffix or ".mp4"
            best_suffix = Path(str(result.get("best_frame_path", ""))).suffix or ".jpg"
            exported["exported_clip"] = export_asset(
                str(result.get("clip_path", "")),
                rank_dir / f"clip{clip_suffix}",
                str(self.args.export_mode),
                "clip_path.txt",
            )
            exported["exported_best_frame"] = export_asset(
                str(result.get("best_frame_path", "")),
                rank_dir / f"best{best_suffix}",
                str(self.args.export_mode),
                "best_path.txt",
            )
            write_json(rank_dir / "score.json", exported)
            exported_results.append(exported)

        export_payload["results"] = exported_results
        write_json(query_dir / "results.json", export_payload)
        return str(query_dir.resolve()).replace("\\", "/")

    def _finalize_recorder(self, track_id: int, reason: str) -> None:
        with self.recorder_lock:
            recorder = self.recorders.get(track_id)
            if recorder is None:
                pending = self.pending_stitch_recorders.get(track_id)
                recorder = None if pending is None else pending.recorder
            if recorder is not None:
                self._detach_recorder_aliases_locked(recorder)
                self._detach_pending_aliases_locked(recorder)
        if recorder is None:
            return
        record = recorder.close(
            self.embedder,
            reason,
            min_clip_seconds=float(self.args.min_clip_seconds),
            tracker_backend=str(self.args.tracker_backend),
            tracker_config_path=self.tracker_config_path,
            tracker_with_reid=self.tracker_with_reid,
            source_fps=float(self.source_fps),
            analyzed_fps=float(self.analyzed_fps()),
            dropped_frame_count=int(self.dropped_frame_count),
            post_roll_seconds=float(self.args.post_roll_seconds),
            min_recorded_frames=int(self.args.min_recorded_frames),
            min_unique_frames=int(self.args.min_unique_frames),
            min_gallery_crop_quality=float(self.args.min_gallery_crop_quality),
        )
        if record is None:
            return
        if self.args.show_preview and self.args.preview_reid_crops and recorder.best_crop is not None:
            crop_preview = recorder.best_crop.copy()
            cv2.putText(
                crop_preview,
                f"ReID crop {record.cam_label} track={record.track_id} q={record.quality:.2f}",
                (8, 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )
            enqueue_preview_window("ReID selected best crops", crop_preview, 1.0)
        if self.args.storage_layout == "similarity":
            group = self.gallery.assign_similarity_group(record, float(self.args.similarity_group_threshold))
            record.similarity_group_id = int(group["group_id"])
            record.similarity_group_label = str(group["group_label"])
            record.similarity_group_score = float(group["score"])
            record.similarity_group_count = int(group["count"])
            if int(record.frame_count) >= max(0, int(self.args.similarity_min_frames)):
                record.similarity_group_export_dir = export_similarity_group_record(
                    record,
                    self.snapshot_root,
                    self.session_id,
                    str(self.args.similarity_export_mode),
                )
        added = self.gallery.add_record(record)
        if not added:
            return
        self.osc.send(
            f"/walnut/live_gallery/cam/{self.cam_id}/clip",
            [
                record.event_id,
                time.strftime("%Y-%m-%d %H:%M:%S"),
                record.clip_id,
                record.cam_id,
                record.clip_path,
                round(float(record.quality), 4),
                int(record.frame_count),
            ],
        )
        self.osc.send(f"/walnut/live_gallery/cam/{self.cam_id}/last/cam_label", record.cam_label)
        print(
            f"[gallery] Added {record.clip_id} cam={record.cam_id} label={record.cam_label} "
            f"quality={record.quality:.3f} frames={record.frame_count} unique={record.unique_frame_count} "
            f"encoded={record.encoded_duration_seconds:.2f}s"
            + (
                f" group={record.similarity_group_label} group_score={record.similarity_group_score:.3f}"
                if record.similarity_group_label
                else ""
            )
        )

    def _close_all_recorders(self, reason: str) -> None:
        with self.recorder_lock:
            recorders = self._unique_recorders_locked()
            pending_recorders = [pending.recorder for _track_id, pending in self._unique_pending_locked()]
            track_ids = [int(recorder.current_track_id or recorder.track_id) for recorder in recorders]
            pending_track_ids = [int(recorder.current_track_id or recorder.track_id) for recorder in pending_recorders]
        for track_id in track_ids:
            self._finalize_recorder(track_id, reason)
        for track_id in pending_track_ids:
            self._finalize_recorder(track_id, reason)


class CaptureWorker(threading.Thread):
    def __init__(
        self,
        context: LiveTopKCameraContext,
        stop_event: threading.Event,
        started_at: float,
    ):
        super().__init__(daemon=True)
        self.context = context
        self.stop_event = stop_event
        self.started_at = started_at

    def run(self) -> None:
        context = self.context
        print(
            f"[cam {context.cam_id}] Starting capture worker role={context.cam_type} "
            f"label={context.cam_label} source={context.source_info['display']}"
        )
        open_failures = 0
        while not self.stop_event.is_set():
            if self._runtime_expired():
                self.stop_event.set()
                break

            cap = create_capture(
                context.video_source,
                context.args.frame_width,
                context.args.frame_height,
                float(context.args.recording_fps),
                int(context.args.rtsp_open_timeout_ms),
                int(context.args.rtsp_read_timeout_ms),
            )
            if not cap.isOpened():
                open_failures += 1
                retry_delay = self._open_retry_delay(open_failures)
                print(
                    f"[cam {context.cam_id}] Failed to open {context.source_info['display']}; "
                    f"retrying in {retry_delay:.1f}s."
                )
                time.sleep(retry_delay)
                continue
            open_failures = 0

            try:
                self._capture_loop(cap)
            finally:
                cap.release()

            if source_is_finite_video(context.source_info):
                print(f"[cam {context.cam_id}] Video file ended; stopping session.")
                self.stop_event.set()
                break
            if not self.stop_event.is_set():
                time.sleep(context.args.reconnect_delay)

    def _runtime_expired(self) -> bool:
        max_runtime = float(self.context.args.max_runtime_seconds)
        return max_runtime > 0 and time.monotonic() - self.started_at >= max_runtime

    def _open_retry_delay(self, open_failures: int) -> float:
        base = max(0.1, float(self.context.args.reconnect_delay))
        cap = max(base, float(self.context.args.max_open_retry_delay))
        return min(cap, base * (2 ** min(4, max(0, int(open_failures) - 1))))

    def _capture_loop(self, cap: cv2.VideoCapture) -> None:
        context = self.context
        finite_video_interval = video_source_frame_interval(context.source_info, float(context.args.recording_fps))
        next_frame_at = time.monotonic()
        while not self.stop_event.is_set():
            if self._runtime_expired():
                self.stop_event.set()
                break

            ok, frame = cap.read()
            if not ok or frame is None:
                context.read_failures += 1
                if context.read_failures >= context.args.max_read_failures:
                    print(f"[cam {context.cam_id}] Read failure threshold reached.")
                    break
                time.sleep(0.05)
                continue

            context.read_failures = 0
            context.frame_index += 1
            captured_at = time.monotonic()
            context.update_latest_frame(frame, context.frame_index, captured_at)
            next_frame_at = sleep_for_finite_video_frame(next_frame_at, finite_video_interval, self.stop_event)


class RecordingWorker(threading.Thread):
    def __init__(
        self,
        context: LiveTopKCameraContext,
        stop_event: threading.Event,
        started_at: float,
    ):
        super().__init__(daemon=True)
        self.context = context
        self.stop_event = stop_event
        self.started_at = started_at

    def run(self) -> None:
        context = self.context
        fps = max(1.0, float(context.args.recording_fps))
        interval = 1.0 / fps
        next_tick = time.monotonic()
        print(f"[cam {context.cam_id}] Starting recording worker label={context.cam_label} fps={fps:.1f}")
        while not self.stop_event.is_set():
            if self._runtime_expired():
                self.stop_event.set()
                break
            now = time.monotonic()
            if now < next_tick:
                time.sleep(min(0.02, next_tick - now))
                continue
            context.write_recording_tick()
            next_tick = max(next_tick + interval, time.monotonic())

    def _runtime_expired(self) -> bool:
        max_runtime = float(self.context.args.max_runtime_seconds)
        return max_runtime > 0 and time.monotonic() - self.started_at >= max_runtime


class InferenceCoordinator(threading.Thread):
    def __init__(
        self,
        contexts: list[LiveTopKCameraContext],
        args: argparse.Namespace,
        stop_event: threading.Event,
        started_at: float,
    ):
        super().__init__(daemon=True)
        self.contexts = contexts
        self.args = args
        self.stop_event = stop_event
        self.started_at = started_at

    def run(self) -> None:
        print(
            "[inference] Starting round-robin coordinator "
            f"tracker={self.args.tracker_backend} interval={self.args.inference_interval}"
        )
        while not self.stop_event.is_set():
            if self._runtime_expired():
                self.stop_event.set()
                break

            processed_any = False
            for context in self.contexts:
                if self.stop_event.is_set():
                    break
                processed_any = context.process_next_analysis() or processed_any

            if not processed_any:
                time.sleep(0.005)

    def _runtime_expired(self) -> bool:
        max_runtime = float(self.args.max_runtime_seconds)
        return max_runtime > 0 and time.monotonic() - self.started_at >= max_runtime


def main() -> int:
    args = parse_args()
    snapshot_root = resolve_project_path(args.snapshot_dir)
    snapshot_root.mkdir(parents=True, exist_ok=True)

    sources = split_sources(args.rtsp, args.rtsp_envs)
    cam_types = split_cam_types(args.cam_types, len(sources))
    cam_labels = split_cam_labels(args.cam_labels, len(sources))
    if not args.skip_webcam_preflight:
        preflight_webcams(sources, args.frame_width, args.frame_height, float(args.recording_fps))
    session_id = time.strftime("%Y%m%d_%H%M%S")
    log_dir = PROJECT_ROOT / "logs" / "topk_live" / session_id

    gallery = LiveTopKGallery(log_dir)
    embedder = AppearanceEmbedder(model_name=args.embedding_model)
    osc = OscSender(args.osc_host, args.osc_port, args.osc_dry_run, args.disable_osc)
    stop_event = threading.Event()
    tracker_config_path = resolve_tracker_config_path(str(args.tracker_backend), str(args.tracker_config_path))
    tracker_with_reid = tracker_config_with_reid(tracker_config_path)

    print("Starting live YOLO-ReID Top-K bridge.")
    print(f"Session: {session_id}")
    print(f"OSC target: {args.osc_host}:{args.osc_port} dry_run={args.osc_dry_run} disabled={args.disable_osc}")
    print(f"Snapshot root: {snapshot_root}")
    print(f"Record video mode: {args.record_video_mode} recording_fps={float(args.recording_fps):.1f}")
    print(
        f"Tracker backend: {args.tracker_backend} "
        f"tracker_config={display_project_path(tracker_config_path) or 'default'} "
        f"tracker_with_reid={tracker_with_reid} "
        f"inference_interval={args.inference_interval} "
        f"post_roll_seconds={args.post_roll_seconds} "
        f"min_clip_seconds={args.min_clip_seconds} "
        f"min_recorded_frames={args.min_recorded_frames} "
        f"min_unique_frames={args.min_unique_frames} "
        f"stale_frame_seconds={args.recording_stale_frame_seconds} "
        f"reconnect_grace_seconds={args.recording_reconnect_grace_seconds}"
    )
    print(
        f"Tracklet stitching: enabled={not args.disable_tracklet_stitching} "
        f"window={args.stitch_window_seconds}s "
        f"reid_threshold={args.stitch_reid_threshold} "
        f"ambiguous_margin={args.stitch_ambiguous_margin} "
        f"max_center_distance={args.stitch_max_center_distance_ratio} "
        f"crowded_window={args.stitch_crowded_window_seconds}s "
        f"allow_crowded={args.stitch_allow_crowded}"
    )
    print(
        f"Crop prototypes: strategy={args.crop_selection_strategy} "
        f"top_n={args.live_visual_top_n} "
        f"score_mode={args.prototype_score_mode} "
        f"min_frame_gap={args.crop_diversity_min_frame_gap} "
        f"max_similarity={args.crop_diversity_max_similarity} "
        f"min_quality_ratio={args.crop_min_quality_ratio}"
    )
    print(f"Embedding model: {args.embedding_model} method={embedder.method} device={embedder.device}")
    if args.show_preview:
        print("Preview windows: enabled. Press q or Esc in a preview window to stop.")
    print(
        f"Storage layout: {args.storage_layout} "
        f"similarity_threshold={args.similarity_group_threshold} "
        f"similarity_export_mode={args.similarity_export_mode} "
        f"session_end_merge={not args.no_session_end_merge} "
        f"merge_method={args.merge_method} "
        f"merge_threshold={args.merge_threshold} "
        f"merge_reciprocal_topn={args.merge_reciprocal_topn}"
    )
    if args.export_topk_dir:
        print(f"Top-K export root: {resolve_project_path(args.export_topk_dir)} mode={args.export_mode}")
    print(f"Log dir: {log_dir}")
    for index, (source, cam_type, cam_label) in enumerate(zip(sources, cam_types, cam_labels), start=1):
        print(f"cam{index}: role={cam_type} label={cam_label} source={parse_video_source(source)['display']}")

    contexts = [
        LiveTopKCameraContext(
            cam_id=index,
            cam_label=cam_label,
            cam_type=cam_type,
            video_source=source,
            args=args,
            session_id=session_id,
            gallery=gallery,
            embedder=embedder,
            osc=osc,
            stop_event=stop_event,
        )
        for index, (source, cam_type, cam_label) in enumerate(zip(sources, cam_types, cam_labels), start=1)
    ]

    started_at = time.monotonic()
    capture_workers = [CaptureWorker(context, stop_event, started_at) for context in contexts]
    recording_workers = [RecordingWorker(context, stop_event, started_at) for context in contexts]
    inference_worker = InferenceCoordinator(contexts, args, stop_event, started_at)

    for worker in capture_workers:
        worker.start()
    for worker in recording_workers:
        worker.start()
    inference_worker.start()

    try:
        while any(worker.is_alive() for worker in capture_workers) and not stop_event.is_set():
            if args.show_preview and process_preview_events():
                stop_event.set()
                break
            time.sleep(0.03 if args.show_preview else 0.5)
    except KeyboardInterrupt:
        print("\nStopping live Top-K bridge...")
        stop_event.set()
    finally:
        stop_event.set()
        for worker in capture_workers:
            worker.join(timeout=5.0)
        for worker in recording_workers:
            worker.join(timeout=5.0)
        inference_worker.join(timeout=5.0)
        for context in contexts:
            context._close_all_recorders("shutdown")
        if args.show_preview:
            with PREVIEW_LOCK:
                cv2.destroyAllWindows()
        if args.storage_layout == "similarity" and not args.no_session_end_merge and gallery.count() > 0:
            try:
                merge_payload = regroup_live_session(
                    session_id=session_id,
                    embedding_model=args.embedding_model,
                    method=args.merge_method,
                    threshold=float(args.merge_threshold),
                    reciprocal_topn=int(args.merge_reciprocal_topn),
                    export_mode=str(args.similarity_export_mode),
                    snapshot_root=resolve_project_path(args.snapshot_dir),
                    output_subdir=str(args.merge_output_subdir),
                    write_report=log_dir / "merged_similarity_groups_report.md",
                )
                grouping = merge_payload["grouping"]
                print(
                    "[merge] Session-end regroup complete "
                    f"groups={grouping['group_count']} sizes={grouping['group_sizes']} "
                    f"output={merge_payload['output_dir']}"
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[merge] Session-end regroup failed: {exc!r}")

    print(f"Stopped. Gallery records: {gallery.count()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
