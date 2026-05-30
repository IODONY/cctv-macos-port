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
    create_visual_embedder,
    crop_person as visual_crop_person,
    crop_quality as visual_crop_quality,
    resize_with_padding as visual_resize_with_padding,
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
        default=0.55,
        help="Cosine threshold for final session-end merged similarity groups.",
    )
    parser.add_argument(
        "--merge-reciprocal-topn",
        type=int,
        default=5,
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
        "--min-clip-seconds",
        type=float,
        default=1.5,
        help="Closed gallery clips shorter than this are kept on disk but not added to the ReID gallery.",
    )
    parser.add_argument(
        "--max-clip-seconds",
        type=float,
        default=30.0,
        help="Safety cutoff for a single person track clip; disappearance still ends clips earlier.",
    )
    parser.add_argument("--reconnect-delay", type=float, default=2.0)
    parser.add_argument("--max-read-failures", type=int, default=10)
    parser.add_argument("--query-interval-seconds", type=float, default=1.0)
    parser.add_argument("--topk", type=int, default=7)
    parser.add_argument("--candidate-pool", type=int, default=12)
    parser.add_argument(
        "--live-visual-top-n",
        type=int,
        default=3,
        help="Number of best live person crops to average into a gallery tracklet embedding.",
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


def create_capture(video_source: str, frame_width: int, frame_height: int) -> cv2.VideoCapture:
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
        cap.set(cv2.CAP_PROP_FPS, 30)
    else:
        cap = cv2.VideoCapture(source_info["capture_source"], cv2.CAP_FFMPEG)
        if not cap.isOpened():
            cap = cv2.VideoCapture(source_info["capture_source"])

    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def preflight_webcams(sources: list[str], frame_width: int, frame_height: int) -> None:
    for source in sources:
        source_info = parse_video_source(source)
        if source_info["kind"] != "webcam":
            continue
        print(f"[preflight] Opening {source_info['display']} on main thread for camera authorization.")
        cap = create_capture(source, frame_width, frame_height)
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
    embedding_method: str
    embedding_aggregation: str = "single_best"
    tracker_backend: str = "custom"
    source_fps: float = 0.0
    analyzed_fps: float = 0.0
    dropped_frame_count: int = 0
    post_roll_seconds: float = 0.0
    top_crop_paths: list[str] | None = None
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
            "embedding_method": self.embedding_method,
            "embedding_aggregation": self.embedding_aggregation,
            "tracker_backend": self.tracker_backend,
            "source_fps": round(float(self.source_fps), 3),
            "analyzed_fps": round(float(self.analyzed_fps), 3),
            "dropped_frame_count": int(self.dropped_frame_count),
            "post_roll_seconds": round(float(self.post_roll_seconds), 3),
        }
        if self.top_crop_paths:
            payload["top_crop_paths"] = list(self.top_crop_paths)
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

        with self.lock:
            best_group = None
            best_score = -1.0
            for group in self.similarity_groups:
                centroid = np.asarray(group["centroid"], dtype=np.float32)
                score = float(np.dot(embedding, centroid))
                if score > best_score:
                    best_score = score
                    best_group = group

            if best_group is None or best_score < float(threshold):
                group_id = len(self.similarity_groups) + 1
                best_group = {
                    "group_id": group_id,
                    "group_label": f"group_{group_id:03d}",
                    "centroid": embedding,
                    "count": 0,
                }
                self.similarity_groups.append(best_group)
                best_score = 1.0

            count = int(best_group["count"]) + 1
            centroid = np.asarray(best_group["centroid"], dtype=np.float32)
            updated_centroid = normalize_vector((centroid * float(best_group["count"])) + embedding)
            best_group["centroid"] = embedding if updated_centroid is None else updated_centroid
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
            score = float(np.dot(query, record.embedding))
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
    ):
        event_id = str(int(time.time() * 1000))
        safe_session = sanitize_id(session_id)
        safe_cam = f"cam_{cam_id}"
        safe_cam_label = sanitize_id(cam_label) or safe_cam
        clip_id = f"live_{safe_session}_{safe_cam_label}_track_{track_id}_event_{event_id}"
        clip_dir = snapshot_root / safe_session / safe_cam_label
        self.clip_id = clip_id
        self.event_id = event_id
        self.cam_id = safe_cam
        self.cam_label = safe_cam_label
        self.track_id = int(track_id)
        self.clip_path = clip_dir / f"{clip_id}.mp4"
        self.best_frame_path = clip_dir / f"{clip_id}_best.jpg"
        self.output_size = output_size
        self.record_video_mode = record_video_mode
        self.top_n = max(1, int(top_n))
        self.writer, self.codec = create_clip_writer(self.clip_path, fps, output_size)
        self.started_at = time.monotonic()
        self.created_at = time.time()
        self.last_observed_at = self.started_at
        self.missing_since: float | None = None
        self.last_box = None
        self.last_person: dict[str, object] | None = None
        self.missing_analyses = 0
        self.frame_count = 0
        self.best_crop = None
        self.best_quality = -1.0
        self.crop_candidates: list[dict[str, object]] = []
        self.closed = False
        if self.writer is None:
            print(f"[gallery] Failed to open clip writer: {self.clip_path}")
        else:
            print(f"[gallery] Recording track {track_id} with {self.codec}: {self.clip_path}")

    def observe(self, frame: np.ndarray, person: dict[str, object], frame_index: int = 0) -> None:
        self.last_box = tuple(int(value) for value in person["box"])
        self.last_person = person
        self.last_observed_at = time.monotonic()
        self.missing_since = None
        self.missing_analyses = 0
        crop = visual_crop_person(frame, self.last_box)
        quality = visual_crop_quality(crop, person, frame.shape)
        if crop is not None:
            self.crop_candidates.append(
                {
                    "crop": crop,
                    "quality": float(quality),
                    "frame_index": int(frame_index),
                    "box": [int(value) for value in self.last_box],
                    "confidence": float(person.get("confidence", 0.0)),
                }
            )
            self.crop_candidates.sort(key=lambda item: float(item["quality"]), reverse=True)
            self.crop_candidates = self.crop_candidates[: self.top_n]
            best = self.crop_candidates[0]
            self.best_crop = best["crop"]
            self.best_quality = float(best["quality"])

    def mark_missing(self, now: float | None = None) -> None:
        self.missing_analyses += 1
        if self.missing_since is None:
            self.missing_since = time.monotonic() if now is None else float(now)

    def should_close_after_missing(self, post_roll_seconds: float, track_missing_grace: int) -> bool:
        if self.missing_since is None:
            return False
        now = time.monotonic()
        if post_roll_seconds >= 0 and (now - self.missing_since) >= float(post_roll_seconds):
            return True
        return self.missing_analyses > max(1, int(track_missing_grace))

    def write_frame(self, frame: np.ndarray) -> None:
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
        source_fps: float = 0.0,
        analyzed_fps: float = 0.0,
        dropped_frame_count: int = 0,
        post_roll_seconds: float = 0.0,
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
        if duration < max(0.0, float(min_clip_seconds)):
            print(
                f"[gallery] Kept short clip on disk but skipped ReID gallery track {self.track_id}: "
                f"duration={duration:.2f}s min={float(min_clip_seconds):.2f}s reason={reason}"
            )
            return None

        if self.best_crop is None:
            print(f"[gallery] Dropped empty track {self.track_id}: {reason}")
            return None

        self.best_frame_path.parent.mkdir(parents=True, exist_ok=True)
        top_crop_paths: list[str] = []
        crop_embeddings = []
        methods = []
        for index, candidate in enumerate(self.crop_candidates[: self.top_n], start=1):
            crop = candidate["crop"]
            if index == 1:
                crop_path = self.best_frame_path
            else:
                crop_path = self.best_frame_path.with_name(
                    f"{self.best_frame_path.stem}_crop_{index:03d}{self.best_frame_path.suffix}"
                )
            cv2.imwrite(str(crop_path), crop)
            top_crop_paths.append(str(crop_path.resolve()).replace("\\", "/"))
            embedding, method = embedder.embed_bgr(crop)
            if embedding is not None:
                crop_embeddings.append(embedding)
                methods.append(method)

        if crop_embeddings:
            embedding = normalize_vector(np.vstack(crop_embeddings).mean(axis=0))
            method = methods[-1] if methods else embedder.method
        else:
            embedding, method = embedder.embed_bgr(self.best_crop)
        if embedding is None:
            print(f"[gallery] No embedding for track {self.track_id}: {self.clip_path}")
            return None

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
            embedding_method=method,
            embedding_aggregation=f"mean_top_{len(crop_embeddings)}" if crop_embeddings else "single_best",
            tracker_backend=str(tracker_backend),
            source_fps=float(source_fps),
            analyzed_fps=float(analyzed_fps),
            dropped_frame_count=int(dropped_frame_count),
            post_roll_seconds=float(post_roll_seconds),
            top_crop_paths=top_crop_paths,
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
        tracker_config_path = resolve_project_path(args.tracker_config_path) if args.tracker_config_path else None

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

    def analyzed_fps(self) -> float:
        elapsed = time.monotonic() - self.started_at
        if elapsed <= 0:
            return 0.0
        return float(self.analyzed_frames) / elapsed

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
        while not self.stop_event.is_set():
            if self.args.max_runtime_seconds > 0 and time.monotonic() - started >= self.args.max_runtime_seconds:
                self.stop_event.set()
                break

            cap = create_capture(self.video_source, self.args.frame_width, self.args.frame_height)
            if not cap.isOpened():
                print(f"[cam {self.cam_id}] Failed to open {self.source_info['display']}; retrying.")
                time.sleep(self.args.reconnect_delay)
                continue

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

    def _write_active_recorders(self, frame: np.ndarray) -> None:
        force_close_track_ids = []
        with self.recorder_lock:
            for recorder in list(self.recorders.values()):
                recorder.write_frame(frame)
                if recorder.should_force_close(self.args.max_clip_seconds):
                    force_close_track_ids.append(recorder.track_id)
        for track_id in force_close_track_ids:
            self._finalize_recorder(track_id, "max_clip_seconds")

    def _handle_gallery_people(
        self,
        frame: np.ndarray,
        people: list[dict[str, object]],
        source_frame_index: int = 0,
    ) -> None:
        current_track_ids = {int(person.get("track_id", 0)) for person in people}
        now = time.monotonic()
        close_track_ids = []
        with self.recorder_lock:
            for track_id, recorder in list(self.recorders.items()):
                if track_id not in current_track_ids:
                    recorder.mark_missing(now)
                    if recorder.should_close_after_missing(
                        float(self.args.post_roll_seconds),
                        int(self.args.track_missing_grace),
                    ):
                        close_track_ids.append(track_id)
        for track_id in close_track_ids:
            self._finalize_recorder(track_id, "person_left_frame")

        for person in people:
            track_id = int(person.get("track_id", 0))
            if track_id <= 0:
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
                        fps=30.0,
                        record_video_mode=str(self.args.record_video_mode),
                        top_n=max(1, int(self.args.live_visual_top_n)),
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
            return len(self.recorders)

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
            recorder = self.recorders.pop(track_id, None)
        if recorder is None:
            return
        record = recorder.close(
            self.embedder,
            reason,
            min_clip_seconds=float(self.args.min_clip_seconds),
            tracker_backend=str(self.args.tracker_backend),
            source_fps=float(self.source_fps),
            analyzed_fps=float(self.analyzed_fps()),
            dropped_frame_count=int(self.dropped_frame_count),
            post_roll_seconds=float(self.args.post_roll_seconds),
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
            f"quality={record.quality:.3f} frames={record.frame_count}"
            + (
                f" group={record.similarity_group_label} group_score={record.similarity_group_score:.3f}"
                if record.similarity_group_label
                else ""
            )
        )

    def _close_all_recorders(self, reason: str) -> None:
        with self.recorder_lock:
            track_ids = list(self.recorders)
        for track_id in track_ids:
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
        while not self.stop_event.is_set():
            if self._runtime_expired():
                self.stop_event.set()
                break

            cap = create_capture(context.video_source, context.args.frame_width, context.args.frame_height)
            if not cap.isOpened():
                print(f"[cam {context.cam_id}] Failed to open {context.source_info['display']}; retrying.")
                time.sleep(context.args.reconnect_delay)
                continue

            try:
                self._capture_loop(cap)
            finally:
                cap.release()
                context._close_all_recorders("capture_closed")

            if not self.stop_event.is_set():
                time.sleep(context.args.reconnect_delay)

    def _runtime_expired(self) -> bool:
        max_runtime = float(self.context.args.max_runtime_seconds)
        return max_runtime > 0 and time.monotonic() - self.started_at >= max_runtime

    def _capture_loop(self, cap: cv2.VideoCapture) -> None:
        context = self.context
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
            context._write_active_recorders(frame)


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
        preflight_webcams(sources, args.frame_width, args.frame_height)
    session_id = time.strftime("%Y%m%d_%H%M%S")
    log_dir = PROJECT_ROOT / "logs" / "topk_live" / session_id

    gallery = LiveTopKGallery(log_dir)
    embedder = AppearanceEmbedder(model_name=args.embedding_model)
    osc = OscSender(args.osc_host, args.osc_port, args.osc_dry_run, args.disable_osc)
    stop_event = threading.Event()

    print("Starting live YOLO-ReID Top-K bridge.")
    print(f"Session: {session_id}")
    print(f"OSC target: {args.osc_host}:{args.osc_port} dry_run={args.osc_dry_run} disabled={args.disable_osc}")
    print(f"Snapshot root: {snapshot_root}")
    print(f"Record video mode: {args.record_video_mode}")
    print(
        f"Tracker backend: {args.tracker_backend} "
        f"inference_interval={args.inference_interval} "
        f"post_roll_seconds={args.post_roll_seconds} "
        f"min_clip_seconds={args.min_clip_seconds}"
    )
    print(f"Embedding model: {args.embedding_model} method={embedder.method} device={embedder.device}")
    if args.show_preview:
        print("Preview windows: enabled. Press q or Esc in a preview window to stop.")
    print(
        f"Storage layout: {args.storage_layout} "
        f"similarity_threshold={args.similarity_group_threshold} "
        f"similarity_export_mode={args.similarity_export_mode} "
        f"session_end_merge={not args.no_session_end_merge}"
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
    inference_worker = InferenceCoordinator(contexts, args, stop_event, started_at)

    for worker in capture_workers:
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
        inference_worker.join(timeout=5.0)
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
