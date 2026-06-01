#!/usr/bin/env python3
"""Shared best-shot crop and lightweight visual embedding helpers."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_CACHE_ROOT = PROJECT_ROOT / "logs" / "model_cache" / "torch"
TORCHREID_CACHE_ROOT = PROJECT_ROOT / "logs" / "model_cache" / "torchreid"
OSNET_X0_25_MSMT17_FILE_ID = "1Kkx2zW89jq_NETu4u42CFZTMVD5Hwm6e"


def normalize_vector(vector: np.ndarray | None) -> np.ndarray | None:
    if vector is None:
        return None
    array = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(array))
    if norm <= 1e-8:
        return None
    return array / norm


def sanitize_filename(value: object) -> str:
    text = str(value)
    allowed = []
    for char in text:
        allowed.append(char if char.isalnum() or char in "._-" else "_")
    return "".join(allowed).strip("_") or "unknown"


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def crop_person(frame: np.ndarray, box: Iterable[int], expand_ratio: float = 0.10) -> np.ndarray | None:
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = [int(value) for value in box]
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


def image_sharpness(image: np.ndarray | None) -> float:
    if image is None or image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def crop_quality(
    crop: np.ndarray | None,
    person: dict[str, object],
    frame_shape: tuple[int, int] | tuple[int, int, int] | None = None,
) -> float:
    if crop is None or crop.size == 0:
        return 0.0

    crop_h, crop_w = crop.shape[:2]
    crop_area = float(crop_h * crop_w)
    sharpness_score = min(1.0, image_sharpness(crop) / 900.0)
    confidence_score = min(1.0, max(0.0, float(person.get("confidence", 0.0))))
    area_score = min(1.0, crop_area / float(260 * 520))

    aspect = float(crop_h) / float(max(1, crop_w))
    aspect_score = 1.0 - min(1.0, abs(aspect - 2.1) / 1.8)

    center_score = 0.5
    full_body_score = 0.5
    if frame_shape is not None:
        frame_h, frame_w = int(frame_shape[0]), int(frame_shape[1])
        x1, y1, x2, y2 = [int(value) for value in person.get("box", (0, 0, 0, 0))]
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        dx = abs(cx - (frame_w / 2.0)) / max(1.0, frame_w / 2.0)
        dy = abs(cy - (frame_h / 2.0)) / max(1.0, frame_h / 2.0)
        center_score = 1.0 - min(1.0, (dx * 0.7) + (dy * 0.3))
        body_height_ratio = max(0.0, float(y2 - y1)) / float(max(1, frame_h))
        full_body_score = min(1.0, body_height_ratio / 0.68)

    return float(
        (confidence_score * 0.30)
        + (sharpness_score * 0.22)
        + (area_score * 0.18)
        + (center_score * 0.12)
        + (aspect_score * 0.10)
        + (full_body_score * 0.08)
    )


def color_histogram_bgr(image_bgr: np.ndarray | None) -> np.ndarray | None:
    if image_bgr is None or image_bgr.size == 0:
        return None
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 4], [0, 180, 0, 256, 0, 256])
    return normalize_vector(hist.reshape(-1))


@dataclass
class CropCandidate:
    frame_index: int
    quality: float
    confidence: float
    box: tuple[int, int, int, int]
    crop: np.ndarray
    crop_path: str = ""
    time_bucket: str = ""
    pose_view_hint: str = "back_or_unknown"
    body_angle_hint: dict[str, object] | None = None
    diversity_cluster_id: int = 0
    selection_reason: str = ""

    def to_json(self) -> dict[str, object]:
        return {
            "frame_index": int(self.frame_index),
            "quality": round(float(self.quality), 4),
            "confidence": round(float(self.confidence), 4),
            "box": [int(value) for value in self.box],
            "crop_path": self.crop_path,
            "time_bucket": self.time_bucket,
            "pose_view_hint": self.pose_view_hint,
            "body_angle_hint": self.body_angle_hint or {},
            "diversity_cluster_id": int(self.diversity_cluster_id),
            "selection_reason": self.selection_reason,
        }


def _line_length(line: object) -> float:
    try:
        left, right = line  # type: ignore[misc]
        lx, ly = left
        rx, ry = right
        return float(np.hypot(float(rx) - float(lx), float(ry) - float(ly)))
    except Exception:  # noqa: BLE001
        return 0.0


def _line_angle(line: object) -> float | None:
    try:
        left, right = line  # type: ignore[misc]
        lx, ly = left
        rx, ry = right
        return round(float(np.degrees(np.arctan2(float(ry) - float(ly), float(rx) - float(lx)))), 3)
    except Exception:  # noqa: BLE001
        return None


def infer_pose_metadata(person: dict[str, object], box: Iterable[int]) -> tuple[str, dict[str, object]]:
    x1, y1, x2, y2 = [int(value) for value in box]
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    bbox_aspect = round(float(box_h) / float(box_w), 4)

    torso_lines = person.get("torso_lines") if isinstance(person, dict) else {}
    torso_lines = torso_lines if isinstance(torso_lines, dict) else {}
    shoulder_width = _line_length(torso_lines.get("shoulders"))
    hip_width = _line_length(torso_lines.get("hips"))
    shoulder_angle = _line_angle(torso_lines.get("shoulders"))
    hip_angle = _line_angle(torso_lines.get("hips"))
    torso_visibility = int(shoulder_width > 0.0) + int(hip_width > 0.0)

    face_visibility = person.get("face_visibility") if isinstance(person, dict) else {}
    face_visibility = face_visibility if isinstance(face_visibility, dict) else {}
    face_count = int(face_visibility.get("visible_count") or 0)
    has_nose = bool(face_visibility.get("has_nose"))
    has_eyes = bool(face_visibility.get("has_eyes"))

    width_ratio = 0.0
    if shoulder_width > 0.0 and hip_width > 0.0:
        width_ratio = round(float(shoulder_width) / max(1e-6, float(hip_width)), 4)

    if has_nose and has_eyes and face_count >= 3:
        pose_view_hint = "front_like"
    elif torso_visibility >= 1 and (bbox_aspect >= 2.15 or (0.0 < width_ratio < 0.78)):
        pose_view_hint = "side_like"
    elif face_count <= 1:
        pose_view_hint = "back_or_unknown"
    else:
        pose_view_hint = "side_like"

    body_angle_hint = {
        "bbox_aspect": bbox_aspect,
        "shoulder_width": round(float(shoulder_width), 3),
        "hip_width": round(float(hip_width), 3),
        "shoulder_hip_ratio": width_ratio,
        "shoulder_angle": shoulder_angle,
        "hip_angle": hip_angle,
        "torso_visibility": torso_visibility,
        "face_visible_count": face_count,
        "has_nose": has_nose,
        "has_eyes": has_eyes,
    }
    return pose_view_hint, body_angle_hint


def make_crop_candidate(
    frame_index: int,
    crop: np.ndarray,
    person: dict[str, object],
    frame_shape: tuple[int, ...],
    quality: float | None = None,
) -> dict[str, object]:
    box = tuple(int(value) for value in person["box"])
    pose_view_hint, body_angle_hint = infer_pose_metadata(person, box)
    return {
        "crop": crop,
        "quality": float(crop_quality(crop, person, frame_shape) if quality is None else quality),
        "frame_index": int(frame_index),
        "box": [int(value) for value in box],
        "confidence": float(person.get("confidence", 0.0)),
        "time_bucket": "",
        "pose_view_hint": pose_view_hint,
        "body_angle_hint": body_angle_hint,
        "diversity_cluster_id": 0,
        "selection_reason": "",
    }


def crop_candidate_to_json(candidate: dict[str, object], crop_path: str = "") -> dict[str, object]:
    return {
        "rank": int(candidate.get("rank") or 0),
        "path": crop_path,
        "frame_index": int(candidate.get("frame_index") or 0),
        "box": [int(value) for value in candidate.get("box") or []],
        "confidence": round(float(candidate.get("confidence") or 0.0), 6),
        "quality": round(float(candidate.get("quality") or 0.0), 6),
        "time_bucket": str(candidate.get("time_bucket") or ""),
        "pose_view_hint": str(candidate.get("pose_view_hint") or "back_or_unknown"),
        "body_angle_hint": dict(candidate.get("body_angle_hint") or {}),
        "diversity_cluster_id": int(candidate.get("diversity_cluster_id") or 0),
        "selection_reason": str(candidate.get("selection_reason") or ""),
    }


def _assign_time_buckets(candidates: list[dict[str, object]]) -> None:
    if not candidates:
        return
    frames = [int(item.get("frame_index") or 0) for item in candidates]
    first = min(frames)
    last = max(frames)
    span = max(1, last - first)
    for item in candidates:
        ratio = (int(item.get("frame_index") or first) - first) / float(span)
        if ratio < 0.34:
            item["time_bucket"] = "early"
        elif ratio < 0.67:
            item["time_bucket"] = "middle"
        else:
            item["time_bucket"] = "late"


def _candidate_signature(candidate: dict[str, object]) -> np.ndarray | None:
    return color_histogram_bgr(candidate.get("crop"))  # type: ignore[arg-type]


def _candidate_similarity(left: dict[str, object], right: dict[str, object]) -> float:
    left_sig = left.get("_signature")
    if left_sig is None:
        left_sig = _candidate_signature(left)
        left["_signature"] = left_sig
    right_sig = right.get("_signature")
    if right_sig is None:
        right_sig = _candidate_signature(right)
        right["_signature"] = right_sig
    if left_sig is None or right_sig is None:
        return 0.0
    return float(np.dot(np.asarray(left_sig, dtype=np.float32), np.asarray(right_sig, dtype=np.float32)))


def _box_center_distance_ratio(left: dict[str, object], right: dict[str, object]) -> float:
    try:
        lx1, ly1, lx2, ly2 = [float(value) for value in left.get("box") or []]
        rx1, ry1, rx2, ry2 = [float(value) for value in right.get("box") or []]
    except ValueError:
        return 0.0
    lcx, lcy = (lx1 + lx2) / 2.0, (ly1 + ly2) / 2.0
    rcx, rcy = (rx1 + rx2) / 2.0, (ry1 + ry2) / 2.0
    scale = max(1.0, abs(lx2 - lx1), abs(ly2 - ly1), abs(rx2 - rx1), abs(ry2 - ry1))
    return float(np.hypot(lcx - rcx, lcy - rcy) / scale)


def _candidate_diversity_score(candidate: dict[str, object], selected: list[dict[str, object]]) -> float:
    if not selected:
        return 1.0
    max_similarity = max(_candidate_similarity(candidate, item) for item in selected)
    max_frame_gap = max(abs(int(candidate.get("frame_index") or 0) - int(item.get("frame_index") or 0)) for item in selected)
    time_bonus = 1.0 if str(candidate.get("time_bucket")) not in {str(item.get("time_bucket")) for item in selected} else 0.0
    pose_bonus = 1.0 if str(candidate.get("pose_view_hint")) not in {str(item.get("pose_view_hint")) for item in selected} else 0.0
    box_bonus = min(1.0, max(_box_center_distance_ratio(candidate, item) for item in selected))
    frame_bonus = min(1.0, max_frame_gap / 45.0)
    return float(((1.0 - max_similarity) * 0.45) + (time_bonus * 0.20) + (pose_bonus * 0.20) + (box_bonus * 0.10) + (frame_bonus * 0.05))


def select_diverse_crop_candidates(
    candidates: list[dict[str, object]],
    top_n: int,
    selection_strategy: str = "diverse-quality",
    min_frame_gap: int = 15,
    max_similarity: float = 0.92,
    min_quality_ratio: float = 0.70,
) -> list[dict[str, object]]:
    if not candidates:
        return []

    normalized = []
    for candidate in candidates:
        if candidate.get("crop") is None:
            continue
        item = dict(candidate)
        normalized.append(item)
    if not normalized:
        return []

    _assign_time_buckets(normalized)
    sorted_candidates = sorted(normalized, key=lambda item: float(item.get("quality") or 0.0), reverse=True)
    limit = max(1, int(top_n))
    if str(selection_strategy or "diverse-quality").strip().lower() == "quality-only":
        selected = [dict(item) for item in sorted_candidates[:limit]]
        for index, item in enumerate(selected, start=1):
            item["diversity_cluster_id"] = index
            item["selection_reason"] = "quality_rank"
        return selected

    best_quality = max(1e-6, float(sorted_candidates[0].get("quality") or 0.0))
    quality_floor = best_quality * max(0.0, min(1.0, float(min_quality_ratio)))
    eligible = [item for item in sorted_candidates if float(item.get("quality") or 0.0) >= quality_floor]
    if not eligible:
        eligible = sorted_candidates

    selected = [dict(sorted_candidates[0])]
    selected[0]["selection_reason"] = "quality_best"
    selected_ids = {id(sorted_candidates[0])}

    def add_best(strict: bool) -> bool:
        best_item = None
        best_score = -1.0
        for item in eligible:
            if id(item) in selected_ids:
                continue
            max_sig_similarity = max(_candidate_similarity(item, chosen) for chosen in selected)
            min_gap = min(abs(int(item.get("frame_index") or 0) - int(chosen.get("frame_index") or 0)) for chosen in selected)
            if strict and min_gap < int(min_frame_gap) and max_sig_similarity > float(max_similarity):
                continue
            quality_score = float(item.get("quality") or 0.0) / best_quality
            diversity_score = _candidate_diversity_score(item, selected)
            score = (quality_score * 0.62) + (diversity_score * 0.38)
            if score > best_score:
                best_score = score
                best_item = item
        if best_item is None:
            return False
        picked = dict(best_item)
        picked["selection_reason"] = "diverse_quality" if strict else "diverse_quality_relaxed"
        selected.append(picked)
        selected_ids.add(id(best_item))
        return True

    while len(selected) < limit and add_best(strict=True):
        pass
    while len(selected) < limit and add_best(strict=False):
        pass
    if len(selected) < limit:
        for item in sorted_candidates:
            if len(selected) >= limit:
                break
            if id(item) in selected_ids:
                continue
            picked = dict(item)
            picked["selection_reason"] = "quality_fill"
            selected.append(picked)
            selected_ids.add(id(item))

    for index, item in enumerate(selected, start=1):
        item["rank"] = index
        item["diversity_cluster_id"] = index
        item.pop("_signature", None)
    return selected


def reset_analyzer_state(analyzer) -> None:
    analyzer.frame_index = 0
    analyzer.last_inference_ms = 0.0
    analyzer.next_track_id = 1
    analyzer.tracks = {}
    if hasattr(analyzer, "external_tracks"):
        analyzer.external_tracks = {}


class BestShotSelector:
    def __init__(
        self,
        crop_expand_ratio: float = 0.10,
        selection_strategy: str = "diverse-quality",
        diversity_min_frame_gap: int = 15,
        diversity_max_similarity: float = 0.92,
        min_quality_ratio: float = 0.70,
    ):
        self.crop_expand_ratio = float(crop_expand_ratio)
        self.selection_strategy = str(selection_strategy or "diverse-quality")
        self.diversity_min_frame_gap = int(diversity_min_frame_gap)
        self.diversity_max_similarity = float(diversity_max_similarity)
        self.min_quality_ratio = float(min_quality_ratio)

    def select_from_clip(
        self,
        analyzer,
        clip_path: Path,
        clip_id: str,
        max_frames: int,
        sample_every: int,
        top_n: int = 3,
        save_debug: bool = False,
        debug_dir: Path | None = None,
    ) -> dict[str, object]:
        reset_analyzer_state(analyzer)
        cap = cv2.VideoCapture(str(clip_path))
        if not cap.isOpened():
            return {
                "ok": False,
                "clip_id": clip_id,
                "reason": "video_open_failed",
                "frames_read": 0,
                "frames_analyzed": 0,
                "crop_count": 0,
                "top_crops": [],
            }

        frames_read = 0
        frames_analyzed = 0
        candidates: list[dict[str, object]] = []
        warning = None
        try:
            while frames_read < max_frames:
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                frames_read += 1
                if frames_read % max(1, sample_every) != 0:
                    continue
                frames_analyzed += 1
                people = analyzer.analyze_frame(frame)
                if len(people) > 1:
                    warning = "multiple_people_detected_target_selected"
                if not people:
                    continue

                frame_candidates = []
                for person in people:
                    crop = crop_person(frame, person["box"], self.crop_expand_ratio)
                    quality = crop_quality(crop, person, frame.shape)
                    if crop is None:
                        continue
                    frame_candidates.append(make_crop_candidate(frames_read, crop, person, frame.shape, quality))
                if frame_candidates:
                    candidates.append(max(frame_candidates, key=lambda item: float(item.get("quality") or 0.0)))
        finally:
            cap.release()

        top_candidates = select_diverse_crop_candidates(
            candidates,
            top_n=max(1, int(top_n)),
            selection_strategy=self.selection_strategy,
            min_frame_gap=self.diversity_min_frame_gap,
            max_similarity=self.diversity_max_similarity,
            min_quality_ratio=self.min_quality_ratio,
        )
        if save_debug and debug_dir is not None and top_candidates:
            self._save_debug_crops(top_candidates, debug_dir, clip_id)

        if not top_candidates:
            return {
                "ok": False,
                "clip_id": clip_id,
                "reason": "no_person_crop",
                "frames_read": frames_read,
                "frames_analyzed": frames_analyzed,
                "crop_count": 0,
                "top_crops": [],
                "warning": warning,
            }

        return {
            "ok": True,
            "clip_id": clip_id,
            "reason": "best_shot_selected",
            "frames_read": frames_read,
            "frames_analyzed": frames_analyzed,
            "crop_count": len(candidates),
            "selected_frame_index": int(top_candidates[0].get("frame_index") or 0),
            "best_crop_quality": round(float(top_candidates[0].get("quality") or 0.0), 4),
            "top_crops": [crop_candidate_to_json(candidate) for candidate in top_candidates],
            "crop_selection_strategy": self.selection_strategy,
            "warning": warning,
            "_crop_arrays": [candidate["crop"] for candidate in top_candidates],
        }

    def _save_debug_crops(self, candidates: list[dict[str, object]], debug_dir: Path, clip_id: str) -> None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        safe_id = sanitize_filename(clip_id)
        thumbs = []
        for index, candidate in enumerate(candidates, start=1):
            suffix = "best" if index == 1 else f"rank_{index:02d}"
            path = debug_dir / f"{safe_id}_{suffix}.jpg"
            crop = candidate.get("crop")
            if crop is None:
                continue
            cv2.imwrite(str(path), crop)
            candidate["crop_path"] = project_relative(path)
            thumbs.append(resize_with_padding(crop, (160, 320)))

        if thumbs:
            sheet = np.concatenate(thumbs, axis=1)
            cv2.imwrite(str(debug_dir / f"{safe_id}_contact.jpg"), sheet)


class TorchvisionEmbedder:
    def __init__(
        self,
        model_name: str = "mobilenet_v3_large",
        cache_root: Path = MODEL_CACHE_ROOT,
        color_weight: float = 0.20,
    ):
        self.model_name = str(model_name or "mobilenet_v3_large").strip().lower()
        self.cache_root = cache_root
        self.cache_root.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("TORCH_HOME", str(self.cache_root))
        self.color_weight = max(0.0, min(1.0, float(color_weight)))
        self.lock = threading.Lock()
        self.model = None
        self.preprocess = None
        self.device = "cpu"
        self.method = "hsv_histogram"
        self._torch_failed = False
        if self.model_name != "hsv_histogram":
            self._load_torchvision_model()

    @property
    def config_id(self) -> str:
        return f"{self.model_name}:color={self.color_weight:.3f}:method={self.method}"

    def _load_torchvision_model(self) -> None:
        try:
            import certifi

            os.environ.setdefault("SSL_CERT_FILE", certifi.where())
            os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
        except Exception:
            pass

        try:
            import torch
            from torchvision.models import (
                EfficientNet_B0_Weights,
                MobileNet_V3_Large_Weights,
                MobileNet_V3_Small_Weights,
                efficientnet_b0,
                mobilenet_v3_large,
                mobilenet_v3_small,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[visual-reid] torchvision unavailable; using HSV fallback: {exc!r}")
            return

        if torch.cuda.is_available():
            self.device = "cuda:0"
        elif getattr(getattr(torch, "backends", None), "mps", None) is not None and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        try:
            if self.model_name == "mobilenet_v3_small":
                weights = MobileNet_V3_Small_Weights.DEFAULT
                model = mobilenet_v3_small(weights=weights)
                model.classifier = torch.nn.Identity()
            elif self.model_name == "efficientnet_b0":
                weights = EfficientNet_B0_Weights.DEFAULT
                model = efficientnet_b0(weights=weights)
                model.classifier = torch.nn.Identity()
            else:
                self.model_name = "mobilenet_v3_large"
                weights = MobileNet_V3_Large_Weights.DEFAULT
                model = mobilenet_v3_large(weights=weights)
                model.classifier = torch.nn.Identity()

            model.eval().to(self.device)
            self.model = model
            self.preprocess = weights.transforms()
            self.method = f"torchvision_{self.model_name}"
            print(f"[visual-reid] Loaded {self.method} on {self.device}; cache={self.cache_root}")
        except Exception as exc:  # noqa: BLE001
            print(f"[visual-reid] Failed to load {self.model_name}; using HSV fallback: {exc!r}")
            self.model = None
            self.preprocess = None
            self.method = "hsv_histogram"

    def embed_bgr(self, image_bgr: np.ndarray | None) -> tuple[np.ndarray | None, str]:
        if image_bgr is None or image_bgr.size == 0:
            return None, self.method

        if self.model is not None and not self._torch_failed:
            embedding = self._embed_torch(image_bgr)
            if embedding is not None:
                fused = self._fuse_color(embedding, image_bgr)
                return fused, self.method
        return color_histogram_bgr(image_bgr), "hsv_histogram"

    def _embed_torch(self, image_bgr: np.ndarray) -> np.ndarray | None:
        try:
            import torch
            from PIL import Image

            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            tensor = self.preprocess(pil_image).unsqueeze(0).to(self.device)
            with self.lock, torch.inference_mode():
                features = self.model(tensor).detach().float().cpu().numpy().reshape(-1)
            return normalize_vector(features)
        except Exception as exc:  # noqa: BLE001
            self._torch_failed = True
            print(f"[visual-reid] Torch embedding failed once; switching to HSV fallback: {exc!r}")
            return None

    def _fuse_color(self, embedding: np.ndarray, image_bgr: np.ndarray) -> np.ndarray | None:
        visual = normalize_vector(embedding)
        if visual is None or self.color_weight <= 0.0:
            return visual
        color = color_histogram_bgr(image_bgr)
        if color is None:
            return visual
        fused = np.concatenate(
            [
                visual * (1.0 - self.color_weight),
                color * self.color_weight,
            ]
        )
        return normalize_vector(fused)


class PersonReIDEmbedder:
    def __init__(
        self,
        model_name: str = "osnet_x0_25",
        cache_root: Path = TORCHREID_CACHE_ROOT,
    ):
        self.model_name = str(model_name or "osnet_x0_25").strip().lower()
        self.cache_root = cache_root
        self.checkpoint_dir = self.cache_root / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.model = None
        self.device = "cpu"
        self.method = f"torchreid_{self.model_name}"
        self._load_model()

    @property
    def config_id(self) -> str:
        return f"{self.model_name}:method={self.method}:checkpoint=msmt17_combineall"

    def _load_model(self) -> None:
        if self.model_name != "osnet_x0_25":
            raise ValueError(f"Unsupported person-ReID model: {self.model_name}")

        try:
            import certifi

            os.environ.setdefault("SSL_CERT_FILE", certifi.where())
            os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
        except Exception:
            pass

        os.environ.setdefault("TORCH_HOME", str(self.cache_root))
        try:
            import torch
            import torchreid
            from torchreid.reid.utils import load_pretrained_weights
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "torchreid person-ReID backend is unavailable. "
                "Install torchreid, gdown, and tensorboard in the project .venv."
            ) from exc

        if torch.cuda.is_available():
            self.device = "cuda:0"
        elif getattr(getattr(torch, "backends", None), "mps", None) is not None and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        checkpoint_path = self._ensure_checkpoint()
        model = torchreid.models.build_model(
            name=self.model_name,
            num_classes=1000,
            loss="softmax",
            pretrained=False,
        )
        load_pretrained_weights(model, str(checkpoint_path))
        model.eval().to(self.device)
        self.model = model
        print(f"[person-reid] Loaded {self.method} on {self.device}; checkpoint={checkpoint_path}")

    def _ensure_checkpoint(self) -> Path:
        checkpoint_path = self.checkpoint_dir / (
            "osnet_x0_25_msmt17_combineall_256x128_amsgrad_"
            "ep150_stp60_lr0.0015_b64_fb10_softmax_labelsmooth_flip_jitter.pth"
        )
        if checkpoint_path.is_file() and checkpoint_path.stat().st_size > 0:
            return checkpoint_path

        try:
            import gdown
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("gdown is required to download OSNet x0.25 ReID weights.") from exc

        url = f"https://drive.google.com/uc?id={OSNET_X0_25_MSMT17_FILE_ID}"
        downloaded = gdown.download(url, str(checkpoint_path), quiet=False)
        if not downloaded or not checkpoint_path.is_file() or checkpoint_path.stat().st_size <= 0:
            raise RuntimeError(f"Failed to download OSNet x0.25 ReID weights to {checkpoint_path}")
        return checkpoint_path

    def embed_bgr(self, image_bgr: np.ndarray | None) -> tuple[np.ndarray | None, str]:
        if image_bgr is None or image_bgr.size == 0:
            return None, self.method
        if self.model is None:
            raise RuntimeError("PersonReIDEmbedder model is not loaded.")
        embedding = self._embed_torchreid(image_bgr)
        return embedding, self.method

    def _embed_torchreid(self, image_bgr: np.ndarray) -> np.ndarray | None:
        import torch

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(image_rgb, (128, 256), interpolation=cv2.INTER_AREA)
        tensor = torch.from_numpy(resized).float().permute(2, 0, 1).unsqueeze(0) / 255.0
        mean = torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(1, 3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(1, 3, 1, 1)
        tensor = ((tensor - mean) / std).to(self.device)

        with self.lock, torch.inference_mode():
            features = self.model(tensor).detach().float().cpu().numpy().reshape(-1)
        return normalize_vector(features)


def create_visual_embedder(
    model_name: str = "osnet_x0_25",
    cache_root: Path | None = None,
    color_weight: float = 0.20,
):
    normalized = str(model_name or "osnet_x0_25").strip().lower()
    if normalized == "osnet_x0_25":
        return PersonReIDEmbedder(model_name=normalized, cache_root=cache_root or TORCHREID_CACHE_ROOT)
    return TorchvisionEmbedder(
        model_name=normalized,
        cache_root=cache_root or MODEL_CACHE_ROOT,
        color_weight=color_weight,
    )


def _cache_key(clip_path: Path, params: dict[str, object]) -> str:
    stat = clip_path.stat()
    payload = {
        "clip_path": str(clip_path.resolve()),
        "mtime_ns": int(stat.st_mtime_ns),
        "size": int(stat.st_size),
        **params,
    }
    text = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _load_cached_analysis(cache_path: Path) -> dict[str, object] | None:
    if not cache_path.is_file():
        return None
    try:
        with np.load(str(cache_path), allow_pickle=False) as data:
            metadata = json.loads(str(data["metadata"].item()))
            embedding = data["embedding"].astype(np.float32)
            prototype_embeddings = (
                data["prototype_embeddings"].astype(np.float32)
                if "prototype_embeddings" in data
                else np.zeros((0, 0), dtype=np.float32)
            )
        metadata["embedding"] = normalize_vector(embedding)
        if prototype_embeddings.size:
            normalized_prototypes = []
            for row in prototype_embeddings:
                normalized = normalize_vector(row)
                if normalized is not None:
                    normalized_prototypes.append(normalized)
            if normalized_prototypes:
                metadata["prototype_embeddings"] = np.vstack(normalized_prototypes).astype(np.float32)
        metadata["cache_hit"] = True
        return metadata
    except Exception:  # noqa: BLE001
        return None


def _save_cached_analysis(
    cache_path: Path,
    metadata: dict[str, object],
    embedding: np.ndarray,
    prototype_embeddings: np.ndarray | None = None,
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    serializable = {key: value for key, value in metadata.items() if key not in {"embedding", "prototype_embeddings"}}
    prototypes = (
        np.asarray(prototype_embeddings, dtype=np.float32)
        if prototype_embeddings is not None
        else np.zeros((0, 0), dtype=np.float32)
    )
    np.savez_compressed(
        str(cache_path),
        embedding=np.asarray(embedding, dtype=np.float32),
        prototype_embeddings=prototypes,
        metadata=np.asarray(json.dumps(serializable, sort_keys=True)),
    )


def analyze_clip_visual(
    analyzer,
    embedder,
    clip_path: Path,
    clip_id: str,
    max_frames: int,
    sample_every: int,
    top_n: int,
    save_debug_crops: bool,
    debug_dir: Path,
    embedding_cache_dir: Path,
    crop_expand_ratio: float = 0.10,
    selection_strategy: str = "diverse-quality",
    diversity_min_frame_gap: int = 15,
    diversity_max_similarity: float = 0.92,
    crop_min_quality_ratio: float = 0.70,
) -> dict[str, object]:
    clip_path = clip_path.resolve()
    params = {
        "embedder": embedder.config_id,
        "max_frames": int(max_frames),
        "sample_every": int(sample_every),
        "top_n": int(top_n),
        "crop_expand_ratio": round(float(crop_expand_ratio), 4),
        "selection_strategy": str(selection_strategy or "diverse-quality"),
        "diversity_min_frame_gap": int(diversity_min_frame_gap),
        "diversity_max_similarity": round(float(diversity_max_similarity), 4),
        "crop_min_quality_ratio": round(float(crop_min_quality_ratio), 4),
    }
    cache_path = embedding_cache_dir / f"{_cache_key(clip_path, params)}.npz"
    cached = _load_cached_analysis(cache_path)
    if cached is not None:
        return cached

    selector = BestShotSelector(
        crop_expand_ratio=crop_expand_ratio,
        selection_strategy=selection_strategy,
        diversity_min_frame_gap=diversity_min_frame_gap,
        diversity_max_similarity=diversity_max_similarity,
        min_quality_ratio=crop_min_quality_ratio,
    )
    selected = selector.select_from_clip(
        analyzer=analyzer,
        clip_path=clip_path,
        clip_id=clip_id,
        max_frames=max_frames,
        sample_every=sample_every,
        top_n=top_n,
        save_debug=save_debug_crops,
        debug_dir=debug_dir,
    )
    crop_arrays = selected.pop("_crop_arrays", [])
    if not selected.get("ok"):
        selected["embedding"] = None
        selected["embedding_method"] = embedder.method
        selected["cache_hit"] = False
        return selected

    embeddings = []
    methods = []
    for crop in crop_arrays:
        embedding, method = embedder.embed_bgr(crop)
        if embedding is not None:
            embeddings.append(embedding)
            methods.append(method)

    if not embeddings:
        selected["ok"] = False
        selected["reason"] = "embedding_failed"
        selected["embedding"] = None
        selected["embedding_method"] = embedder.method
        selected["cache_hit"] = False
        return selected

    stacked = np.vstack(embeddings)
    aggregate = normalize_vector(stacked.mean(axis=0))
    if aggregate is None:
        selected["ok"] = False
        selected["reason"] = "embedding_normalize_failed"
        selected["embedding"] = None
        selected["embedding_method"] = methods[-1] if methods else embedder.method
        selected["cache_hit"] = False
        return selected

    selected["embedding"] = aggregate
    selected["prototype_embeddings"] = stacked.astype(np.float32)
    selected["prototype_count"] = int(stacked.shape[0])
    selected["embedding_method"] = methods[-1] if methods else embedder.method
    selected["embedding_aggregation"] = f"prototype_mean_top_{len(embeddings)}"
    selected["embedding_dim"] = int(aggregate.shape[0])
    selected["cache_hit"] = False
    _save_cached_analysis(cache_path, selected, aggregate, stacked)
    return selected


def serializable_visual_analysis(analysis: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in analysis.items() if key not in {"embedding", "prototype_embeddings"}}
