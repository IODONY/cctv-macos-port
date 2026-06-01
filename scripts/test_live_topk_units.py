#!/usr/bin/env python3
"""Camera-free checks for the live Top-K bridge helpers."""

from __future__ import annotations

import os
import json
import shutil
import sys
import tempfile
import threading
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from live_topk_bridge import (  # noqa: E402
    GalleryRecord,
    LiveTopKGallery,
    LiveTopKCameraContext,
    PersonClipRecorder,
    box_center_distance_ratio,
    build_topk_payload,
    export_asset,
    export_similarity_group_record,
    has_crowded_overlap,
    normalize_cam_type,
    normalize_vector,
    parse_video_source,
    resolve_tracker_config_path,
    sleep_for_finite_video_frame,
    split_cam_labels,
    split_cam_types,
    split_sources,
    source_is_finite_video,
    spatial_continuity_stitch_reason,
    tracker_config_with_reid,
    video_source_frame_interval,
    write_json,
)
from live_session_grouping import regroup_live_session  # noqa: E402
from run_live_from_camera_csv import resolve_tracker_config_arg  # noqa: E402
from visual_reid import select_diverse_crop_candidates  # noqa: E402
from visual_grouping import VisualGroupRecord, group_records, reciprocal_groups  # noqa: E402


def make_record(clip_id: str, vector: list[float]) -> GalleryRecord:
    return GalleryRecord(
        clip_id=clip_id,
        clip_path=f"/tmp/{clip_id}.mp4",
        best_frame_path=f"/tmp/{clip_id}.jpg",
        cam_id="cam_1",
        cam_label="tapo_1",
        event_id=clip_id,
        track_id=1,
        created_at=1.0,
        embedding=np.asarray(vector, dtype=np.float32),
        quality=0.9,
        duration_seconds=1.0,
        frame_count=10,
        writer_fps=25.0,
        encoded_duration_seconds=0.4,
        unique_frame_count=10,
        duplicate_frame_count=0,
        max_frame_age_seconds=0.0,
        embedding_method="unit",
    )


def test_source_parsing() -> None:
    os.environ["UNIT_RTSP_A"] = "rtsp://user:pass@example.test/stream1"
    sources = split_sources("webcam:0", "UNIT_RTSP_A")
    assert sources == ["rtsp://user:pass@example.test/stream1", "webcam:0"]
    assert split_cam_types("G,Q", 2) == ["G", "Q"]
    assert split_cam_labels("tapo_1,macbook_query", 2) == ["tapo_1", "macbook_query"]
    assert split_cam_labels("", 2) == ["cam_1", "cam_2"]
    assert normalize_cam_type("a") == "G"
    assert normalize_cam_type("c") == "Q"
    assert source_is_finite_video(parse_video_source("snapshots/testdata/example.mp4"))
    assert not source_is_finite_video(parse_video_source("webcam:0"))
    assert video_source_frame_interval(parse_video_source("snapshots/testdata/example.mp4"), 25.0) == 0.04


def test_tracker_config_resolution() -> None:
    botsort_path = resolve_tracker_config_path("botsort", "")
    assert botsort_path is not None
    assert botsort_path.name == "botsort.yaml"
    assert tracker_config_with_reid(botsort_path) is False

    botsort_reid_path = resolve_tracker_config_path("botsort", "config/trackers/botsort_reid.yaml")
    assert botsort_reid_path is not None
    assert botsort_reid_path.name == "botsort_reid.yaml"
    assert tracker_config_with_reid(botsort_reid_path) is True

    assert resolve_tracker_config_path("custom", "") is None
    assert tracker_config_with_reid(None) is None

    class Args:
        tracker_backend = "botsort"
        tracker_config_path = ""
        tracker_reid = True

    assert resolve_tracker_config_arg(Args()) == "config/trackers/botsort_reid.yaml"

    Args.tracker_reid = False
    Args.tracker_config_path = "config/trackers/botsort.yaml"
    assert resolve_tracker_config_arg(Args()) == "config/trackers/botsort.yaml"


def test_gallery_ranking() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        gallery = LiveTopKGallery(Path(tmp_dir))
        assert gallery.add_record(make_record("match", [1.0, 0.0, 0.0]))
        assert gallery.add_record(make_record("miss", [0.0, 1.0, 0.0]))
        results = gallery.rank(normalize_vector(np.asarray([1.0, 0.0, 0.0])), k=2, candidate_pool=2, fallback_score=0.5)
        assert [item["clip_id"] for item in results] == ["match", "miss"]
        assert results[0]["score"] > results[1]["score"]
        assert results[1]["fallback"] is True


def test_similarity_grouping() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        gallery = LiveTopKGallery(Path(tmp_dir))
        first = make_record("first", [1.0, 0.0, 0.0])
        second = make_record("second", [0.95, 0.05, 0.0])
        third = make_record("third", [0.0, 1.0, 0.0])

        group_a = gallery.assign_similarity_group(first, threshold=0.8)
        group_b = gallery.assign_similarity_group(second, threshold=0.8)
        group_c = gallery.assign_similarity_group(third, threshold=0.8)

        assert group_a["group_label"] == "group_001"
        assert group_b["group_label"] == "group_001"
        assert group_b["count"] == 2
        assert group_c["group_label"] == "group_002"


def test_visual_grouping_connected_chain() -> None:
    records = [
        VisualGroupRecord("a", "/tmp/a.mp4", "/tmp/a.jpg", np.asarray([1.0, 0.0], dtype=np.float32)),
        VisualGroupRecord("b", "/tmp/b.mp4", "/tmp/b.jpg", np.asarray([0.8, 0.6], dtype=np.float32)),
        VisualGroupRecord("c", "/tmp/c.mp4", "/tmp/c.jpg", np.asarray([0.28, 0.96], dtype=np.float32)),
    ]
    report = group_records(records, method="connected", threshold=0.75)
    assert report["group_count"] == 1
    assert report["group_sizes"] == [3]


def test_visual_grouping_reciprocal_filter() -> None:
    scores = np.asarray(
        [
            [1.0, 0.7, 0.9],
            [0.7, 1.0, 0.1],
            [0.9, 0.1, 1.0],
        ],
        dtype=np.float32,
    )
    groups = reciprocal_groups(scores, threshold=0.65, reciprocal_topn=1)
    assert groups == [[0, 2], [1]]


def test_topk_payload_shape() -> None:
    results = [
        {
            "rank": 1,
            "clip_id": "clip_a",
            "clip_path": "/tmp/clip_a.mp4",
            "score": 0.9,
            "cam_id": "cam_1",
            "cam_label": "tapo_1",
            "best_frame_path": "/tmp/clip_a.jpg",
            "fallback": False,
            "quality": 0.8,
        }
    ]
    flat, structured = build_topk_payload(
        "session",
        cam_id=3,
        cam_label="macbook_query",
        query_track_id=7,
        k=9,
        gallery_count=4,
        results=results,
    )
    assert flat[3] == "cam_3"
    assert flat[4] == 9
    assert flat[5] == 1
    assert flat[6] == 4
    assert flat[7:13] == [1, "clip_a", "/tmp/clip_a.mp4", 0.9, "cam_1", 0]
    assert structured["cam_label"] == "macbook_query"
    assert structured["results"][0]["clip_id"] == "clip_a"
    assert structured["results"][0]["cam_label"] == "tapo_1"


def test_export_helpers() -> None:
    test_root = PROJECT_ROOT / "logs" / "test_live_topk_units"
    shutil.rmtree(test_root, ignore_errors=True)
    source_dir = test_root / "source"
    export_dir = test_root / "export"
    source_dir.mkdir(parents=True, exist_ok=True)

    clip_path = source_dir / "clip.mp4"
    clip_path.write_bytes(b"unit-clip")
    best_path = source_dir / "best.jpg"
    cv2.imwrite(str(best_path), np.zeros((8, 8, 3), dtype=np.uint8))

    exported = export_asset(str(clip_path), export_dir / "rank_01" / "clip.mp4", "symlink", "clip_path.txt")
    assert Path(exported).exists()
    assert (export_dir / "rank_01" / "clip_path.txt").read_text(encoding="utf-8") == str(clip_path)

    path_only = export_asset(str(best_path), export_dir / "rank_01" / "best.jpg", "path", "best_path.txt")
    assert Path(path_only).name == "best_path.txt"
    assert not (export_dir / "rank_01" / "best.jpg").exists()

    write_json(export_dir / "results.json", {"ok": True})
    assert '"ok": true' in (export_dir / "results.json").read_text(encoding="utf-8")
    shutil.rmtree(test_root, ignore_errors=True)


def test_similarity_group_export() -> None:
    test_root = PROJECT_ROOT / "logs" / "test_similarity_group_export"
    shutil.rmtree(test_root, ignore_errors=True)
    source_dir = test_root / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    clip_path = source_dir / "clip.mp4"
    clip_path.write_bytes(b"unit-clip")
    best_path = source_dir / "best.jpg"
    cv2.imwrite(str(best_path), np.zeros((8, 8, 3), dtype=np.uint8))

    record = make_record("clip", [1.0, 0.0, 0.0])
    record.clip_path = str(clip_path)
    record.best_frame_path = str(best_path)
    record.similarity_group_id = 1
    record.similarity_group_label = "group_001"
    record.similarity_group_score = 1.0
    record.similarity_group_count = 1

    group_dir = export_similarity_group_record(record, test_root, "session", "symlink")
    assert Path(group_dir).name == "group_001"
    assert (Path(group_dir) / "clip.mp4").exists()
    assert (Path(group_dir) / "clip_best.jpg").exists()
    assert (Path(group_dir) / "clip.json").exists()
    shutil.rmtree(test_root, ignore_errors=True)


def test_person_clip_recorder_topn_embedding() -> None:
    class UnitEmbedder:
        method = "unit_embedder"

        def embed_bgr(self, image_bgr):
            value = float(image_bgr.mean()) + 1.0
            return normalize_vector(np.asarray([value, 1.0], dtype=np.float32)), self.method

    test_root = PROJECT_ROOT / "logs" / "test_person_clip_recorder"
    shutil.rmtree(test_root, ignore_errors=True)
    recorder = PersonClipRecorder(
        session_id="unit_session",
        snapshot_root=test_root,
        cam_id=1,
        cam_label="tapo_1",
        track_id=7,
        output_size=(64, 64),
        fps=10.0,
        record_video_mode="full-frame",
        top_n=3,
    )
    person = {"box": (10, 5, 42, 60), "confidence": 0.95}
    for index in range(5):
        frame = np.full((64, 64, 3), 30 + (index * 20), dtype=np.uint8)
        recorder.observe(frame, person, frame_index=index + 1)
        recorder.write_frame(frame, source_frame_index=index + 1, frame_age_seconds=0.02)

    record = recorder.close(
        UnitEmbedder(),
        reason="unit_done",
        min_clip_seconds=0.0,
        tracker_backend="botsort",
        source_fps=10.0,
        analyzed_fps=5.0,
        dropped_frame_count=2,
        post_roll_seconds=2.0,
        min_recorded_frames=0,
        min_unique_frames=0,
    )
    assert record is not None
    assert record.cam_label == "tapo_1"
    assert "_event_" not in record.clip_id
    assert "_t007_e" in record.clip_id
    assert record.writer_fps == 10.0
    assert record.encoded_duration_seconds == 0.5
    assert record.unique_frame_count == 5
    assert record.duplicate_frame_count == 0
    assert record.tracker_backend == "botsort"
    assert record.embedding_aggregation == "prototype_mean_top_3"
    assert record.prototype_count == 3
    assert record.prototype_score_mode == "max"
    assert record.crop_selection_strategy == "diverse-quality"
    assert len(record.top_crop_paths or []) == 3
    assert len(record.top_crop_metadata or []) == 3
    assert record.best_crop_box == [10, 5, 42, 60]
    assert record.best_crop_frame_index >= 1
    assert record.best_crop_quality > 0.0
    for item in record.top_crop_metadata or []:
        assert item["track_id"] == 7
        assert item["box"] == [10, 5, 42, 60]
        assert int(item["frame_index"]) >= 1
        assert float(item["quality"]) > 0.0
        assert item["time_bucket"] in {"early", "middle", "late"}
        assert item["pose_view_hint"] in {"front_like", "side_like", "back_or_unknown"}
        assert item["selection_reason"]
    payload = record.to_json()
    assert payload["prototype_count"] == 3
    assert payload["prototype_score_mode"] == "max"
    assert payload["crop_selection_strategy"] == "diverse-quality"
    assert payload["best_crop"]["track_id"] == 7
    assert payload["best_crop"]["box"] == [10, 5, 42, 60]
    assert len(payload["top_crop_metadata"]) == 3
    assert Path(record.clip_path).exists()
    assert Path(record.best_frame_path).exists()
    assert all(Path(path).exists() for path in record.top_crop_paths or [])
    shutil.rmtree(test_root, ignore_errors=True)


def test_tracklet_stitching_metadata() -> None:
    class UnitEmbedder:
        method = "unit_embedder"

        def embed_bgr(self, image_bgr):
            value = float(image_bgr.mean()) + 1.0
            return normalize_vector(np.asarray([value, 1.0], dtype=np.float32)), self.method

    test_root = PROJECT_ROOT / "logs" / "test_tracklet_stitching_metadata"
    shutil.rmtree(test_root, ignore_errors=True)
    recorder = PersonClipRecorder(
        session_id="unit_stitch",
        snapshot_root=test_root,
        cam_id=1,
        cam_label="tapo_1",
        track_id=3,
        output_size=(64, 64),
        fps=10.0,
        record_video_mode="full-frame",
        top_n=2,
    )
    frame = np.full((64, 64, 3), 80, dtype=np.uint8)
    recorder.observe(frame, {"box": (8, 4, 44, 62), "confidence": 0.9}, frame_index=1)
    recorder.write_frame(frame, source_frame_index=1, frame_age_seconds=0.01)
    first_embedding, first_method = recorder.stitch_embedding(UnitEmbedder())
    assert first_embedding is not None
    assert first_method == "unit_embedder"

    stitch_event = {
        "accepted": True,
        "reason": "stitched_tracklet",
        "old_track_id": 3,
        "new_track_id": 9,
        "score": 0.91,
    }
    recorder.reassign_track_id(9, stitch_event)
    recorder.observe(frame, {"box": (10, 6, 46, 62), "confidence": 0.91}, frame_index=2)
    recorder.write_frame(frame, source_frame_index=2, frame_age_seconds=0.01)

    record = recorder.close(
        UnitEmbedder(),
        reason="person_left_frame",
        min_clip_seconds=0.0,
        min_recorded_frames=0,
        min_unique_frames=0,
    )
    assert record is not None
    assert record.track_id == 9
    assert record.original_track_id == 3
    assert record.current_track_id == 9
    assert record.stitched_track_ids == [3, 9]
    assert len(record.stitch_events or []) == 1
    assert record.close_reason == "person_left_frame"
    payload = record.to_json()
    assert payload["original_track_id"] == 3
    assert payload["current_track_id"] == 9
    assert payload["stitched_track_ids"] == [3, 9]
    assert payload["stitch_event_count"] == 1
    assert payload["close_reason"] == "person_left_frame"
    shutil.rmtree(test_root, ignore_errors=True)


def test_post_roll_time_takes_priority_over_missing_grace() -> None:
    test_root = PROJECT_ROOT / "logs" / "test_post_roll_priority"
    shutil.rmtree(test_root, ignore_errors=True)
    recorder = PersonClipRecorder(
        session_id="unit_post_roll",
        snapshot_root=test_root,
        cam_id=1,
        cam_label="unit",
        track_id=3,
        output_size=(64, 64),
        fps=25.0,
        record_video_mode="full-frame",
        top_n=1,
    )
    now = 100.0
    recorder.missing_since = now - 0.5
    recorder.missing_analyses = 100
    time_module = __import__("time")
    original = time_module.monotonic
    try:
        time_module.monotonic = lambda: now
        assert recorder.should_close_after_missing(post_roll_seconds=2.0, track_missing_grace=8) is False
        assert recorder.should_close_after_missing(post_roll_seconds=-1.0, track_missing_grace=8) is True
    finally:
        time_module.monotonic = original
    if recorder.writer is not None:
        recorder.writer.release()
    shutil.rmtree(test_root, ignore_errors=True)


def test_tracklet_stitching_geometry_helpers() -> None:
    frame_shape = (720, 1280, 3)
    near = box_center_distance_ratio((100, 100, 240, 520), (120, 110, 260, 530), frame_shape)
    far = box_center_distance_ratio((100, 100, 240, 520), (900, 100, 1040, 520), frame_shape)
    assert near < 0.05
    assert far > 0.35
    assert has_crowded_overlap([
        {"box": (10, 10, 100, 200)},
        {"box": (20, 20, 120, 220)},
    ])
    assert not has_crowded_overlap([{"box": (10, 10, 100, 200)}])

    class Args:
        stitch_spatial_resume_window_seconds = 1.5
        stitch_spatial_resume_max_distance_ratio = 0.02
        stitch_spatial_resume_min_score = 0.55
        stitch_micro_gap_seconds = 0.35
        stitch_micro_gap_max_distance_ratio = 0.06
        stitch_micro_gap_min_score = 0.35

    assert spatial_continuity_stitch_reason(0.60, 1.2, 0.01, Args(), False) == "spatial_continuity_stitched"
    assert spatial_continuity_stitch_reason(0.40, 0.2, 0.04, Args(), False) == "micro_gap_spatial_stitched"
    assert spatial_continuity_stitch_reason(0.60, 1.2, 0.01, Args(), True) == ""


def test_diverse_crop_selection_prefers_temporal_variety() -> None:
    candidates = []
    for frame_index, quality, value, pose in [
        (10, 0.95, 20, "front_like"),
        (12, 0.94, 22, "front_like"),
        (40, 0.84, 120, "side_like"),
        (80, 0.80, 220, "back_or_unknown"),
        (82, 0.79, 222, "back_or_unknown"),
    ]:
        candidates.append(
            {
                "crop": np.full((32, 16, 3), value, dtype=np.uint8),
                "quality": quality,
                "frame_index": frame_index,
                "box": [10, 5, 26, 37],
                "confidence": 0.9,
                "pose_view_hint": pose,
                "body_angle_hint": {},
            }
        )
    selected = select_diverse_crop_candidates(
        candidates,
        top_n=3,
        selection_strategy="diverse-quality",
        min_frame_gap=15,
        max_similarity=0.92,
        min_quality_ratio=0.70,
    )
    assert len(selected) == 3
    assert selected[0]["selection_reason"] == "quality_best"
    assert len({item["time_bucket"] for item in selected}) >= 2
    assert len({item["pose_view_hint"] for item in selected}) >= 2


def make_stitch_context(test_root: Path):
    class Args:
        disable_tracklet_stitching = False
        stitch_window_seconds = 1.5
        stitch_reid_threshold = 0.76
        stitch_ambiguous_margin = 0.08
        stitch_max_center_distance_ratio = 0.35
        stitch_crowded_window_seconds = 2.0
        stitch_allow_crowded = False

    class UnitEmbedder:
        method = "unit_embedder"

        def embed_bgr(self, image_bgr):
            value = float(image_bgr.mean()) + 1.0
            return normalize_vector(np.asarray([value, 1.0], dtype=np.float32)), self.method

    context = object.__new__(LiveTopKCameraContext)
    context.cam_id = 1
    context.cam_label = "unit"
    context.cam_type = "G"
    context.args = Args()
    context.session_id = "unit_stitch_context"
    context.embedder = UnitEmbedder()
    context.recorders = {}
    context.pending_stitch_recorders = {}
    context.recorder_lock = threading.Lock()
    context.crowded_until = 0.0
    context.stitch_log_path = test_root / "stitch_events.jsonl"
    return context


def test_tracklet_stitching_accepts_clear_single_person_split() -> None:
    test_root = PROJECT_ROOT / "logs" / "test_tracklet_stitching_context"
    shutil.rmtree(test_root, ignore_errors=True)
    context = make_stitch_context(test_root)
    frame = np.full((96, 96, 3), 90, dtype=np.uint8)
    recorder = PersonClipRecorder(
        session_id="unit_stitch_context",
        snapshot_root=test_root,
        cam_id=1,
        cam_label="unit",
        track_id=3,
        output_size=(96, 96),
        fps=10.0,
        record_video_mode="full-frame",
        top_n=1,
    )
    recorder.observe(frame, {"box": (20, 10, 70, 92), "confidence": 0.95}, frame_index=1)
    now = 100.0
    recorder.missing_since = now - 0.2
    context.recorders[3] = recorder

    stitched = context._try_stitch_track(
        frame,
        {"track_id": 9, "box": (22, 12, 72, 92), "confidence": 0.94},
        source_frame_index=2,
        now=now,
    )
    assert stitched is True
    assert 3 in context.recorders
    assert 9 in context.recorders
    assert context.recorders[3] is context.recorders[9]
    assert context.active_recording_count() == 1
    assert context.recorders[9].stitched_track_ids == [3, 9]
    assert context.recorders[9].stitch_events[0]["accepted"] is True
    assert (test_root / "stitch_events.jsonl").exists()
    if context.recorders[9].writer is not None:
        context.recorders[9].writer.release()
    shutil.rmtree(test_root, ignore_errors=True)


def test_tracklet_stitching_rejects_recent_crowded_frame() -> None:
    test_root = PROJECT_ROOT / "logs" / "test_tracklet_stitching_crowded"
    shutil.rmtree(test_root, ignore_errors=True)
    context = make_stitch_context(test_root)
    frame = np.full((96, 96, 3), 90, dtype=np.uint8)
    recorder = PersonClipRecorder(
        session_id="unit_stitch_crowded",
        snapshot_root=test_root,
        cam_id=1,
        cam_label="unit",
        track_id=3,
        output_size=(96, 96),
        fps=10.0,
        record_video_mode="full-frame",
        top_n=1,
    )
    recorder.observe(frame, {"box": (20, 10, 70, 92), "confidence": 0.95}, frame_index=1)
    now = 100.0
    recorder.missing_since = now - 0.2
    context.recorders[3] = recorder
    context.crowded_until = now + 1.0

    stitched = context._try_stitch_track(
        frame,
        {"track_id": 9, "box": (58, 12, 94, 92), "confidence": 0.94},
        source_frame_index=2,
        now=now,
    )
    assert stitched is False
    assert 3 in context.recorders
    assert 9 not in context.recorders
    assert "recent_crowded_frame" in (test_root / "stitch_events.jsonl").read_text(encoding="utf-8")
    if context.recorders[3].writer is not None:
        context.recorders[3].writer.release()
    shutil.rmtree(test_root, ignore_errors=True)


def test_tracklet_stitching_resumes_same_pending_track_without_reid_gate() -> None:
    test_root = PROJECT_ROOT / "logs" / "test_tracklet_stitching_same_track_resume"
    shutil.rmtree(test_root, ignore_errors=True)
    context = make_stitch_context(test_root)
    frame = np.full((96, 96, 3), 90, dtype=np.uint8)
    recorder = PersonClipRecorder(
        session_id="unit_stitch_same",
        snapshot_root=test_root,
        cam_id=1,
        cam_label="unit",
        track_id=3,
        output_size=(96, 96),
        fps=10.0,
        record_video_mode="full-frame",
        top_n=1,
    )
    recorder.observe(frame, {"box": (20, 10, 70, 92), "confidence": 0.95}, frame_index=1)
    now = 100.0
    context.pending_stitch_recorders[3] = __import__("live_topk_bridge").PendingStitchRecorder(
        recorder=recorder,
        pending_since=now - 0.3,
        expires_at=now + 1.2,
        close_reason="person_left_frame",
    )
    context.crowded_until = now + 1.0

    stitched = context._try_stitch_track(
        frame,
        {"track_id": 3, "box": (23, 12, 73, 92), "confidence": 0.94},
        source_frame_index=2,
        now=now,
    )
    assert stitched is True
    assert 3 in context.recorders
    assert not context.pending_stitch_recorders
    assert context.recorders[3].stitch_events[0]["reason"] == "same_track_resumed"
    if context.recorders[3].writer is not None:
        context.recorders[3].writer.release()
    shutil.rmtree(test_root, ignore_errors=True)


def test_active_duplicate_track_absorbs_into_existing_recorder() -> None:
    test_root = PROJECT_ROOT / "logs" / "test_active_duplicate_absorb"
    shutil.rmtree(test_root, ignore_errors=True)
    context = make_stitch_context(test_root)
    frame = np.full((96, 96, 3), 90, dtype=np.uint8)
    recorder = PersonClipRecorder(
        session_id="unit_absorb",
        snapshot_root=test_root,
        cam_id=1,
        cam_label="unit",
        track_id=3,
        output_size=(96, 96),
        fps=10.0,
        record_video_mode="full-frame",
        top_n=2,
    )
    recorder.observe(frame, {"track_id": 3, "box": (20, 10, 70, 92), "confidence": 0.95}, frame_index=1)
    context.recorders[3] = recorder

    absorbed = context._try_absorb_duplicate_track(
        frame,
        {"track_id": 9, "box": (22, 12, 70, 92), "confidence": 0.94},
        source_frame_index=2,
        now=100.0,
    )
    assert absorbed is True
    assert context.recorders[3] is context.recorders[9]
    assert context.active_recording_count() == 1
    assert 9 in recorder.owned_track_ids
    assert recorder.absorbed_track_ids == [9]
    assert recorder.track_ownership_events[0]["reason"] in {
        "containment_absorbed",
        "active_duplicate_absorbed",
        "prototype_absorbed",
    }
    if recorder.writer is not None:
        recorder.writer.release()
    shutil.rmtree(test_root, ignore_errors=True)


def test_regroup_live_session_export() -> None:
    session_id = "unit_regroup"
    log_root = PROJECT_ROOT / "logs" / "topk_live" / session_id
    test_root = PROJECT_ROOT / "logs" / "test_regroup_live_session"
    shutil.rmtree(log_root, ignore_errors=True)
    shutil.rmtree(test_root, ignore_errors=True)
    source_dir = test_root / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for index, color in enumerate(((0, 0, 255), (0, 0, 255), (255, 0, 0)), start=1):
        clip_id = f"clip_{index}"
        clip_path = source_dir / f"{clip_id}.mp4"
        writer = cv2.VideoWriter(str(clip_path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (32, 32))
        assert writer.isOpened()
        for _frame_index in range(3):
            writer.write(np.full((32, 32, 3), color, dtype=np.uint8))
        writer.release()
        best_path = source_dir / f"{clip_id}_best.jpg"
        cv2.imwrite(str(best_path), np.full((32, 32, 3), color, dtype=np.uint8))
        rows.append(
            {
                "clip_id": clip_id,
                "clip_path": str(clip_path),
                "best_frame_path": str(best_path),
                "cam_id": "cam_1",
                "cam_label": "unit",
                "event_id": clip_id,
                "track_id": index,
                "created_at": float(index),
            }
        )
    log_root.mkdir(parents=True, exist_ok=True)
    with (log_root / "gallery_events.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    payload = regroup_live_session(
        session_id=session_id,
        embedding_model="hsv_histogram",
        method="reciprocal",
        threshold=0.9,
        reciprocal_topn=2,
        export_mode="symlink",
        snapshot_root=test_root / "snapshots",
        output_subdir="similarity_groups_merged",
    )
    assert payload["grouping"]["record_count"] == 3
    assert payload["grouping"]["group_count"] == 2
    output_dir = PROJECT_ROOT / payload["output_dir"]
    group_json = output_dir / "group_001" / "group.json"
    assert group_json.exists()
    group_payload = json.loads(group_json.read_text(encoding="utf-8"))
    assert group_payload["merged_clip"]["created"] is True
    assert Path(group_payload["merged_clip"]["clip_path"]).exists()
    assert group_payload["merged_clip"]["source_clip_count"] == 2
    assert (log_root / "merged_similarity_groups.json").exists()
    shutil.rmtree(log_root, ignore_errors=True)
    shutil.rmtree(test_root, ignore_errors=True)


def main() -> int:
    test_source_parsing()
    test_tracker_config_resolution()
    test_gallery_ranking()
    test_similarity_grouping()
    test_visual_grouping_connected_chain()
    test_visual_grouping_reciprocal_filter()
    test_topk_payload_shape()
    test_export_helpers()
    test_similarity_group_export()
    test_person_clip_recorder_topn_embedding()
    test_tracklet_stitching_metadata()
    test_post_roll_time_takes_priority_over_missing_grace()
    test_tracklet_stitching_geometry_helpers()
    test_diverse_crop_selection_prefers_temporal_variety()
    test_tracklet_stitching_accepts_clear_single_person_split()
    test_tracklet_stitching_rejects_recent_crowded_frame()
    test_tracklet_stitching_resumes_same_pending_track_without_reid_gate()
    test_active_duplicate_track_absorbs_into_existing_recorder()
    test_regroup_live_session_export()
    print("LIVE_TOPK_UNIT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
