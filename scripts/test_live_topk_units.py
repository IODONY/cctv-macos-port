#!/usr/bin/env python3
"""Camera-free checks for the live Top-K bridge helpers."""

from __future__ import annotations

import os
import json
import shutil
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from live_topk_bridge import (  # noqa: E402
    GalleryRecord,
    LiveTopKGallery,
    PersonClipRecorder,
    build_topk_payload,
    export_asset,
    export_similarity_group_record,
    normalize_cam_type,
    normalize_vector,
    split_cam_labels,
    split_cam_types,
    split_sources,
    write_json,
)
from live_session_grouping import regroup_live_session  # noqa: E402
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
        recorder.write_frame(frame)

    record = recorder.close(
        UnitEmbedder(),
        reason="unit_done",
        min_clip_seconds=0.0,
        tracker_backend="botsort",
        source_fps=10.0,
        analyzed_fps=5.0,
        dropped_frame_count=2,
        post_roll_seconds=2.0,
    )
    assert record is not None
    assert record.cam_label == "tapo_1"
    assert record.tracker_backend == "botsort"
    assert record.embedding_aggregation == "mean_top_3"
    assert len(record.top_crop_paths or []) == 3
    assert Path(record.clip_path).exists()
    assert Path(record.best_frame_path).exists()
    assert all(Path(path).exists() for path in record.top_crop_paths or [])
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
        clip_path.write_bytes(b"unit-clip")
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
    assert (output_dir / "group_001" / "group.json").exists()
    assert (log_root / "merged_similarity_groups.json").exists()
    shutil.rmtree(log_root, ignore_errors=True)
    shutil.rmtree(test_root, ignore_errors=True)


def main() -> int:
    test_source_parsing()
    test_gallery_ranking()
    test_similarity_grouping()
    test_visual_grouping_connected_chain()
    test_visual_grouping_reciprocal_filter()
    test_topk_payload_shape()
    test_export_helpers()
    test_similarity_group_export()
    test_person_clip_recorder_topn_embedding()
    test_regroup_live_session_export()
    print("LIVE_TOPK_UNIT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
