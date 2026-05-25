"""
Windows TouchDesigner OSC bridge
================================

Role split
----------
- Camera Type A/B: gallery cameras that create the master visitor database.
  Finalized visitors are matched, assigned a global visitor_id, and recorded as
  5-second MP4 clips under snapshots/visitor_[id]/.
- Camera Type C: final webcam lookup camera. It analyzes only one target person
  at a time, never creates a new visitor_id, and never records a new clip. When
  it matches an existing visitor, it sends that visitor's previously recorded
  Type A/B clip history to TouchDesigner exactly once per local track.

Type C target rule
------------------
Among all detected people, Type C keeps only the person with the largest box
area while also being closest to the horizontal center of the frame. The score is
area-normalized box size minus a center-distance penalty.

OSC contract for TouchDesigner
------------------------------
- Realtime numeric status, good for OSC In CHOP:
  /walnut/realtime/cam/[cam]/person/[visitor_id]/...
- Gallery visit logs, good for OSC In DAT + touchdesigner_oscin2_callbacks.py:
  /walnut/log/cam/[cam]/visit
- Type C history trigger, good for OSC In DAT:
  /walnut/type_c/cam/[cam]/history
  Payload:
  [event_id, timestamp, matched_id, cam_id, clip_count, clip_path_1, ...]

TouchDesigner network guideline
-------------------------------
1. Use Video Stream In TOP nodes for visual camera feeds only.
2. Use OSC In CHOP on port 7000 for realtime numeric channels.
3. Use OSC In DAT on port 7000 with a callbacks DAT for visit/history events.
4. For Type C history playback, route /walnut/type_c/cam/[cam]/history rows into
   a Table DAT, then use a Select DAT or DAT Execute to put clip_path columns
   into Movie File In TOP parameters. On Windows, paths are sent with forward
   slashes so TouchDesigner can read them reliably.
"""

import argparse
import os
import threading
import time
from collections import Counter
from urllib.parse import urlparse

import cv2
from pythonosc.udp_client import SimpleUDPClient

from walnut_core import WalnutAnalyzer


COLOR_CODES = {
    "unknown": 0,
    "black": 1,
    "white": 2,
    "dark_gray": 3,
    "gray": 4,
    "light_gray": 5,
    "red": 6,
    "red_orange": 7,
    "orange": 8,
    "yellow": 9,
    "yellow_green": 10,
    "green": 11,
    "cyan": 12,
    "blue": 13,
    "indigo": 14,
    "purple": 15,
}

GARMENT_CODES = {
    "unknown": 0,
    "short": 1,
    "long": 2,
}

BAG_CODES = {
    "no": 0,
    "yes": 1,
    "unknown": -1,
}

STATUS_CODES = {
    "inactive": 0,
    "collecting": 1,
    "waiting_for_complete_profile": 2,
    "finalized": 3,
    "other_skip": 4,
}

HISTORY_STATUS_CODES = {
    "none": 0,
    "matched": 1,
    "no_match": 2,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Multi-camera RTSP -> Walnut AI -> OSC bridge for TouchDesigner"
    )
    parser.add_argument(
        "--rtsp",
        required=True,
        help=(
            'Comma-separated video sources. Use RTSP URLs and optional webcam:N tokens. '
            'Example: "rtsp://cam1,rtsp://cam2,webcam:0"'
        ),
    )
    parser.add_argument(
        "--cam-types",
        default="",
        help='Comma-separated camera operating modes. Example: "A,A,B,B,C". Defaults to all A when omitted.',
    )
    parser.add_argument("--osc-host", default="127.0.0.1", help="TouchDesigner OSC target host")
    parser.add_argument("--osc-port", type=int, default=7000, help="TouchDesigner OSC target port")
    parser.add_argument("--frame-width", type=int, default=1280, help="Capture width hint")
    parser.add_argument("--frame-height", type=int, default=720, help="Capture height hint")
    parser.add_argument("--inference-interval", type=int, default=2, help="Analyze every Nth frame per camera")
    parser.add_argument("--print-interval-frames", type=int, default=30, help="Console print interval in analyzed frames per camera")
    parser.add_argument("--snapshot-dir", default="snapshots", help="Directory to store per-visitor snapshots")
    parser.add_argument("--clip-seconds", type=float, default=5.0, help="Seconds to record after each finalized visit event")
    parser.add_argument("--log-repeat-frames", type=int, default=30, help="How many analyzed frames to repeat each visit log OSC event")
    parser.add_argument("--reconnect-delay", type=float, default=2.0, help="Seconds to wait before reconnecting a broken RTSP stream")
    parser.add_argument("--max-read-failures", type=int, default=10, help="Consecutive frame read failures before reconnecting")
    return parser.parse_args()


def split_rtsp_sources(rtsp_arg):
    sources = [item.strip() for item in rtsp_arg.split(",") if item.strip()]
    if not sources:
        raise ValueError("No video sources were provided.")
    return sources


def split_cam_types(cam_types_arg, camera_count):
    if not cam_types_arg.strip():
        return ["A"] * camera_count

    cam_types = [item.strip().upper() for item in cam_types_arg.split(",") if item.strip()]
    if len(cam_types) != camera_count:
        raise ValueError(
            f"--cam-types count ({len(cam_types)}) must match RTSP count ({camera_count})."
        )

    valid_types = {"A", "B", "C"}
    for cam_type in cam_types:
        if cam_type not in valid_types:
            raise ValueError(f"Unsupported cam type '{cam_type}'. Supported types: A, B, C.")
    return cam_types


def parse_video_source(source):
    normalized = source.strip()
    lower_source = normalized.lower()

    for prefix in ("webcam:", "usb:", "camera:"):
        if lower_source.startswith(prefix):
            camera_id_text = normalized.split(":", 1)[1].strip()
            if not camera_id_text:
                raise ValueError(f"Missing camera id in source '{source}'. Use webcam:0, webcam:1, ...")
            return {
                "kind": "webcam",
                "capture_source": int(camera_id_text),
                "display": f"webcam:{int(camera_id_text)}",
            }

    if lower_source.isdigit():
        return {
            "kind": "webcam",
            "capture_source": int(lower_source),
            "display": f"webcam:{int(lower_source)}",
        }

    parsed = urlparse(normalized)
    if parsed.scheme.lower() == "rtsp":
        return {
            "kind": "rtsp",
            "capture_source": normalized,
            "display": normalized,
        }

    return {
        "kind": "video",
        "capture_source": normalized,
        "display": normalized,
    }


def create_capture(video_source, frame_width, frame_height):
    source_info = parse_video_source(video_source)

    if source_info["kind"] == "webcam":
        cap = cv2.VideoCapture(source_info["capture_source"], cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(source_info["capture_source"])
        cap.set(cv2.CAP_PROP_FPS, 30)
    else:
        cap = cv2.VideoCapture(source_info["capture_source"], cv2.CAP_FFMPEG)
        if not cap.isOpened():
            cap = cv2.VideoCapture(source_info["capture_source"])

    if not cap.isOpened():
        return cap

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def format_shoulder_to_hip(torso_ratio):
    if torso_ratio in (None, 0):
        return ""
    return f"1:{round(1.0 / torso_ratio, 3)}"


class GlobalVisitorDB:
    def __init__(self, snapshot_root):
        self.lock = threading.Lock()
        self.snapshot_root = snapshot_root
        self.next_visitor_id = 1
        self.next_event_id = int(time.time() * 1000)
        self.records = {}
        os.makedirs(self.snapshot_root, exist_ok=True)

    def register_visit(self, profile, cam_id, cam_type):
        with self.lock:
            visitor_id = self.match_visitor(profile, cam_type)
            if str(cam_type).strip().upper() == "C":
                if visitor_id is None:
                    return {
                        "event_id": None,
                        "visitor_id": None,
                        "profile": None,
                        "matched": False,
                        "history_paths": [],
                    }

                dominant_profile = self._build_dominant_profile(self.records[visitor_id])
                return {
                    "event_id": self._next_event_id(),
                    "visitor_id": visitor_id,
                    "profile": dominant_profile,
                    "matched": True,
                    "history_paths": self.get_history_paths(visitor_id),
                }

            if visitor_id is None:
                visitor_id = self.next_visitor_id
                self.next_visitor_id += 1
                self.records[visitor_id] = self._create_record(profile, cam_id)
            else:
                self._update_record(self.records[visitor_id], profile, cam_id)

            event_id = self._next_event_id()

            dominant_profile = self._build_dominant_profile(self.records[visitor_id])
            return {
                "event_id": event_id,
                "visitor_id": visitor_id,
                "profile": dominant_profile,
                "matched": True,
                "history_paths": self.get_history_paths(visitor_id),
            }

    def _next_event_id(self):
        event_id = self.next_event_id
        self.next_event_id += 1
        return event_id

    def _create_record(self, profile, cam_id):
        record = {
            "profiles": [],
            "counters": {
                "top": Counter(),
                "bottom": Counter(),
                "bag": Counter(),
                "is_long_sleeve": Counter(),
                "is_long_pants": Counter(),
            },
            "torso_ratios": [],
            "brightness_ratios": [],
            "cams": set(),
            "clip_paths": [],
        }
        self._update_record(record, profile, cam_id)
        return record

    def _update_record(self, record, profile, cam_id, clip_path=None):
        record["profiles"].append(profile.copy())
        record["cams"].add(cam_id)
        if clip_path:
            record["clip_paths"].append(self._normalize_path_for_td(clip_path))
        for key in record["counters"]:
            value = profile.get(key)
            if value is not None:
                record["counters"][key][value] += 1
        if profile.get("torso_ratio") is not None:
            record["torso_ratios"].append(float(profile["torso_ratio"]))
        if profile.get("brightness_ratio") is not None:
            record["brightness_ratios"].append(float(profile["brightness_ratio"]))

    def _build_dominant_profile(self, record):
        profile = {}
        for key, counter in record["counters"].items():
            profile[key] = counter.most_common(1)[0][0] if counter else "unknown"
        if record["torso_ratios"]:
            profile["torso_ratio"] = round(sum(record["torso_ratios"]) / len(record["torso_ratios"]), 3)
        else:
            profile["torso_ratio"] = None
        if record["brightness_ratios"]:
            profile["brightness_ratio"] = round(sum(record["brightness_ratios"]) / len(record["brightness_ratios"]), 4)
        else:
            profile["brightness_ratio"] = None
        return profile

    def attach_clip_path(self, visitor_id, clip_path):
        with self.lock:
            record = self.records.get(visitor_id)
            if record is None:
                return
            record["clip_paths"].append(self._normalize_path_for_td(clip_path))

    def get_history_paths(self, visitor_id):
        record = self.records.get(visitor_id)
        if record is None:
            return []
        return list(record.get("clip_paths", []))

    def _normalize_path_for_td(self, path):
        return os.path.abspath(path).replace("\\", "/")

    def match_visitor(self, profile, cam_type):
        normalized_type = str(cam_type).strip().upper() or "A"
        if not self._profile_is_valid_for_mode(profile, normalized_type):
            return None

        candidates = self._collect_candidates()

        if normalized_type == "A":
            return self._match_type_a(profile, candidates)
        if normalized_type == "B":
            return self._match_type_b(profile, candidates)
        if normalized_type == "C":
            return self._match_type_c(profile, candidates)
        return self._match_type_a(profile, candidates)

    def _collect_candidates(self):
        candidates = []
        for visitor_id, record in self.records.items():
            candidates.append((visitor_id, self._build_dominant_profile(record)))
        return candidates

    def _profile_is_valid(self, profile):
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
            value = profile.get(key)
            if value is None:
                return False
            if isinstance(value, str) and value.strip().lower() in {"", "unknown", "nan", "none"}:
                return False
        return True

    def _profile_is_valid_for_mode(self, profile, cam_type):
        normalized_type = str(cam_type).strip().upper() or "A"
        if normalized_type == "A":
            return self._profile_is_valid(profile)

        required_keys = ("bag", "torso_ratio", "brightness_ratio")
        for key in required_keys:
            value = profile.get(key)
            if value is None:
                return False
            if isinstance(value, str) and value.strip().lower() in {"", "unknown", "nan", "none"}:
                return False
        return True

    def _match_type_a(self, new_profile, candidates):
        for visitor_id, candidate_profile in candidates:
            if self._profiles_match_type_a(new_profile, candidate_profile):
                return visitor_id
        return None

    def _match_type_b(self, new_profile, candidates):
        for visitor_id, candidate_profile in candidates:
            if self._profiles_match_type_b(new_profile, candidate_profile):
                return visitor_id
        return None

    def _match_type_c(self, new_profile, candidates):
        if not self._profile_is_valid_for_mode(new_profile, "C"):
            return None

        best_candidate_id = None
        best_score = None
        for visitor_id, candidate_profile in candidates:
            if not self._profile_is_valid_for_mode(candidate_profile, "C"):
                continue
            score = self._type_c_similarity_score(new_profile, candidate_profile)
            if best_score is None or score > best_score:
                best_score = score
                best_candidate_id = visitor_id
        return best_candidate_id

    def _profiles_match_type_a(self, new_profile, old_profile):
        if not self._profile_is_valid_for_mode(new_profile, "A"):
            return False
        if not self._profile_is_valid_for_mode(old_profile, "A"):
            return False

        torso_ratio_gap = self._numeric_gap(new_profile, old_profile, "torso_ratio")
        if torso_ratio_gap is None or torso_ratio_gap > 0.08:
            return False

        brightness_ratio_gap = self._numeric_gap(new_profile, old_profile, "brightness_ratio")
        if brightness_ratio_gap is None or brightness_ratio_gap > 0.35:
            return False

        if new_profile["is_long_pants"] != old_profile["is_long_pants"]:
            return False

        matched_attributes = 0
        for key in ("top", "bottom", "bag", "is_long_sleeve"):
            if new_profile.get(key) == old_profile.get(key):
                matched_attributes += 1
        return matched_attributes >= 3

    def _profiles_match_type_b(self, new_profile, old_profile):
        if not self._profile_is_valid_for_mode(new_profile, "B"):
            return False
        if not self._profile_is_valid_for_mode(old_profile, "B"):
            return False

        if new_profile.get("bag") != old_profile.get("bag"):
            return False

        torso_ratio_gap = self._numeric_gap(new_profile, old_profile, "torso_ratio")
        if torso_ratio_gap is None or torso_ratio_gap > 0.12:
            return False

        brightness_ratio_gap = self._numeric_gap(new_profile, old_profile, "brightness_ratio")
        if brightness_ratio_gap is None or brightness_ratio_gap > 0.45:
            return False

        return True

    def _type_c_similarity_score(self, new_profile, old_profile):
        bag_similarity = 1.0 if new_profile.get("bag") == old_profile.get("bag") else 0.0
        torso_ratio_gap = self._numeric_gap(new_profile, old_profile, "torso_ratio")
        brightness_ratio_gap = self._numeric_gap(new_profile, old_profile, "brightness_ratio")

        torso_similarity = 1.0 / (1.0 + (torso_ratio_gap if torso_ratio_gap is not None else 999.0))
        brightness_similarity = 1.0 / (
            1.0 + (brightness_ratio_gap if brightness_ratio_gap is not None else 999.0)
        )
        return (bag_similarity * 2.0) + torso_similarity + brightness_similarity

    def _numeric_gap(self, left_profile, right_profile, key):
        left_value = left_profile.get(key)
        right_value = right_profile.get(key)
        if left_value is None or right_value is None:
            return None
        try:
            return abs(float(left_value) - float(right_value))
        except (TypeError, ValueError):
            return None


def build_clip_path(snapshot_root, visitor_id, cam_id, event_id):
    visitor_dir = os.path.join(snapshot_root, f"visitor_{visitor_id}")
    os.makedirs(visitor_dir, exist_ok=True)
    return os.path.join(
        visitor_dir,
        f"cam_{cam_id}_event_{event_id}.mp4",
    )


def get_region_color_name(person, region_name):
    profile = person.get("final_profile")
    if profile is not None:
        return profile.get(region_name, "unknown")

    region = person.get("regions", {}).get(region_name)
    if region is None:
        return "unknown"
    return region.get("color_name", "unknown")


def get_bag_value(person):
    profile = person.get("final_profile")
    if profile is not None:
        return profile.get("bag", "unknown")
    return "yes" if person.get("bags") else "no"


def get_garment_value(person, key):
    profile = person.get("final_profile")
    if profile is not None:
        return profile.get(key, "unknown")
    return person.get(key, "unknown")


def get_status_value(person):
    skip_reason = person.get("skip_reason")
    if person.get("final_profile") is not None and skip_reason is None:
        return "finalized"
    if skip_reason == "waiting_for_complete_profile":
        return "waiting_for_complete_profile"
    if skip_reason:
        return "other_skip"
    return "collecting"


class CameraWorker(threading.Thread):
    def __init__(self, cam_id, cam_type, video_source, args, global_db, stop_event):
        super().__init__(daemon=True)
        self.cam_id = cam_id
        self.cam_type = cam_type
        self.video_source = video_source
        self.source_info = parse_video_source(video_source)
        self.args = args
        self.global_db = global_db
        self.stop_event = stop_event

        self.analyzer = WalnutAnalyzer(
            pose_model_name="yolov8n-pose.pt",
            detect_model_name="yolov8n.pt",
            person_confidence=0.45,
            pose_confidence=0.35,
            accessory_confidence=0.18,
            model_imgsz=640,
            vote_frame_window=75,
            track_max_missing=15,
        )
        self.client = SimpleUDPClient(args.osc_host, args.osc_port)
        self.frame_index = 0
        self.analyzed_frames = 0
        self.read_failures = 0
        self.last_active_person_ids = set()
        self.repeat_queue = []
        self.active_clip_recordings = []
        self.local_to_global = {}
        self.type_c_sent_track_ids = set()
        self.log_count = 0

    def run(self):
        print(
            f"[cam {self.cam_id}] Starting worker ({self.cam_type}) "
            f"for {self.source_info['display']}"
        )

        while not self.stop_event.is_set():
            cap = create_capture(self.video_source, self.args.frame_width, self.args.frame_height)
            if not cap.isOpened():
                print(
                    f"[cam {self.cam_id}] Failed to open video source "
                    f"({self.source_info['display']}). Retrying in {self.args.reconnect_delay}s."
                )
                time.sleep(self.args.reconnect_delay)
                continue

            try:
                self._capture_loop(cap)
            finally:
                cap.release()
                self._release_active_clips()

            if not self.stop_event.is_set():
                print(f"[cam {self.cam_id}] Reconnecting in {self.args.reconnect_delay}s.")
                time.sleep(self.args.reconnect_delay)

    def _capture_loop(self, cap):
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                self.read_failures += 1
                if self.read_failures >= self.args.max_read_failures:
                    print(f"[cam {self.cam_id}] Read failure threshold reached. Restarting source.")
                    break
                time.sleep(0.05)
                continue

            self.read_failures = 0
            self.frame_index += 1
            self._write_active_clips(frame)

            if self.frame_index % max(1, self.args.inference_interval) != 0:
                continue

            self.analyzed_frames += 1
            people = self.analyzer.analyze_frame(frame)
            if self.cam_type == "C":
                people = self._filter_type_c_target(people, frame.shape[1], frame.shape[0])
            self._apply_global_visitor_ids(frame, people)
            self._send_realtime_payload(people, frame.shape[1], frame.shape[0])
            self._send_log_repeat_payload()

            if self.analyzed_frames % max(1, self.args.print_interval_frames) == 0:
                self._print_results(people)

    def _apply_global_visitor_ids(self, frame, people):
        for person in people:
            track_id = int(person.get("track_id", 0))
            if track_id in self.local_to_global:
                person["id"] = self.local_to_global[track_id]

            log_record = person.get("log_record")
            if not log_record:
                continue

            registered = self.global_db.register_visit(
                log_record["profile"],
                self.cam_id,
                self.cam_type,
            )
            visitor_id = registered["visitor_id"]
            event_id = registered["event_id"]
            profile = registered["profile"]
            if self.cam_type == "C":
                self._handle_type_c_registration(track_id, person, registered)
                continue

            self.local_to_global[track_id] = visitor_id
            person["id"] = visitor_id

            clip_path = build_clip_path(
                self.args.snapshot_dir,
                visitor_id,
                self.cam_id,
                event_id,
            )
            self._start_clip_recording(clip_path, frame)
            self.global_db.attach_clip_path(visitor_id, clip_path)

            self.repeat_queue.append(
                {
                    "event_id": int(event_id),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "visitor_id": int(visitor_id),
                    "cam_id": int(self.cam_id),
                    "top": profile["top"],
                    "bottom": profile["bottom"],
                    "bag": profile["bag"],
                    "is_long_sleeve": profile["is_long_sleeve"],
                    "is_long_pants": profile["is_long_pants"],
                    "shoulder_to_hip": format_shoulder_to_hip(profile["torso_ratio"]),
                    "torso_ratio": float(profile["torso_ratio"] or 0.0),
                    "brightness_ratio": float(profile["brightness_ratio"] or 0.0),
                    "snapshot_path": clip_path,
                    "remaining_repeats": int(self.args.log_repeat_frames),
                }
            )
            self.log_count += 1
            print(
                f"[cam {self.cam_id}] Queued OSC visit log event "
                f"{event_id} for visitor {visitor_id}: {clip_path}"
            )

    def _filter_type_c_target(self, people, frame_width, frame_height):
        if len(people) <= 1:
            return people

        frame_center_x = frame_width / 2.0
        frame_area = max(1.0, float(frame_width * frame_height))

        def target_score(person):
            x1, y1, x2, y2 = person["box"]
            box_area = max(0.0, float((x2 - x1) * (y2 - y1)))
            box_center_x = (x1 + x2) / 2.0
            center_distance_ratio = abs(box_center_x - frame_center_x) / max(1.0, frame_center_x)
            return (box_area / frame_area) - (center_distance_ratio * 0.18)

        return [max(people, key=target_score)]

    def _handle_type_c_registration(self, track_id, person, registered):
        if not registered.get("matched"):
            person["id"] = int(person.get("track_id", 0))
            person["type_c_history_status"] = "no_match"
            print(f"[cam {self.cam_id}] Type C found no matching master visitor.")
            return

        visitor_id = int(registered["visitor_id"])
        person["id"] = visitor_id
        person["type_c_history_status"] = "matched"
        self.local_to_global[track_id] = visitor_id

        if track_id in self.type_c_sent_track_ids:
            return

        self.type_c_sent_track_ids.add(track_id)
        self._send_type_c_history_trigger(
            int(registered["event_id"]),
            visitor_id,
            registered.get("history_paths", []),
        )

    def _send_type_c_history_trigger(self, event_id, visitor_id, history_paths):
        payload = [
            event_id,
            time.strftime("%Y-%m-%d %H:%M:%S"),
            int(visitor_id),
            int(self.cam_id),
            int(len(history_paths)),
            *history_paths,
        ]
        self.client.send_message(f"/walnut/type_c/cam/{self.cam_id}/history", payload)
        self.client.send_message(f"/walnut/type_c/cam/{self.cam_id}/last/event_id", int(event_id))
        self.client.send_message(f"/walnut/type_c/cam/{self.cam_id}/last/matched_id", int(visitor_id))
        self.client.send_message(f"/walnut/type_c/cam/{self.cam_id}/last/clip_count", int(len(history_paths)))
        print(
            f"[cam {self.cam_id}] Type C matched visitor {visitor_id}; "
            f"sent {len(history_paths)} history clip paths."
        )

    def _start_clip_recording(self, clip_path, frame):
        height, width = frame.shape[:2]
        fps = self._estimate_output_fps()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(clip_path, fourcc, fps, (width, height))
        if not writer.isOpened():
            print(f"[cam {self.cam_id}] Failed to open clip writer: {clip_path}")
            return

        end_time = time.monotonic() + max(0.1, float(self.args.clip_seconds))
        writer.write(frame)
        self.active_clip_recordings.append(
            {
                "path": clip_path,
                "writer": writer,
                "end_time": end_time,
            }
        )
        print(f"[cam {self.cam_id}] Recording {self.args.clip_seconds:.1f}s clip: {clip_path}")

    def _write_active_clips(self, frame):
        if not self.active_clip_recordings:
            return

        now = time.monotonic()
        still_recording = []
        for recording in self.active_clip_recordings:
            writer = recording["writer"]
            if now <= recording["end_time"]:
                writer.write(frame)
                still_recording.append(recording)
            else:
                writer.release()
                print(f"[cam {self.cam_id}] Clip saved: {recording['path']}")

        self.active_clip_recordings = still_recording

    def _release_active_clips(self):
        for recording in self.active_clip_recordings:
            recording["writer"].release()
            print(f"[cam {self.cam_id}] Clip saved: {recording['path']}")
        self.active_clip_recordings = []

    def _estimate_output_fps(self):
        source_fps = 30.0
        return source_fps

    def _send_realtime_payload(self, people, frame_width, frame_height):
        self.client.send_message(f"/walnut/realtime/cam/{self.cam_id}/meta/people_count", len(people))
        self.client.send_message(f"/walnut/realtime/cam/{self.cam_id}/meta/inference_ms", float(self.analyzer.last_inference_ms))
        self.client.send_message(f"/walnut/realtime/cam/{self.cam_id}/meta/frame_width", int(frame_width))
        self.client.send_message(f"/walnut/realtime/cam/{self.cam_id}/meta/frame_height", int(frame_height))

        current_ids = set()
        for person in people:
            person_id = int(person.get("id", 0))
            current_ids.add(person_id)
            self._send_realtime_person(person, person_id, frame_width, frame_height)

        for stale_id in self.last_active_person_ids - current_ids:
            self.client.send_message(f"/walnut/realtime/cam/{self.cam_id}/person/{stale_id}/active", 0)

        self.last_active_person_ids = current_ids

    def _send_realtime_person(self, person, person_id, frame_width, frame_height):
        x1, y1, x2, y2 = person["box"]
        width = max(1.0, float(frame_width))
        height = max(1.0, float(frame_height))
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        status_name = get_status_value(person)
        base = f"/walnut/realtime/cam/{self.cam_id}/person/{person_id}"

        values = {
            "active": 1,
            "visitor_id": int(person_id),
            "track_id": int(person.get("track_id", 0)),
            "confidence": float(person.get("confidence", 0.0)),
            "x1": float(x1) / width,
            "y1": float(y1) / height,
            "x2": float(x2) / width,
            "y2": float(y2) / height,
            "cx": float(cx) / width,
            "cy": float(cy) / height,
            "w": float(x2 - x1) / width,
            "h": float(y2 - y1) / height,
            "top_code": COLOR_CODES.get(get_region_color_name(person, "top"), 0),
            "bottom_code": COLOR_CODES.get(get_region_color_name(person, "bottom"), 0),
            "bag_code": BAG_CODES.get(get_bag_value(person), -1),
            "sleeve_code": GARMENT_CODES.get(get_garment_value(person, "is_long_sleeve"), 0),
            "pants_code": GARMENT_CODES.get(get_garment_value(person, "is_long_pants"), 0),
            "torso_ratio": float(person.get("torso_ratio") or 0.0),
            "brightness_ratio": float(person.get("brightness_ratio") or 0.0),
            "observed_frames": int(person.get("observed_frames", 0)),
            "status_code": STATUS_CODES.get(status_name, 6),
            "history_status_code": HISTORY_STATUS_CODES.get(person.get("type_c_history_status", "none"), 0),
            "resolved": 1 if person.get("resolved") else 0,
        }

        for key, value in values.items():
            self.client.send_message(f"{base}/{key}", value)

    def _send_log_repeat_payload(self):
        next_queue = []

        for event in self.repeat_queue:
            self.client.send_message(
                f"/walnut/log/cam/{self.cam_id}/visit",
                [
                    event["event_id"],
                    event["timestamp"],
                    event["visitor_id"],
                    event["cam_id"],
                    event["top"],
                    event["bottom"],
                    event["bag"],
                    event["is_long_sleeve"],
                    event["is_long_pants"],
                    event["shoulder_to_hip"],
                    event["brightness_ratio"],
                    event["snapshot_path"],
                ],
            )

            self.client.send_message(f"/walnut/log/cam/{self.cam_id}/last/event_id", event["event_id"])
            self.client.send_message(f"/walnut/log/cam/{self.cam_id}/last/visitor_id", event["visitor_id"])
            self.client.send_message(f"/walnut/log/cam/{self.cam_id}/last/top_code", COLOR_CODES.get(event["top"], 0))
            self.client.send_message(f"/walnut/log/cam/{self.cam_id}/last/bottom_code", COLOR_CODES.get(event["bottom"], 0))
            self.client.send_message(f"/walnut/log/cam/{self.cam_id}/last/bag_code", BAG_CODES.get(event["bag"], -1))
            self.client.send_message(f"/walnut/log/cam/{self.cam_id}/last/sleeve_code", GARMENT_CODES.get(event["is_long_sleeve"], 0))
            self.client.send_message(f"/walnut/log/cam/{self.cam_id}/last/pants_code", GARMENT_CODES.get(event["is_long_pants"], 0))
            self.client.send_message(f"/walnut/log/cam/{self.cam_id}/last/torso_ratio", event["torso_ratio"])
            self.client.send_message(f"/walnut/log/cam/{self.cam_id}/last/brightness_ratio", event["brightness_ratio"])
            self.client.send_message(f"/walnut/log/cam/{self.cam_id}/count", int(self.log_count))

            event["remaining_repeats"] -= 1
            if event["remaining_repeats"] > 0:
                next_queue.append(event)

        self.repeat_queue = next_queue

    def _print_results(self, people):
        print(
            f"\n[cam {self.cam_id}] People: {len(people)} | Device: {self.analyzer.device} | "
            f"Inference: {self.analyzer.last_inference_ms:.1f} ms | Mode: {self.cam_type}"
        )
        if not people:
            print(f"[cam {self.cam_id}] No person detected.")
            return

        for person in people:
            print(self._format_console_summary(person))

    def _format_console_summary(self, person):
        summary = [
            f"cam={self.cam_id}",
            f"mode={self.cam_type}",
            f"people={person.get('id', 0)}",
            f"top={get_region_color_name(person, 'top')}",
            f"bottom={get_region_color_name(person, 'bottom')}",
            f"bag={get_bag_value(person)}",
            f"sleeve={get_garment_value(person, 'is_long_sleeve')}",
            f"pants={get_garment_value(person, 'is_long_pants')}",
            f"torso_ratio={person.get('torso_ratio')}",
            f"brightness_ratio={person.get('brightness_ratio')}",
            f"status={get_status_value(person)}",
        ]
        return " | ".join(summary)


def main():
    args = parse_args()
    video_sources = split_rtsp_sources(args.rtsp)
    cam_types = split_cam_types(args.cam_types, len(video_sources))

    global_db = GlobalVisitorDB(args.snapshot_dir)
    stop_event = threading.Event()
    workers = [
        CameraWorker(
            cam_id=index,
            cam_type=cam_type,
            video_source=video_source,
            args=args,
            global_db=global_db,
            stop_event=stop_event,
        )
        for index, (video_source, cam_type) in enumerate(zip(video_sources, cam_types), start=1)
    ]

    print("Starting multi-camera OSC bridge.")
    print(f"OSC target: {args.osc_host}:{args.osc_port}")
    print(f"Camera count: {len(video_sources)}")
    print(f"Camera modes: {', '.join(f'cam{idx}:{cam_type}' for idx, cam_type in enumerate(cam_types, start=1))}")
    print("Realtime OSC: /walnut/realtime/cam/[cam]/person/[visitor_id]/...")
    print("Visit log OSC: /walnut/log/cam/[cam]/visit")
    print(f"Snapshot root: {args.snapshot_dir}")

    for worker in workers:
        worker.start()

    try:
        while any(worker.is_alive() for worker in workers):
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopping all camera workers...")
        stop_event.set()
    finally:
        stop_event.set()
        for worker in workers:
            worker.join(timeout=5.0)


if __name__ == "__main__":
    main()
