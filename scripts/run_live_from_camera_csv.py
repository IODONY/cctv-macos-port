#!/usr/bin/env python3
"""Run live_topk_bridge.py from a camera CSV without putting credentials in shell history."""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start Live Top-K from config/cameras/cameras.local.csv.")
    parser.add_argument("--camera-csv", default="config/cameras/cameras.local.csv")
    parser.add_argument("--tracker-backend", choices=("botsort", "bytetrack", "custom"), default="botsort")
    parser.add_argument("--tracker-config-path", default="")
    parser.add_argument(
        "--tracker-reid",
        action="store_true",
        help="Use config/trackers/botsort_reid.yaml so BoT-SORT also uses tracker-side ReID.",
    )
    parser.add_argument("--inference-interval", type=int, default=2)
    parser.add_argument("--post-roll-seconds", type=float, default=2.0)
    parser.add_argument("--disable-tracklet-stitching", action="store_true")
    parser.add_argument("--stitch-window-seconds", type=float, default=1.5)
    parser.add_argument("--stitch-reid-threshold", type=float, default=0.76)
    parser.add_argument("--stitch-ambiguous-margin", type=float, default=0.08)
    parser.add_argument("--stitch-max-center-distance-ratio", type=float, default=0.35)
    parser.add_argument("--stitch-spatial-resume-window-seconds", type=float, default=1.5)
    parser.add_argument("--stitch-spatial-resume-max-distance-ratio", type=float, default=0.02)
    parser.add_argument("--stitch-spatial-resume-min-score", type=float, default=0.55)
    parser.add_argument("--stitch-micro-gap-seconds", type=float, default=0.35)
    parser.add_argument("--stitch-micro-gap-max-distance-ratio", type=float, default=0.06)
    parser.add_argument("--stitch-micro-gap-min-score", type=float, default=0.35)
    parser.add_argument("--stitch-crowded-window-seconds", type=float, default=2.0)
    parser.add_argument("--stitch-crowded-near-distance-ratio", type=float, default=0.08)
    parser.add_argument("--stitch-allow-crowded", action="store_true")
    parser.add_argument("--disable-duplicate-track-suppression", action="store_true")
    parser.add_argument("--duplicate-absorb-reid-threshold", type=float, default=0.76)
    parser.add_argument("--duplicate-absorb-max-center-distance-ratio", type=float, default=0.12)
    parser.add_argument("--duplicate-absorb-min-iou", type=float, default=0.50)
    parser.add_argument("--duplicate-absorb-min-containment", type=float, default=0.85)
    parser.add_argument("--duplicate-absorb-low-quality-max", type=float, default=0.45)
    parser.add_argument("--duplicate-absorb-low-quality-distance-ratio", type=float, default=0.08)
    parser.add_argument("--duplicate-track-max-quality", type=float, default=0.45)
    parser.add_argument("--duplicate-track-min-iou", type=float, default=0.12)
    parser.add_argument("--duplicate-track-max-center-distance-ratio", type=float, default=0.10)
    parser.add_argument("--min-clip-seconds", type=float, default=1.5)
    parser.add_argument("--min-gallery-crop-quality", type=float, default=0.45)
    parser.add_argument("--live-visual-top-n", type=int, default=6)
    parser.add_argument("--crop-selection-strategy", choices=("diverse-quality", "quality-only"), default="diverse-quality")
    parser.add_argument("--prototype-score-mode", choices=("max", "top2-mean", "mean"), default="max")
    parser.add_argument("--crop-diversity-min-frame-gap", type=int, default=15)
    parser.add_argument("--crop-diversity-max-similarity", type=float, default=0.92)
    parser.add_argument("--crop-min-quality-ratio", type=float, default=0.70)
    parser.add_argument("--topk", type=int, default=12)
    parser.add_argument("--candidate-pool", type=int, default=60)
    parser.add_argument("--topk-selection-mode", choices=("score", "camera-covered"), default="camera-covered")
    parser.add_argument(
        "--coverage-cam-labels",
        default="tapo_1,tapo_2,tapo_3,tapo_4,tapo_5,tapo_6,tapo_7,tapo_8,tapo_9",
        help="Comma-separated gallery labels that should each occupy one fixed Top-K slot.",
    )
    parser.add_argument("--frame-width", type=int, default=1280)
    parser.add_argument("--frame-height", type=int, default=720)
    parser.add_argument("--recording-fps", type=float, default=25.0)
    parser.add_argument("--recording-stale-frame-seconds", type=float, default=1.0)
    parser.add_argument("--recording-reconnect-grace-seconds", type=float, default=3.0)
    parser.add_argument("--min-recorded-frames", type=int, default=0)
    parser.add_argument("--min-unique-frames", type=int, default=5)
    parser.add_argument("--rtsp-open-timeout-ms", type=int, default=5000)
    parser.add_argument("--rtsp-read-timeout-ms", type=int, default=5000)
    parser.add_argument("--max-open-retry-delay", type=float, default=30.0)
    parser.add_argument("--embedding-model", default="osnet_x0_25")
    parser.add_argument("--record-video-mode", choices=("full-frame", "person-crop"), default="full-frame")
    parser.add_argument("--storage-layout", choices=("camera", "similarity"), default="similarity")
    parser.add_argument("--similarity-group-threshold", type=float, default=0.72)
    parser.add_argument("--similarity-export-mode", choices=("symlink", "copy", "path"), default="symlink")
    parser.add_argument("--merge-method", choices=("connected", "reciprocal"), default="reciprocal")
    parser.add_argument("--merge-threshold", type=float, default=0.65)
    parser.add_argument("--merge-reciprocal-topn", type=int, default=4)
    parser.add_argument("--no-session-end-merge", action="store_true")
    parser.add_argument("--export-topk-dir", default="snapshots/live_topk_exports")
    parser.add_argument("--max-runtime-seconds", type=float, default=0.0)
    parser.add_argument("--disable-osc", action="store_true")
    parser.add_argument("--osc-dry-run", action="store_true")
    parser.add_argument("--show-preview", action="store_true")
    parser.add_argument("--preview-reid-crops", action="store_true")
    parser.add_argument("--skip-webcam-preflight", action="store_true")
    parser.add_argument("bridge_args", nargs=argparse.REMAINDER, help="Extra args passed after -- to live_topk_bridge.py")
    return parser.parse_args()


def truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def build_rtsp_url(row: dict[str, str]) -> str:
    username = row.get("username", "").strip()
    password = row.get("password", "").strip()
    ip = row.get("ip", "").strip()
    path = row.get("path", "").strip()
    if not ip:
        raise ValueError(f"RTSP row is missing ip: {row}")
    if path and not path.startswith("/"):
        path = f"/{path}"
    auth = f"{quote(username, safe='')}:{quote(password, safe='')}@" if (username or password) else ""
    return f"rtsp://{auth}{ip}{path}"


def build_source(row: dict[str, str]) -> str:
    explicit_source = row.get("source", "").strip()
    source_type = row.get("source_type", "rtsp").strip().lower()
    if explicit_source:
        return explicit_source
    if source_type == "rtsp":
        return build_rtsp_url(row)
    if source_type == "webcam":
        camera_no = row.get("camera_no", "0").strip() or "0"
        return f"webcam:{camera_no}"
    if source_type in {"file", "video"}:
        raise ValueError("file/video rows must set the source column.")
    raise ValueError(f"Unsupported source_type '{source_type}' in row: {row}")


def redact_source(source: str) -> str:
    parsed = urlparse(source)
    if parsed.scheme.lower() != "rtsp" or parsed.password is None:
        return source
    username = parsed.username or ""
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{username}:***@{host}{port}" if username else f"***@{host}{port}"
    return parsed._replace(netloc=netloc).geturl()


def load_camera_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Camera CSV not found: {csv_path}\n"
            "Copy config/cameras/cameras.example.csv to config/cameras/cameras.local.csv "
            "and edit only that local file."
        )
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    enabled_rows = [row for row in rows if truthy(row.get("enabled", "1"))]
    if not enabled_rows:
        raise ValueError(f"No enabled cameras in {csv_path}")
    return enabled_rows


def resolve_tracker_config_arg(args: argparse.Namespace) -> str:
    config_path = str(args.tracker_config_path or "").strip()
    if not args.tracker_reid:
        return config_path
    if args.tracker_backend != "botsort":
        raise ValueError("--tracker-reid can only be used with --tracker-backend botsort")
    if config_path:
        raise ValueError("Use either --tracker-reid or --tracker-config-path, not both.")
    return "config/trackers/botsort_reid.yaml"


def main() -> int:
    args = parse_args()
    rows = load_camera_rows(resolve_project_path(args.camera_csv))
    tracker_config_arg = resolve_tracker_config_arg(args)

    env = os.environ.copy()
    env_names = []
    roles = []
    labels = []
    for index, row in enumerate(rows, start=1):
        source = build_source(row)
        env_name = f"LIVE_TOPK_SOURCE_{index}"
        env[env_name] = source
        env_names.append(env_name)
        roles.append(str(row.get("role", "G") or "G").strip().upper())
        labels.append(str(row.get("label", f"cam_{index}") or f"cam_{index}").strip())
        print(f"source {index}: role={roles[-1]} label={labels[-1]} source={redact_source(source)}")

    command = [
        sys.executable,
        str(PROJECT_ROOT / "src" / "live_topk_bridge.py"),
        "--rtsp-envs",
        ",".join(env_names),
        "--cam-types",
        ",".join(roles),
        "--cam-labels",
        ",".join(labels),
        "--tracker-backend",
        args.tracker_backend,
        "--inference-interval",
        str(max(1, int(args.inference_interval))),
        "--post-roll-seconds",
        str(args.post_roll_seconds),
        "--stitch-window-seconds",
        str(args.stitch_window_seconds),
        "--stitch-reid-threshold",
        str(args.stitch_reid_threshold),
        "--stitch-ambiguous-margin",
        str(args.stitch_ambiguous_margin),
        "--stitch-max-center-distance-ratio",
        str(args.stitch_max_center_distance_ratio),
        "--stitch-spatial-resume-window-seconds",
        str(args.stitch_spatial_resume_window_seconds),
        "--stitch-spatial-resume-max-distance-ratio",
        str(args.stitch_spatial_resume_max_distance_ratio),
        "--stitch-spatial-resume-min-score",
        str(args.stitch_spatial_resume_min_score),
        "--stitch-micro-gap-seconds",
        str(args.stitch_micro_gap_seconds),
        "--stitch-micro-gap-max-distance-ratio",
        str(args.stitch_micro_gap_max_distance_ratio),
        "--stitch-micro-gap-min-score",
        str(args.stitch_micro_gap_min_score),
        "--stitch-crowded-window-seconds",
        str(args.stitch_crowded_window_seconds),
        "--stitch-crowded-near-distance-ratio",
        str(args.stitch_crowded_near_distance_ratio),
        "--duplicate-absorb-reid-threshold",
        str(args.duplicate_absorb_reid_threshold),
        "--duplicate-absorb-max-center-distance-ratio",
        str(args.duplicate_absorb_max_center_distance_ratio),
        "--duplicate-absorb-min-iou",
        str(args.duplicate_absorb_min_iou),
        "--duplicate-absorb-min-containment",
        str(args.duplicate_absorb_min_containment),
        "--duplicate-absorb-low-quality-max",
        str(args.duplicate_absorb_low_quality_max),
        "--duplicate-absorb-low-quality-distance-ratio",
        str(args.duplicate_absorb_low_quality_distance_ratio),
        "--duplicate-track-max-quality",
        str(args.duplicate_track_max_quality),
        "--duplicate-track-min-iou",
        str(args.duplicate_track_min_iou),
        "--duplicate-track-max-center-distance-ratio",
        str(args.duplicate_track_max_center_distance_ratio),
        "--min-clip-seconds",
        str(args.min_clip_seconds),
        "--min-gallery-crop-quality",
        str(args.min_gallery_crop_quality),
        "--live-visual-top-n",
        str(max(1, int(args.live_visual_top_n))),
        "--crop-selection-strategy",
        args.crop_selection_strategy,
        "--prototype-score-mode",
        args.prototype_score_mode,
        "--crop-diversity-min-frame-gap",
        str(args.crop_diversity_min_frame_gap),
        "--crop-diversity-max-similarity",
        str(args.crop_diversity_max_similarity),
        "--crop-min-quality-ratio",
        str(args.crop_min_quality_ratio),
        "--topk",
        str(max(1, int(args.topk))),
        "--candidate-pool",
        str(max(1, int(args.candidate_pool))),
        "--topk-selection-mode",
        args.topk_selection_mode,
        "--coverage-cam-labels",
        args.coverage_cam_labels,
        "--frame-width",
        str(args.frame_width),
        "--frame-height",
        str(args.frame_height),
        "--recording-fps",
        str(args.recording_fps),
        "--recording-stale-frame-seconds",
        str(args.recording_stale_frame_seconds),
        "--recording-reconnect-grace-seconds",
        str(args.recording_reconnect_grace_seconds),
        "--min-recorded-frames",
        str(args.min_recorded_frames),
        "--min-unique-frames",
        str(args.min_unique_frames),
        "--rtsp-open-timeout-ms",
        str(args.rtsp_open_timeout_ms),
        "--rtsp-read-timeout-ms",
        str(args.rtsp_read_timeout_ms),
        "--max-open-retry-delay",
        str(args.max_open_retry_delay),
        "--embedding-model",
        args.embedding_model,
        "--record-video-mode",
        args.record_video_mode,
        "--storage-layout",
        args.storage_layout,
        "--similarity-group-threshold",
        str(args.similarity_group_threshold),
        "--similarity-export-mode",
        args.similarity_export_mode,
        "--merge-method",
        args.merge_method,
        "--merge-threshold",
        str(args.merge_threshold),
        "--merge-reciprocal-topn",
        str(max(1, int(args.merge_reciprocal_topn))),
    ]
    if tracker_config_arg:
        command.extend(["--tracker-config-path", tracker_config_arg])
    if args.export_topk_dir:
        command.extend(["--export-topk-dir", args.export_topk_dir])
    if args.max_runtime_seconds > 0:
        command.extend(["--max-runtime-seconds", str(args.max_runtime_seconds)])
    if args.disable_osc:
        command.append("--disable-osc")
    if args.disable_tracklet_stitching:
        command.append("--disable-tracklet-stitching")
    if args.stitch_allow_crowded:
        command.append("--stitch-allow-crowded")
    if args.disable_duplicate_track_suppression:
        command.append("--disable-duplicate-track-suppression")
    if args.osc_dry_run:
        command.append("--osc-dry-run")
    if args.show_preview:
        command.append("--show-preview")
    if args.preview_reid_crops:
        command.append("--preview-reid-crops")
    if args.skip_webcam_preflight:
        command.append("--skip-webcam-preflight")
    if args.no_session_end_merge:
        command.append("--no-session-end-merge")
    if args.bridge_args:
        extra_args = args.bridge_args[1:] if args.bridge_args[0] == "--" else args.bridge_args
        command.extend(extra_args)

    print("starting live_topk_bridge.py")
    return subprocess.call(command, cwd=str(PROJECT_ROOT), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
