import time
from collections import Counter, deque
import os
from pathlib import Path

import cv2
import numpy as np
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = PROJECT_ROOT / "models"
os.environ.setdefault("YOLO_CONFIG_DIR", str(PROJECT_ROOT / "logs" / "ultralytics"))

from ultralytics import YOLO


class WalnutAnalyzer:
    TRACKER_BACKENDS = {"custom", "botsort", "bytetrack"}
    TORSO_RATIO_CONFIDENCE = 0.4
    KEYPOINT_INDEX = {
        "nose": 0,
        "left_shoulder": 5,
        "right_shoulder": 6,
        "left_elbow": 7,
        "right_elbow": 8,
        "left_wrist": 9,
        "right_wrist": 10,
        "left_hip": 11,
        "right_hip": 12,
        "left_knee": 13,
        "right_knee": 14,
        "left_ankle": 15,
        "right_ankle": 16,
    }
    BAG_CLASS_NAMES = {"backpack", "handbag", "suitcase"}
    REGION_NAMES = ("top", "bottom")

    def __init__(
        self,
        pose_model_name="yolov8n-pose.pt",
        detect_model_name="yolov8n.pt",
        person_confidence=0.45,
        pose_confidence=0.35,
        accessory_confidence=0.18,
        model_imgsz=640,
        vote_frame_window=75,
        track_max_missing=15,
        tracker_backend="custom",
        tracker_config_path=None,
    ):
        self.pose_model_name = pose_model_name
        self.detect_model_name = detect_model_name
        self.person_confidence = person_confidence
        self.pose_confidence = pose_confidence
        self.accessory_confidence = accessory_confidence
        self.model_imgsz = model_imgsz
        self.vote_frame_window = max(1, int(vote_frame_window))
        self.track_max_missing = max(1, int(track_max_missing))
        self.tracker_backend = self._normalize_tracker_backend(tracker_backend)
        self.tracker_config_path = tracker_config_path

        self.device = self._select_device()
        self.use_half = self.device.startswith("cuda")

        self.pose_model = self._load_model(self.pose_model_name)
        self.detect_model = self._load_model(self.detect_model_name)
        self.detect_class_names = self.detect_model.names
        self.detect_target_class_ids = [
            class_id
            for class_id, class_name in self.detect_class_names.items()
            if class_name == "person" or class_name in self.BAG_CLASS_NAMES
        ]

        self.frame_index = 0
        self.last_inference_ms = 0.0
        self.next_track_id = 1
        self.tracks = {}
        self.external_tracks = {}

        cv2.setUseOptimized(True)
        if self.device.startswith("cuda"):
            torch.backends.cudnn.benchmark = True

    def analyze_frame(self, frame):
        self.frame_index += 1
        start_time = time.perf_counter()

        pose_results = self._run_pose_model(frame)
        detect_results = self.detect_model.predict(
            source=frame,
            conf=min(self.person_confidence, self.accessory_confidence),
            verbose=False,
            device=self.device,
            half=self.use_half,
            imgsz=self.model_imgsz,
            max_det=30,
            classes=self.detect_target_class_ids,
        )

        self.last_inference_ms = (time.perf_counter() - start_time) * 1000.0
        pose_result = pose_results[0] if pose_results else None
        detect_result = detect_results[0] if detect_results else None
        return self._build_scene(frame, pose_result, detect_result)

    def _normalize_tracker_backend(self, tracker_backend):
        normalized = str(tracker_backend or "custom").strip().lower()
        if normalized not in self.TRACKER_BACKENDS:
            allowed = ", ".join(sorted(self.TRACKER_BACKENDS))
            raise ValueError(f"Unsupported tracker_backend '{tracker_backend}'. Use one of: {allowed}.")
        return normalized

    def _tracker_config(self):
        if self.tracker_config_path:
            return str(self.tracker_config_path)
        if self.tracker_backend == "botsort":
            project_config = PROJECT_ROOT / "configs" / "trackers" / "botsort.yaml"
            return str(project_config) if project_config.is_file() else "botsort.yaml"
        if self.tracker_backend == "bytetrack":
            project_config = PROJECT_ROOT / "configs" / "trackers" / "bytetrack.yaml"
            return str(project_config) if project_config.is_file() else "bytetrack.yaml"
        return None

    def _run_pose_model(self, frame):
        common_kwargs = {
            "source": frame,
            "conf": self.person_confidence,
            "verbose": False,
            "device": self.device,
            "half": self.use_half,
            "imgsz": self.model_imgsz,
            "max_det": 20,
            "classes": [0],
        }
        if self.tracker_backend == "custom":
            return self.pose_model.predict(**common_kwargs)
        return self.pose_model.track(
            **common_kwargs,
            persist=True,
            tracker=self._tracker_config(),
        )

    def _select_device(self):
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"Using Nvidia GPU: {device_name}")
            return "cuda:0"

        mps_backend = getattr(getattr(torch, "backends", None), "mps", None)
        if mps_backend is not None and mps_backend.is_available():
            print("Using Apple Silicon MPS.")
            return "mps"

        print("CUDA and MPS are unavailable. Running on CPU.")
        return "cpu"

    def _resolve_model_path(self, model_name):
        model_path = Path(model_name).expanduser()
        if model_path.is_absolute():
            resolved = model_path.resolve()
            if not str(resolved).startswith(str(PROJECT_ROOT)):
                raise ValueError(f"Model path must stay inside project root: {resolved}")
            return str(resolved)

        candidates = [MODEL_ROOT / model_path, PROJECT_ROOT / model_path]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate.resolve())
        return str((MODEL_ROOT / model_path).resolve())

    def _load_model(self, model_name):
        model_path = self._resolve_model_path(model_name)
        print(f"Loading model: {model_path}")
        model = YOLO(model_path)
        model.to(self.device)
        return model

    def _build_scene(self, frame, pose_result, detect_result):
        people = self._extract_people_from_pose(frame, pose_result)
        bag_candidates = self._extract_bags(frame, detect_result)

        for bag in bag_candidates:
            owner = self._find_bag_owner(people, bag["box"])
            if owner is not None:
                owner["bags"].append(bag)

        if self.tracker_backend == "custom":
            return self._update_tracks(people)
        return self._update_external_tracks(people)

    def _extract_people_from_pose(self, frame, pose_result):
        if pose_result is None or pose_result.boxes is None or pose_result.keypoints is None:
            return []

        boxes = pose_result.boxes.xyxy.detach().cpu().numpy().astype(int)
        confidences = pose_result.boxes.conf.detach().cpu().numpy()
        keypoints_xy = pose_result.keypoints.xy.detach().cpu().numpy()
        track_ids = None
        if getattr(pose_result.boxes, "id", None) is not None:
            track_ids = pose_result.boxes.id.detach().cpu().numpy()
        keypoints_conf = (
            pose_result.keypoints.conf.detach().cpu().numpy()
            if pose_result.keypoints.conf is not None
            else None
        )

        people = []
        for index, (box, confidence, kpts_xy) in enumerate(zip(boxes, confidences, keypoints_xy)):
            if confidence < self.person_confidence:
                continue

            clipped_box = self._clip_box(frame, box)
            if clipped_box is None:
                continue

            kpts_conf = keypoints_conf[index] if keypoints_conf is not None else None
            regions = self._compute_pose_region_colors(frame, clipped_box, kpts_xy, kpts_conf)
            limb_coverage = self._compute_limb_coverage(frame, kpts_xy, kpts_conf)
            torso_ratio = self._compute_torso_ratio(kpts_xy, kpts_conf)
            external_track_id = None
            if track_ids is not None and index < len(track_ids):
                try:
                    external_track_id = int(track_ids[index])
                except (TypeError, ValueError):
                    external_track_id = None
            people.append(
                {
                    "box": clipped_box,
                    "confidence": float(confidence),
                    "external_track_id": external_track_id,
                    "regions": regions,
                    "brightness_ratio": self._compute_brightness_ratio_from_regions(regions),
                    "is_long_sleeve": limb_coverage["is_long_sleeve"],
                    "is_long_pants": limb_coverage["is_long_pants"],
                    "limb_samples": limb_coverage["samples"],
                    "torso_lines": self._compute_torso_lines(kpts_xy, kpts_conf),
                    "torso_ratio": torso_ratio,
                    "bags": [],
                }
            )

        return people

    def _extract_bags(self, frame, detect_result):
        if detect_result is None or detect_result.boxes is None or len(detect_result.boxes) == 0:
            return []

        boxes_xyxy = detect_result.boxes.xyxy.detach().cpu().numpy().astype(int)
        classes = detect_result.boxes.cls.detach().cpu().numpy().astype(int)
        confidences = detect_result.boxes.conf.detach().cpu().numpy()

        bag_candidates = []
        for box, cls_id, confidence in zip(boxes_xyxy, classes, confidences):
            class_name = self.detect_class_names[int(cls_id)]
            if class_name not in self.BAG_CLASS_NAMES or confidence < self.accessory_confidence:
                continue

            clipped_box = self._clip_box(frame, box)
            if clipped_box is None:
                continue

            bag_candidates.append(
                {
                    "name": "bag",
                    "source_name": class_name,
                    "confidence": float(confidence),
                    "box": clipped_box,
                }
            )

        return bag_candidates

    def _update_tracks(self, detected_people):
        matched_track_ids = set()
        tracked_people = []

        for person in detected_people:
            track_id = self._match_existing_track(person, matched_track_ids)
            if track_id is None:
                track_id = self._create_track(person)

            matched_track_ids.add(track_id)
            track = self.tracks[track_id]
            self._update_track_state(track, person)
            tracked_people.append(self._build_person_view(track, person))

        self._cleanup_stale_tracks(matched_track_ids)
        return tracked_people

    def _update_external_tracks(self, detected_people):
        matched_track_ids = set()
        tracked_people = []

        for person in detected_people:
            external_track_id = person.get("external_track_id")
            if external_track_id is None:
                continue
            track_id = int(external_track_id)
            if track_id <= 0:
                continue

            track = self.external_tracks.setdefault(
                track_id,
                {
                    "id": track_id,
                    "first_seen_frame": self.frame_index,
                    "last_seen_frame": self.frame_index,
                    "observed_frames": 0,
                },
            )
            track["last_seen_frame"] = self.frame_index
            track["observed_frames"] = int(track.get("observed_frames", 0)) + 1
            matched_track_ids.add(track_id)
            tracked_people.append(self._build_external_person_view(track, person))

        self._cleanup_external_tracks(matched_track_ids)
        return tracked_people

    def _create_track(self, person):
        track_id = self.next_track_id
        self.next_track_id += 1
        self.tracks[track_id] = {
            "id": track_id,
            "box": person["box"],
            "last_seen_frame": self.frame_index,
            "observed_frames": 0,
            "vote_samples": deque(maxlen=self.vote_frame_window),
            "resolved": False,
            "skip_reason": None,
            "torso_ratio": person.get("torso_ratio"),
            "final_profile": None,
            "pending_log": None,
        }
        return track_id

    def _match_existing_track(self, person, matched_track_ids):
        best_track_id = None
        best_score = -1.0
        person_center = self._box_center(person["box"])

        for track_id, track in self.tracks.items():
            if track_id in matched_track_ids:
                continue
            if self.frame_index - track["last_seen_frame"] > self.track_max_missing:
                continue

            iou = self._intersection_over_union(track["box"], person["box"])
            center_distance = self._center_distance(self._box_center(track["box"]), person_center)
            box_width = max(1.0, track["box"][2] - track["box"][0])
            box_height = max(1.0, track["box"][3] - track["box"][1])
            distance_threshold = max(box_width, box_height) * 0.75

            if iou <= 0 and center_distance > distance_threshold:
                continue

            score = iou * 1000.0 - center_distance
            if score > best_score:
                best_score = score
                best_track_id = track_id

        return best_track_id

    def _update_track_state(self, track, person):
        track["box"] = person["box"]
        track["last_seen_frame"] = self.frame_index

        if track["resolved"]:
            return

        track["observed_frames"] += 1
        track["vote_samples"].append(self._build_vote_sample(person))

        if track["observed_frames"] < self.vote_frame_window:
            return

        candidate_profile = self._finalize_track_profile(track)
        if self._profile_has_unknown_values(candidate_profile):
            track["final_profile"] = None
            track["skip_reason"] = "waiting_for_complete_profile"
            return

        track["final_profile"] = candidate_profile
        self._finalize_local_track(track)

    def _finalize_track_profile(self, track):
        samples = list(track["vote_samples"])
        profile = {}
        for region_name in self.REGION_NAMES:
            values = [sample.get(region_name) for sample in samples]
            profile[region_name] = self._pick_voted_value(values, "unknown")
        profile["bag"] = self._pick_voted_value([sample.get("bag") for sample in samples], "no")
        profile["is_long_sleeve"] = self._pick_voted_value(
            [sample.get("is_long_sleeve") for sample in samples],
            "unknown",
        )
        profile["is_long_pants"] = self._pick_voted_value(
            [sample.get("is_long_pants") for sample in samples],
            "unknown",
        )

        torso_ratio_values = [
            float(sample["torso_ratio"])
            for sample in samples
            if sample.get("torso_ratio") is not None
        ]
        if torso_ratio_values:
            profile["torso_ratio"] = round(sum(torso_ratio_values) / len(torso_ratio_values), 3)
        else:
            profile["torso_ratio"] = None

        brightness_ratio_values = [
            float(sample["brightness_ratio"])
            for sample in samples
            if sample.get("brightness_ratio") is not None
        ]
        if brightness_ratio_values:
            profile["brightness_ratio"] = round(
                sum(brightness_ratio_values) / len(brightness_ratio_values),
                4,
            )
        else:
            profile["brightness_ratio"] = None
        return profile

    def _build_vote_sample(self, person):
        sample = {}
        for region_name in self.REGION_NAMES:
            region = person["regions"].get(region_name)
            sample[region_name] = region["color_name"] if region is not None else "unknown"
        sample["bag"] = "yes" if person["bags"] else "no"
        sample["is_long_sleeve"] = person["is_long_sleeve"]
        sample["is_long_pants"] = person["is_long_pants"]
        sample["torso_ratio"] = person.get("torso_ratio")
        sample["brightness_ratio"] = person.get("brightness_ratio")
        return sample

    def _pick_voted_value(self, values, default_value):
        valid_values = [
            value
            for value in values
            if value is not None
            and not (isinstance(value, str) and value.strip().lower() in {"", "unknown", "nan", "none"})
        ]
        if not valid_values:
            return default_value
        counter = Counter(valid_values)
        return counter.most_common(1)[0][0]

    def _finalize_local_track(self, track):
        if track["final_profile"] is None:
            return
        if self._profile_has_unknown_values(track["final_profile"]):
            track["final_profile"] = None
            track["skip_reason"] = "waiting_for_complete_profile"
            return

        track["resolved"] = True
        track["skip_reason"] = None
        track["pending_log"] = {
            "visitor_id": track["id"],
            "track_id": track["id"],
            "profile": track["final_profile"].copy(),
        }

    def _profile_has_unknown_values(self, profile):
        required_keys = (
            "top",
            "bottom",
            "bag",
            "is_long_sleeve",
            "is_long_pants",
            "torso_ratio",
            "brightness_ratio",
        )
        for key in required_keys:
            if self._is_missing_identity_value(profile.get(key)):
                return True
        return False

    def _is_missing_identity_value(self, value):
        if value is None:
            return True
        if isinstance(value, float) and np.isnan(value):
            return True
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"", "unknown", "nan", "none"}:
                return True
        return False

    def _build_person_view(self, track, person):
        pending_log = track["pending_log"]
        track["pending_log"] = None
        return {
            "id": track["id"],
            "track_id": track["id"],
            "box": person["box"],
            "confidence": person["confidence"],
            "regions": person["regions"],
            "is_long_sleeve": person["is_long_sleeve"],
            "is_long_pants": person["is_long_pants"],
            "limb_samples": person["limb_samples"],
            "torso_lines": person["torso_lines"],
            "torso_ratio": track["torso_ratio"],
            "brightness_ratio": person.get("brightness_ratio"),
            "bags": person["bags"],
            "observed_frames": track["observed_frames"],
            "final_profile": track["final_profile"],
            "visitor_metadata": track["final_profile"],
            "visitor_id": track["id"],
            "resolved": track["resolved"],
            "skip_reason": track["skip_reason"],
            "log_record": pending_log,
            "inference_ms": self.last_inference_ms,
        }

    def _build_external_person_view(self, track, person):
        return {
            "id": track["id"],
            "track_id": track["id"],
            "tracker_backend": self.tracker_backend,
            "box": person["box"],
            "confidence": person["confidence"],
            "regions": person["regions"],
            "is_long_sleeve": person["is_long_sleeve"],
            "is_long_pants": person["is_long_pants"],
            "limb_samples": person["limb_samples"],
            "torso_lines": person["torso_lines"],
            "torso_ratio": person.get("torso_ratio"),
            "brightness_ratio": person.get("brightness_ratio"),
            "bags": person["bags"],
            "observed_frames": track["observed_frames"],
            "final_profile": None,
            "visitor_metadata": None,
            "visitor_id": track["id"],
            "resolved": False,
            "skip_reason": None,
            "log_record": None,
            "inference_ms": self.last_inference_ms,
        }

    def _cleanup_stale_tracks(self, matched_track_ids):
        stale_track_ids = [
            track_id
            for track_id, track in self.tracks.items()
            if track_id not in matched_track_ids
            and self.frame_index - track["last_seen_frame"] > self.track_max_missing
        ]

        for track_id in stale_track_ids:
            del self.tracks[track_id]

    def _cleanup_external_tracks(self, matched_track_ids):
        stale_track_ids = [
            track_id
            for track_id, track in self.external_tracks.items()
            if track_id not in matched_track_ids
            and self.frame_index - track["last_seen_frame"] > self.track_max_missing
        ]

        for track_id in stale_track_ids:
            del self.external_tracks[track_id]

    def _clip_box(self, frame, box):
        height, width = frame.shape[:2]
        x1, y1, x2, y2 = map(int, box)
        x1 = max(0, min(width - 1, x1))
        y1 = max(0, min(height - 1, y1))
        x2 = max(0, min(width, x2))
        y2 = max(0, min(height, y2))
        if x2 <= x1 or y2 <= y1:
            return None
        return x1, y1, x2, y2

    def _kp_valid(self, xy, conf, idx):
        if idx >= len(xy):
            return False
        x, y = xy[idx]
        if x <= 0 or y <= 0:
            return False
        if conf is not None and idx < len(conf) and conf[idx] < self.pose_confidence:
            return False
        return True

    def _mean_point(self, xy, conf, indices):
        points = [xy[idx] for idx in indices if self._kp_valid(xy, conf, idx)]
        if not points:
            return None
        points = np.asarray(points, dtype=np.float32)
        return points.mean(axis=0)

    def _kp_valid_for_torso_ratio(self, xy, conf, idx):
        if idx >= len(xy):
            return False
        x, y = xy[idx]
        if x <= 0 or y <= 0:
            return False
        if conf is None or idx >= len(conf):
            return False
        return conf[idx] > self.TORSO_RATIO_CONFIDENCE

    def _euclidean_distance(self, point_a, point_b):
        return float(np.linalg.norm(point_a - point_b))

    def _compute_torso_ratio(self, kpts_xy, kpts_conf):
        left_shoulder_idx = self.KEYPOINT_INDEX["left_shoulder"]
        right_shoulder_idx = self.KEYPOINT_INDEX["right_shoulder"]
        left_hip_idx = self.KEYPOINT_INDEX["left_hip"]
        right_hip_idx = self.KEYPOINT_INDEX["right_hip"]

        required_indices = [
            left_shoulder_idx,
            right_shoulder_idx,
            left_hip_idx,
            right_hip_idx,
        ]
        if not all(self._kp_valid_for_torso_ratio(kpts_xy, kpts_conf, idx) for idx in required_indices):
            return None

        shoulder_width = self._euclidean_distance(kpts_xy[left_shoulder_idx], kpts_xy[right_shoulder_idx])
        hip_width = self._euclidean_distance(kpts_xy[left_hip_idx], kpts_xy[right_hip_idx])
        if shoulder_width <= 0.0 or hip_width <= 0.0:
            return None

        return round(shoulder_width / hip_width, 3)

    def _extract_roi_mean_bgr(self, frame, center_x, center_y, radius_x=30, radius_y=30):
        height, width = frame.shape[:2]
        x1 = max(0, int(center_x - radius_x))
        y1 = max(0, int(center_y - radius_y))
        x2 = min(width, int(center_x + radius_x))
        y2 = min(height, int(center_y + radius_y))

        if x2 <= x1 or y2 <= y1:
            return None

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return None

        mean_bgr = roi.mean(axis=(0, 1))
        return tuple(int(round(channel)) for channel in mean_bgr)

    def _extract_small_roi_mean_bgr(self, frame, x, y, radius=3):
        height, width = frame.shape[:2]
        px = int(round(x))
        py = int(round(y))
        if px < 0 or py < 0 or px >= width or py >= height:
            return None

        x1 = max(0, px - radius)
        y1 = max(0, py - radius)
        x2 = min(width, px + radius + 1)
        y2 = min(height, py + radius + 1)
        if x2 <= x1 or y2 <= y1:
            return None

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return None

        mean_bgr = roi.mean(axis=(0, 1))
        return tuple(int(round(channel)) for channel in mean_bgr)

    def _extract_small_roi(self, frame, x, y, radius=3):
        height, width = frame.shape[:2]
        px = int(round(x))
        py = int(round(y))
        if px < 0 or py < 0 or px >= width or py >= height:
            return None

        x1 = max(0, px - radius)
        y1 = max(0, py - radius)
        x2 = min(width, px + radius + 1)
        y2 = min(height, py + radius + 1)
        if x2 <= x1 or y2 <= y1:
            return None

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return None
        return roi

    def _is_skin_bgr(self, bgr):
        pixel = np.uint8([[list(bgr)]])
        h, s, v = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)[0][0]
        _, cr, cb = cv2.cvtColor(pixel, cv2.COLOR_BGR2YCrCb)[0][0]
        hsv_skin = 0 <= h <= 30 and 20 <= s <= 180 and 35 <= v <= 255
        ycrcb_skin = 133 <= cr <= 173 and 77 <= cb <= 127
        return hsv_skin or ycrcb_skin

    def _measure_skin_ratio(self, roi):
        if roi is None or roi.size == 0:
            return None

        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        ycrcb_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2YCrCb)

        hsv_mask = (
            (hsv_roi[:, :, 0] >= 0)
            & (hsv_roi[:, :, 0] <= 30)
            & (hsv_roi[:, :, 1] >= 20)
            & (hsv_roi[:, :, 1] <= 180)
            & (hsv_roi[:, :, 2] >= 35)
            & (hsv_roi[:, :, 2] <= 255)
        )
        ycrcb_mask = (
            (ycrcb_roi[:, :, 1] >= 133)
            & (ycrcb_roi[:, :, 1] <= 173)
            & (ycrcb_roi[:, :, 2] >= 77)
            & (ycrcb_roi[:, :, 2] <= 127)
        )
        skin_mask = hsv_mask | ycrcb_mask
        return float(np.count_nonzero(skin_mask)) / float(skin_mask.size)

    def _classify_limb_cover_state(self, frame, start_point, end_point):
        midpoint = (start_point + end_point) / 2.0
        roi = self._extract_small_roi(frame, midpoint[0], midpoint[1], radius=3)
        sample_bgr = self._extract_small_roi_mean_bgr(frame, midpoint[0], midpoint[1], radius=3)
        if roi is None or sample_bgr is None:
            return None, midpoint, None

        skin_ratio = self._measure_skin_ratio(roi)
        if skin_ratio is None:
            return None, midpoint, None

        return (not (skin_ratio >= 0.30)), midpoint, sample_bgr

    def _vote_limb_cover_state(self, values, default_value="unknown"):
        valid_values = [value for value in values if value is not None]
        if not valid_values:
            return default_value
        true_count = sum(1 for value in valid_values if value)
        false_count = len(valid_values) - true_count
        if true_count == false_count:
            return default_value
        return "long" if true_count > false_count else "short"

    def _compute_limb_coverage(self, frame, kpts_xy, kpts_conf):
        long_sleeve_votes = []
        long_pants_votes = []
        samples = []

        arm_pairs = [
            ("left_arm", "left_elbow", "left_wrist"),
            ("right_arm", "right_elbow", "right_wrist"),
        ]
        for sample_name, elbow_name, wrist_name in arm_pairs:
            elbow_idx = self.KEYPOINT_INDEX[elbow_name]
            wrist_idx = self.KEYPOINT_INDEX[wrist_name]
            if self._kp_valid(kpts_xy, kpts_conf, elbow_idx) and self._kp_valid(kpts_xy, kpts_conf, wrist_idx):
                is_covered, midpoint, sample_bgr = self._classify_limb_cover_state(
                    frame, kpts_xy[elbow_idx], kpts_xy[wrist_idx]
                )
                long_sleeve_votes.append(is_covered)
                samples.append(
                    {
                        "name": sample_name,
                        "start": (int(kpts_xy[elbow_idx][0]), int(kpts_xy[elbow_idx][1])),
                        "end": (int(kpts_xy[wrist_idx][0]), int(kpts_xy[wrist_idx][1])),
                        "mid": (int(midpoint[0]), int(midpoint[1])),
                        "bgr": sample_bgr,
                        "is_skin": None if sample_bgr is None else self._is_skin_bgr(sample_bgr),
                    }
                )

        leg_pairs = [
            ("left_leg", "left_knee", "left_ankle"),
            ("right_leg", "right_knee", "right_ankle"),
        ]
        for sample_name, knee_name, ankle_name in leg_pairs:
            knee_idx = self.KEYPOINT_INDEX[knee_name]
            ankle_idx = self.KEYPOINT_INDEX[ankle_name]
            if self._kp_valid(kpts_xy, kpts_conf, knee_idx) and self._kp_valid(kpts_xy, kpts_conf, ankle_idx):
                is_covered, midpoint, sample_bgr = self._classify_limb_cover_state(
                    frame, kpts_xy[knee_idx], kpts_xy[ankle_idx]
                )
                long_pants_votes.append(is_covered)
                samples.append(
                    {
                        "name": sample_name,
                        "start": (int(kpts_xy[knee_idx][0]), int(kpts_xy[knee_idx][1])),
                        "end": (int(kpts_xy[ankle_idx][0]), int(kpts_xy[ankle_idx][1])),
                        "mid": (int(midpoint[0]), int(midpoint[1])),
                        "bgr": sample_bgr,
                        "is_skin": None if sample_bgr is None else self._is_skin_bgr(sample_bgr),
                    }
                )

        return {
            "is_long_sleeve": self._vote_limb_cover_state(long_sleeve_votes, default_value="unknown"),
            "is_long_pants": self._vote_limb_cover_state(long_pants_votes, default_value="unknown"),
            "samples": samples,
        }

    def _compute_torso_lines(self, kpts_xy, kpts_conf):
        lines = {}

        left_shoulder_idx = self.KEYPOINT_INDEX["left_shoulder"]
        right_shoulder_idx = self.KEYPOINT_INDEX["right_shoulder"]
        left_hip_idx = self.KEYPOINT_INDEX["left_hip"]
        right_hip_idx = self.KEYPOINT_INDEX["right_hip"]

        if self._kp_valid_for_torso_ratio(kpts_xy, kpts_conf, left_shoulder_idx) and self._kp_valid_for_torso_ratio(kpts_xy, kpts_conf, right_shoulder_idx):
            lines["shoulders"] = (
                (int(kpts_xy[left_shoulder_idx][0]), int(kpts_xy[left_shoulder_idx][1])),
                (int(kpts_xy[right_shoulder_idx][0]), int(kpts_xy[right_shoulder_idx][1])),
            )

        if self._kp_valid_for_torso_ratio(kpts_xy, kpts_conf, left_hip_idx) and self._kp_valid_for_torso_ratio(kpts_xy, kpts_conf, right_hip_idx):
            lines["hips"] = (
                (int(kpts_xy[left_hip_idx][0]), int(kpts_xy[left_hip_idx][1])),
                (int(kpts_xy[right_hip_idx][0]), int(kpts_xy[right_hip_idx][1])),
            )

        return lines

    def _extract_upper_region_from_face(self, frame, kpts_xy, kpts_conf):
        nose_idx = self.KEYPOINT_INDEX["nose"]
        left_eye_idx = 1
        right_eye_idx = 2

        if not (
            self._kp_valid(kpts_xy, kpts_conf, nose_idx)
            and self._kp_valid(kpts_xy, kpts_conf, left_eye_idx)
            and self._kp_valid(kpts_xy, kpts_conf, right_eye_idx)
        ):
            return None

        nose = kpts_xy[nose_idx]
        left_eye = kpts_xy[left_eye_idx]
        right_eye = kpts_xy[right_eye_idx]
        eye_mid = (left_eye + right_eye) / 2.0
        eye_distance = float(np.linalg.norm(left_eye - right_eye))
        if eye_distance < 4.0:
            return None

        center_x = eye_mid[0]
        center_y = eye_mid[1] - (eye_distance * 0.50)
        radius_x = max(10, int(eye_distance * 0.55))
        radius_y = max(10, int(eye_distance * 0.35))

        bottom_y = center_y + radius_y
        max_allowed_bottom = nose[1] - (eye_distance * 0.20)
        if bottom_y >= max_allowed_bottom:
            center_y = max_allowed_bottom - radius_y

        if center_y - radius_y < 0:
            return None

        mean_bgr = self._extract_roi_mean_bgr(frame, center_x, center_y, radius_x, radius_y)
        if mean_bgr is None:
            return None

        return {
            "bgr": mean_bgr,
            "pos": (int(center_x), int(center_y)),
            "color_name": self._classify_bgr_color_name(mean_bgr),
        }

    def _compute_pose_region_colors(self, frame, person_box, kpts_xy, kpts_conf):
        x1, y1, x2, y2 = person_box
        person_height = max(1, y2 - y1)
        person_width = max(1, x2 - x1)
        region_radius_x = max(18, int(person_width * 0.16))
        region_radius_y = max(18, int(person_height * 0.10))
        top_sample_radius = max(3, min(8, int(min(person_width, person_height) * 0.025)))

        shoulders = self._mean_point(
            kpts_xy,
            kpts_conf,
            [self.KEYPOINT_INDEX["left_shoulder"], self.KEYPOINT_INDEX["right_shoulder"]],
        )
        hips = self._mean_point(
            kpts_xy,
            kpts_conf,
            [self.KEYPOINT_INDEX["left_hip"], self.KEYPOINT_INDEX["right_hip"]],
        )
        left_hip = self._mean_point(kpts_xy, kpts_conf, [self.KEYPOINT_INDEX["left_hip"]])
        left_knee = self._mean_point(kpts_xy, kpts_conf, [self.KEYPOINT_INDEX["left_knee"]])

        regions = {}

        top_region = self._extract_top_region_by_outer_vote(
            frame,
            kpts_xy,
            kpts_conf,
            top_sample_radius,
        )
        if top_region is not None:
            regions["top"] = top_region

        if left_hip is not None and left_knee is not None:
            bottom_point = (left_hip + left_knee) / 2.0
            bottom_bgr = self._extract_roi_mean_bgr(
                frame,
                bottom_point[0],
                bottom_point[1],
                region_radius_x,
                region_radius_y,
            )
            if bottom_bgr is not None:
                regions["bottom"] = {
                    "bgr": bottom_bgr,
                    "pos": (int(bottom_point[0]), int(bottom_point[1])),
                    "color_name": self._classify_bgr_color_name(bottom_bgr),
                }

        return regions

    def _extract_top_region_by_outer_vote(self, frame, kpts_xy, kpts_conf, sample_radius):
        left_shoulder_idx = self.KEYPOINT_INDEX["left_shoulder"]
        right_shoulder_idx = self.KEYPOINT_INDEX["right_shoulder"]
        left_hip_idx = self.KEYPOINT_INDEX["left_hip"]
        right_hip_idx = self.KEYPOINT_INDEX["right_hip"]

        required_indices = [
            left_shoulder_idx,
            right_shoulder_idx,
            left_hip_idx,
            right_hip_idx,
        ]
        if not all(self._kp_valid(kpts_xy, kpts_conf, idx) for idx in required_indices):
            return None

        left_shoulder = kpts_xy[left_shoulder_idx]
        right_shoulder = kpts_xy[right_shoulder_idx]
        left_hip = kpts_xy[left_hip_idx]
        right_hip = kpts_xy[right_hip_idx]

        shoulder_y_mean = (left_shoulder[1] + right_shoulder[1]) / 2.0
        hip_y_mean = (left_hip[1] + right_hip[1]) / 2.0
        navel_y = shoulder_y_mean + ((hip_y_mean - shoulder_y_mean) * 0.65)
        center_point = ((left_shoulder + right_shoulder) / 2.0 + (left_hip + right_hip) / 2.0) / 2.0

        sample_points = [
            ("left_shoulder", left_shoulder),
            ("right_shoulder", right_shoulder),
            ("left_hem", np.array([left_shoulder[0], navel_y], dtype=np.float32)),
            ("right_hem", np.array([right_shoulder[0], navel_y], dtype=np.float32)),
            ("center", center_point),
        ]

        color_samples = []
        for sample_name, point in sample_points:
            sample_bgr = self._extract_roi_mean_bgr(
                frame,
                point[0],
                point[1],
                sample_radius,
                sample_radius,
            )
            if sample_bgr is None:
                continue

            color_samples.append(
                {
                    "name": sample_name,
                    "bgr": sample_bgr,
                    "lab": self._bgr_to_lab(sample_bgr),
                    "pos": (int(point[0]), int(point[1])),
                    "is_center": sample_name == "center",
                }
            )

        dominant_group = self._pick_dominant_color_group(color_samples)
        if dominant_group is None:
            return None

        group_bgr_values = np.asarray([sample["bgr"] for sample in dominant_group], dtype=np.float32)
        representative_bgr = tuple(int(round(channel)) for channel in group_bgr_values.mean(axis=0))
        group_positions = np.asarray([sample["pos"] for sample in dominant_group], dtype=np.float32)
        representative_pos = tuple(int(round(value)) for value in group_positions.mean(axis=0))

        return {
            "bgr": representative_bgr,
            "pos": representative_pos,
            "color_name": self._classify_bgr_color_name(representative_bgr),
            "samples": [
                {
                    "name": sample["name"],
                    "bgr": sample["bgr"],
                    "pos": sample["pos"],
                }
                for sample in color_samples
            ],
        }

    def _pick_dominant_color_group(self, color_samples):
        if not color_samples:
            return None

        lab_distance_threshold = 34.0
        groups = []
        for sample in color_samples:
            best_group = None
            best_distance = None
            for group in groups:
                group_lab = np.asarray([member["lab"] for member in group], dtype=np.float32).mean(axis=0)
                distance = float(np.linalg.norm(sample["lab"] - group_lab))
                if distance <= lab_distance_threshold and (
                    best_distance is None or distance < best_distance
                ):
                    best_distance = distance
                    best_group = group

            if best_group is None:
                groups.append([sample])
            else:
                best_group.append(sample)

        groups.sort(
            key=lambda group: (
                len(group),
                sum(1 for sample in group if not sample["is_center"]),
            ),
            reverse=True,
        )
        return groups[0]

    def _bgr_to_lab(self, bgr):
        pixel = np.uint8([[list(bgr)]])
        return cv2.cvtColor(pixel, cv2.COLOR_BGR2LAB)[0][0].astype(np.float32)

    def _compute_brightness_ratio_from_regions(self, regions):
        top_region = regions.get("top")
        bottom_region = regions.get("bottom")
        if top_region is None or bottom_region is None:
            return None

        top_bgr = top_region.get("bgr")
        bottom_bgr = bottom_region.get("bgr")
        if top_bgr is None or bottom_bgr is None:
            return None

        top_v = cv2.cvtColor(np.uint8([[list(top_bgr)]]), cv2.COLOR_BGR2HSV)[0][0][2]
        bottom_v = cv2.cvtColor(np.uint8([[list(bottom_bgr)]]), cv2.COLOR_BGR2HSV)[0][0][2]
        return round(float(top_v) / (float(bottom_v) + 1e-5), 4)

    def _classify_bgr_color_name(self, bgr):
        pixel = np.uint8([[list(bgr)]])
        h, s, v = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)[0][0]

        if v < 45:
            return "black"
        if v > 210 and s < 35:
            return "white"
        if s < 40:
            if v < 90:
                return "dark_gray"
            if v < 180:
                return "gray"
            return "light_gray"

        if h < 8 or h >= 170:
            return "red"
        if h < 18:
            return "red_orange"
        if h < 28:
            return "orange"
        if h < 38:
            return "yellow"
        if h < 50:
            return "yellow_green"
        if h < 85:
            return "green"
        if h < 100:
            return "cyan"
        if h < 130:
            return "blue"
        if h < 150:
            return "indigo"
        return "purple"

    def _find_bag_owner(self, people, bag_box):
        if not people:
            return None

        bx1, by1, bx2, by2 = bag_box
        bag_center_x = (bx1 + bx2) / 2.0
        bag_center_y = (by1 + by2) / 2.0

        best_owner = None
        best_score = -1.0

        for person in people:
            px1, py1, px2, py2 = person["box"]
            expand_x = int((px2 - px1) * 0.18)
            expanded_box = (px1 - expand_x, py1, px2 + expand_x, py2)

            if not self._point_in_box((bag_center_x, bag_center_y), expanded_box):
                continue

            intersection = self._intersection_area(expanded_box, bag_box)
            distance_penalty = self._center_distance((bag_center_x, bag_center_y), self._box_center(person["box"]))
            score = intersection - (distance_penalty * 0.15)
            if score > best_score:
                best_score = score
                best_owner = person

        return best_owner

    def _point_in_box(self, point, box):
        x, y = point
        x1, y1, x2, y2 = box
        return x1 <= x <= x2 and y1 <= y <= y2

    def _intersection_area(self, box_a, box_b):
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        return max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

    def _box_center(self, box):
        x1, y1, x2, y2 = box
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def _intersection_over_union(self, box_a, box_b):
        intersection = self._intersection_area(box_a, box_b)
        if intersection <= 0:
            return 0.0

        area_a = max(0, box_a[2] - box_a[0]) * max(0, box_a[3] - box_a[1])
        area_b = max(0, box_b[2] - box_b[0]) * max(0, box_b[3] - box_b[1])
        union = area_a + area_b - intersection
        if union <= 0:
            return 0.0
        return intersection / union

    def _center_distance(self, point_a, point_b):
        return ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** 0.5
