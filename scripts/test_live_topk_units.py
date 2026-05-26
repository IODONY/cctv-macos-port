#!/usr/bin/env python3
"""Camera-free checks for the live Top-K bridge helpers."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from live_topk_bridge import (  # noqa: E402
    GalleryRecord,
    LiveTopKGallery,
    build_topk_payload,
    normalize_cam_type,
    normalize_vector,
    split_cam_types,
    split_sources,
)


def make_record(clip_id: str, vector: list[float]) -> GalleryRecord:
    return GalleryRecord(
        clip_id=clip_id,
        clip_path=f"/tmp/{clip_id}.mp4",
        best_frame_path=f"/tmp/{clip_id}.jpg",
        cam_id="cam_1",
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


def test_topk_payload_shape() -> None:
    results = [
        {
            "rank": 1,
            "clip_id": "clip_a",
            "clip_path": "/tmp/clip_a.mp4",
            "score": 0.9,
            "cam_id": "cam_1",
            "fallback": False,
            "quality": 0.8,
        }
    ]
    flat, structured = build_topk_payload("session", cam_id=3, query_track_id=7, k=9, gallery_count=4, results=results)
    assert flat[3] == "cam_3"
    assert flat[4] == 9
    assert flat[5] == 1
    assert flat[6] == 4
    assert flat[7:13] == [1, "clip_a", "/tmp/clip_a.mp4", 0.9, "cam_1", 0]
    assert structured["results"][0]["clip_id"] == "clip_a"


def main() -> int:
    test_source_parsing()
    test_gallery_ranking()
    test_topk_payload_shape()
    print("LIVE_TOPK_UNIT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
