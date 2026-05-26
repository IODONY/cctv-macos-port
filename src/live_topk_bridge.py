#!/usr/bin/env python3
"""Live YOLO person clips -> appearance embedding -> Top-K OSC bridge.

This runtime is intentionally track-centric:
- Gallery cameras record one cropped clip per detected local person track.
- Recording starts when YOLO first sees the person and ends when that track
  disappears for a small grace window.
- Each finished track stores a best ReID crop and an appearance embedding.
- Query cameras periodically embed the current target person and send ranked
  clip paths to TouchDesigner.
"""

from __future__ import annotations

import argparse
import json
import os
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

from visual_reid import (
    TorchvisionEmbedder,
    crop_person as visual_crop_person,
    crop_quality as visual_crop_quality,
    resize_with_padding as visual_resize_with_padding,
)
from walnut_core import WalnutAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_CACHE_ROOT = PROJECT_ROOT / "logs" / "model_cache" / "torch"
GALLERY_TYPES = {"A", "B", "G"}
QUERY_TYPES = {"C", "Q"}


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
    parser.add_argument("--snapshot-dir", default="snapshots/live_topk")
    parser.add_argument("--clip-width", type=int, default=320)
    parser.add_argument("--clip-height", type=int, default=640)
    parser.add_argument("--track-missing-grace", type=int, default=8)
    parser.add_argument(
        "--max-clip-seconds",
        type=float,
        default=30.0,
        help="Safety cutoff for a single person track clip; disappearance still ends clips earlier.",
    )
    parser.add_argument("--reconnect-delay", type=float, default=2.0)
    parser.add_argument("--max-read-failures", type=int, default=10)
    parser.add_argument("--query-interval-seconds", type=float, default=1.0)
    parser.add_argument("--topk", type=int, default=9)
    parser.add_argument("--candidate-pool", type=int, default=12)
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


def crop_quality(crop: np.ndarray | None, person: dict[str, object]) -> float:
    if crop is None or crop.size == 0:
        return 0.0
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    sharpness = min(1.0, float(cv2.Laplacian(gray, cv2.CV_64F).var()) / 900.0)
    crop_area = float(crop.shape[0] * crop.shape[1])
    area_score = min(1.0, crop_area / float(260 * 520))
    confidence = min(1.0, max(0.0, float(person.get("confidence", 0.0))))
    return (confidence * 0.45) + (sharpness * 0.30) + (area_score * 0.25)


class AppearanceEmbedder(TorchvisionEmbedder):
    def __init__(self, cache_root: Path = MODEL_CACHE_ROOT):
        super().__init__(
            model_name="mobilenet_v3_large",
            cache_root=cache_root,
            color_weight=0.20,
        )


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

    def to_json(self) -> dict[str, object]:
        return {
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
        }


class LiveTopKGallery:
    def __init__(self, log_dir: Path):
        self.lock = threading.Lock()
        self.records: list[GalleryRecord] = []
        self.seen_clip_ids: set[str] = set()
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.gallery_log_path = self.log_dir / "gallery_events.jsonl"
        self.query_log_path = self.log_dir / "query_results.jsonl"

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
                }
            )
        return results[:k]

    def log_query(self, payload: dict[str, object]) -> None:
        self._append_jsonl(self.query_log_path, payload)

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
    ):
        event_id = str(int(time.time() * 1000))
        safe_session = sanitize_id(session_id)
        safe_cam = f"cam_{cam_id}"
        clip_id = f"live_{safe_session}_{safe_cam}_track_{track_id}_event_{event_id}"
        clip_dir = snapshot_root / safe_session / safe_cam
        self.clip_id = clip_id
        self.event_id = event_id
        self.cam_id = safe_cam
        self.cam_label = sanitize_id(cam_label)
        self.track_id = int(track_id)
        self.clip_path = clip_dir / f"{clip_id}.mp4"
        self.best_frame_path = clip_dir / f"{clip_id}_best.jpg"
        self.output_size = output_size
        self.writer, self.codec = create_clip_writer(self.clip_path, fps, output_size)
        self.started_at = time.monotonic()
        self.created_at = time.time()
        self.last_box = None
        self.last_person: dict[str, object] | None = None
        self.missing_analyses = 0
        self.frame_count = 0
        self.best_crop = None
        self.best_quality = -1.0
        self.closed = False
        if self.writer is None:
            print(f"[gallery] Failed to open clip writer: {self.clip_path}")
        else:
            print(f"[gallery] Recording track {track_id} with {self.codec}: {self.clip_path}")

    def observe(self, frame: np.ndarray, person: dict[str, object]) -> None:
        self.last_box = tuple(int(value) for value in person["box"])
        self.last_person = person
        self.missing_analyses = 0
        crop = visual_crop_person(frame, self.last_box)
        quality = visual_crop_quality(crop, person, frame.shape)
        if crop is not None and quality > self.best_quality:
            self.best_crop = crop
            self.best_quality = quality

    def write_frame(self, frame: np.ndarray) -> None:
        if self.writer is None or self.last_box is None or self.closed:
            return
        crop = visual_crop_person(frame, self.last_box)
        if crop is None:
            return
        self.writer.write(visual_resize_with_padding(crop, self.output_size))
        self.frame_count += 1

    def should_force_close(self, max_clip_seconds: float) -> bool:
        if max_clip_seconds <= 0:
            return False
        return (time.monotonic() - self.started_at) >= max_clip_seconds

    def close(self, embedder: AppearanceEmbedder, reason: str) -> GalleryRecord | None:
        if self.closed:
            return None
        self.closed = True
        if self.writer is None:
            print(f"[gallery] Dropped track {self.track_id}; clip writer was unavailable: {reason}")
            return None
        if self.writer is not None:
            self.writer.release()

        if self.best_crop is None:
            print(f"[gallery] Dropped empty track {self.track_id}: {reason}")
            return None

        self.best_frame_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(self.best_frame_path), self.best_crop)
        embedding, method = embedder.embed_bgr(self.best_crop)
        if embedding is None:
            print(f"[gallery] No embedding for track {self.track_id}: {self.clip_path}")
            return None

        duration = time.monotonic() - self.started_at
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


class LiveTopKCameraWorker(threading.Thread):
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
        super().__init__(daemon=True)
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
        self.last_query_sent_at = 0.0

        self.analyzer = WalnutAnalyzer(
            pose_model_name="yolov8n-pose.pt",
            detect_model_name="yolov8n.pt",
            person_confidence=0.45,
            pose_confidence=0.35,
            accessory_confidence=0.18,
            model_imgsz=640,
            vote_frame_window=20,
            track_max_missing=max(5, int(args.track_missing_grace) + 2),
        )

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
                self._handle_gallery_people(frame, people)
            else:
                self._handle_query_people(frame, people)
            self._send_status(people)

            if self.analyzed_frames % max(1, self.args.print_interval_frames) == 0:
                print(
                    f"[cam {self.cam_id}] role={self.cam_type} people={len(people)} "
                    f"gallery={self.gallery.count()} inference_ms={self.analyzer.last_inference_ms:.1f}"
                )

    def _write_active_recorders(self, frame: np.ndarray) -> None:
        for recorder in list(self.recorders.values()):
            recorder.write_frame(frame)
            if recorder.should_force_close(self.args.max_clip_seconds):
                self._finalize_recorder(recorder.track_id, "max_clip_seconds")

    def _handle_gallery_people(self, frame: np.ndarray, people: list[dict[str, object]]) -> None:
        current_track_ids = {int(person.get("track_id", 0)) for person in people}
        for track_id, recorder in list(self.recorders.items()):
            if track_id not in current_track_ids:
                recorder.missing_analyses += 1
                if recorder.missing_analyses > max(1, int(self.args.track_missing_grace)):
                    self._finalize_recorder(track_id, "person_left_frame")

        for person in people:
            track_id = int(person.get("track_id", 0))
            if track_id <= 0:
                continue
            recorder = self.recorders.get(track_id)
            if recorder is None:
                recorder = PersonClipRecorder(
                    self.session_id,
                    self.snapshot_root,
                    self.cam_id,
                    self.cam_label,
                    track_id,
                    self.output_size,
                    fps=30.0,
                )
                self.recorders[track_id] = recorder
            recorder.observe(frame, person)

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
        self.osc.send(f"{base}/active_recordings", int(len(self.recorders)))

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
        recorder = self.recorders.pop(track_id, None)
        if recorder is None:
            return
        record = recorder.close(self.embedder, reason)
        if record is None:
            return
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
        )

    def _close_all_recorders(self, reason: str) -> None:
        for track_id in list(self.recorders):
            self._finalize_recorder(track_id, reason)


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
    embedder = AppearanceEmbedder(MODEL_CACHE_ROOT)
    osc = OscSender(args.osc_host, args.osc_port, args.osc_dry_run, args.disable_osc)
    stop_event = threading.Event()

    print("Starting live YOLO-ReID Top-K bridge.")
    print(f"Session: {session_id}")
    print(f"OSC target: {args.osc_host}:{args.osc_port} dry_run={args.osc_dry_run} disabled={args.disable_osc}")
    print(f"Snapshot root: {snapshot_root}")
    if args.export_topk_dir:
        print(f"Top-K export root: {resolve_project_path(args.export_topk_dir)} mode={args.export_mode}")
    print(f"Log dir: {log_dir}")
    for index, (source, cam_type, cam_label) in enumerate(zip(sources, cam_types, cam_labels), start=1):
        print(f"cam{index}: role={cam_type} label={cam_label} source={parse_video_source(source)['display']}")

    workers = [
        LiveTopKCameraWorker(
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

    for worker in workers:
        worker.start()

    try:
        while any(worker.is_alive() for worker in workers):
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping live Top-K bridge...")
        stop_event.set()
    finally:
        stop_event.set()
        for worker in workers:
            worker.join(timeout=5.0)

    print(f"Stopped. Gallery records: {gallery.count()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
