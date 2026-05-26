#!/usr/bin/env python3
"""Evaluate whether labeled local clips appear to show the same identity."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
LOG_ROOT = PROJECT_ROOT / "logs" / "clip_eval"
os.environ.setdefault("YOLO_CONFIG_DIR", str(PROJECT_ROOT / "logs" / "ultralytics"))
sys.path.insert(0, str(SRC_ROOT))

VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}
PROFILE_KEYS = ("top", "bottom", "bag", "is_long_sleeve", "is_long_pants", "torso_ratio", "brightness_ratio")


@dataclass(frozen=True)
class ClipRecord:
    clip_id: str
    identity_id: str
    cam_id: str
    take_id: str
    clip_path: Path
    notes: str = ""


def resolve_inside_project(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()
    resolved = path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"Path must stay inside project root: {resolved}") from exc
    return resolved


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def load_clips(path: Path) -> dict[str, ClipRecord]:
    clips: dict[str, ClipRecord] = {}
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        required = {"clip_id", "identity_id", "cam_id", "take_id", "clip_path", "notes"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing clips.csv columns: {sorted(missing)}")
        for row in reader:
            clip_path = resolve_inside_project(row["clip_path"])
            if clip_path.suffix.lower() not in VIDEO_SUFFIXES:
                raise ValueError(f"Unsupported clip suffix: {clip_path}")
            if not clip_path.is_file():
                raise FileNotFoundError(f"Clip does not exist: {clip_path}")
            clips[row["clip_id"]] = ClipRecord(
                clip_id=row["clip_id"],
                identity_id=row["identity_id"],
                cam_id=row["cam_id"],
                take_id=row["take_id"],
                clip_path=clip_path,
                notes=row.get("notes", ""),
            )
    return clips


def load_pairs(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        required = {
            "pair_id",
            "clip_id_a",
            "clip_id_b",
            "identity_id_a",
            "identity_id_b",
            "label",
            "pair_type",
            "notes",
        }
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing pair_labels.csv columns: {sorted(missing)}")
        pairs = list(reader)
    for pair in pairs:
        if pair["label"] not in {"0", "1"}:
            raise ValueError(f"Invalid label for {pair['pair_id']}: {pair['label']}")
    return pairs


def reset_analyzer_state(analyzer) -> None:
    analyzer.frame_index = 0
    analyzer.last_inference_ms = 0.0
    analyzer.next_track_id = 1
    analyzer.tracks = {}


def person_rank(person: dict, frame_width: int) -> tuple[float, float, float]:
    x1, y1, x2, y2 = person["box"]
    observed = float(person.get("observed_frames") or 0)
    center_x = (x1 + x2) / 2.0
    center_distance = abs(center_x - (frame_width / 2.0))
    area = float(max(0, x2 - x1) * max(0, y2 - y1))
    return observed, -center_distance, area


def analyze_clip(analyzer, clip: ClipRecord, max_frames: int, sample_every: int) -> dict[str, object]:
    import cv2

    reset_analyzer_state(analyzer)
    cap = cv2.VideoCapture(str(clip.clip_path))
    if not cap.isOpened():
        return {
            "ok": False,
            "clip_id": clip.clip_id,
            "reason": "video_open_failed",
            "frames_read": 0,
            "frames_analyzed": 0,
            "profile": None,
        }

    frames_read = 0
    frames_analyzed = 0
    best_person = None
    best_profile = None
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
            frame_width = int(frame.shape[1])
            person = max(people, key=lambda candidate: person_rank(candidate, frame_width))
            profile = person.get("final_profile")
            if profile is not None:
                best_person = person
                best_profile = profile.copy()
                break
            if best_person is None or person_rank(person, frame_width) > person_rank(best_person, frame_width):
                best_person = person
    finally:
        cap.release()

    if best_profile is None:
        reason = "no_finalized_profile"
        if frames_read == 0:
            reason = "no_frames_read"
        return {
            "ok": False,
            "clip_id": clip.clip_id,
            "reason": reason,
            "frames_read": frames_read,
            "frames_analyzed": frames_analyzed,
            "profile": None,
            "warning": warning,
        }

    return {
        "ok": True,
        "clip_id": clip.clip_id,
        "reason": "profile_finalized",
        "frames_read": frames_read,
        "frames_analyzed": frames_analyzed,
        "profile": best_profile,
        "warning": warning,
    }


def missing_profile_value(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in {"", "unknown", "nan", "none"}:
        return True
    return False


def profile_valid(profile: dict[str, object] | None, keys: tuple[str, ...] = PROFILE_KEYS) -> bool:
    if profile is None:
        return False
    return all(not missing_profile_value(profile.get(key)) for key in keys)


def numeric_gap(left: dict[str, object], right: dict[str, object], key: str) -> float | None:
    try:
        return abs(float(left[key]) - float(right[key]))
    except (KeyError, TypeError, ValueError):
        return None


def type_a_match(left: dict[str, object], right: dict[str, object]) -> bool:
    if not profile_valid(left) or not profile_valid(right):
        return False
    torso_gap = numeric_gap(left, right, "torso_ratio")
    brightness_gap = numeric_gap(left, right, "brightness_ratio")
    if torso_gap is None or torso_gap > 0.08:
        return False
    if brightness_gap is None or brightness_gap > 0.35:
        return False
    if left["is_long_pants"] != right["is_long_pants"]:
        return False
    matched_attributes = sum(1 for key in ("top", "bottom", "bag", "is_long_sleeve") if left.get(key) == right.get(key))
    return matched_attributes >= 3


def type_b_match(left: dict[str, object], right: dict[str, object]) -> bool:
    required = ("bag", "torso_ratio", "brightness_ratio")
    if not profile_valid(left, required) or not profile_valid(right, required):
        return False
    if left.get("bag") != right.get("bag"):
        return False
    torso_gap = numeric_gap(left, right, "torso_ratio")
    brightness_gap = numeric_gap(left, right, "brightness_ratio")
    if torso_gap is None or torso_gap > 0.12:
        return False
    if brightness_gap is None or brightness_gap > 0.45:
        return False
    return True


def type_c_raw_score(left: dict[str, object], right: dict[str, object]) -> float:
    bag_similarity = 1.0 if left.get("bag") == right.get("bag") else 0.0
    torso_gap = numeric_gap(left, right, "torso_ratio")
    brightness_gap = numeric_gap(left, right, "brightness_ratio")
    torso_similarity = 1.0 / (1.0 + (torso_gap if torso_gap is not None else 999.0))
    brightness_similarity = 1.0 / (1.0 + (brightness_gap if brightness_gap is not None else 999.0))
    return (bag_similarity * 2.0) + torso_similarity + brightness_similarity


def compare_profiles(
    left: dict[str, object] | None,
    right: dict[str, object] | None,
    match_threshold: float,
    ambiguous_threshold: float,
) -> dict[str, object]:
    if not profile_valid(left) or not profile_valid(right):
        return {
            "outcome": "low_confidence",
            "matching_score": 0.0,
            "type_c_raw_score": 0.0,
            "type_a_match": False,
            "type_b_match": False,
            "reason": "missing_stable_profile",
        }

    assert left is not None and right is not None
    raw_score = type_c_raw_score(left, right)
    matching_score = max(0.0, min(1.0, raw_score / 4.0))
    a_match = type_a_match(left, right)
    b_match = type_b_match(left, right)
    score_match = matching_score >= match_threshold

    if score_match and (a_match or b_match):
        outcome = "matched"
    elif matching_score >= ambiguous_threshold or len({a_match, b_match, score_match}) > 1:
        outcome = "ambiguous"
    else:
        outcome = "no_match"

    return {
        "outcome": outcome,
        "matching_score": round(matching_score, 4),
        "type_c_raw_score": round(raw_score, 4),
        "type_a_match": a_match,
        "type_b_match": b_match,
        "reason": "profile_comparison",
    }


def evaluate_pairs(args: argparse.Namespace) -> dict[str, object]:
    from walnut_core import WalnutAnalyzer

    clips = load_clips(resolve_inside_project(args.clips))
    pairs = load_pairs(resolve_inside_project(args.pairs))
    analyzer = WalnutAnalyzer(vote_frame_window=args.vote_frame_window)
    profile_cache: dict[str, dict[str, object]] = {}
    results: list[dict[str, object]] = []

    for pair in pairs:
        left_clip = clips[pair["clip_id_a"]]
        right_clip = clips[pair["clip_id_b"]]
        for clip in (left_clip, right_clip):
            if clip.clip_id not in profile_cache:
                profile_cache[clip.clip_id] = analyze_clip(
                    analyzer,
                    clip,
                    max_frames=args.max_frames,
                    sample_every=args.sample_every,
                )

        left_result = profile_cache[left_clip.clip_id]
        right_result = profile_cache[right_clip.clip_id]
        comparison = compare_profiles(
            left_result.get("profile"),
            right_result.get("profile"),
            match_threshold=args.match_threshold,
            ambiguous_threshold=args.ambiguous_threshold,
        )
        expected_same = pair["label"] == "1"
        predicted_same = comparison["outcome"] == "matched"
        if comparison["outcome"] in {"ambiguous", "low_confidence"}:
            evaluation_status = "uncertain"
        else:
            evaluation_status = "correct" if expected_same == predicted_same else "incorrect"

        results.append(
            {
                **pair,
                **comparison,
                "evaluation_status": evaluation_status,
                "clip_a_path": project_relative(left_clip.clip_path),
                "clip_b_path": project_relative(right_clip.clip_path),
                "clip_a_analysis": left_result,
                "clip_b_analysis": right_result,
            }
        )

    return {
        "clips_path": args.clips,
        "pairs_path": args.pairs,
        "result_count": len(results),
        "results": results,
    }


def write_markdown_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = report["results"]
    assert isinstance(rows, list)
    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Clip Match Evaluation Report\n\n")
        fh.write(f"- Clips manifest: `{report['clips_path']}`\n")
        fh.write(f"- Pair labels: `{report['pairs_path']}`\n")
        fh.write(f"- Evaluated pairs: `{len(rows)}`\n\n")
        fh.write("| pair_id | label | outcome | score | status | clip_a | clip_b |\n")
        fh.write("| --- | --- | --- | ---: | --- | --- | --- |\n")
        for row in rows:
            fh.write(
                f"| {row['pair_id']} | {row['label']} | {row['outcome']} | "
                f"{row['matching_score']} | {row['evaluation_status']} | "
                f"{row['clip_id_a']} | {row['clip_id_b']} |\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate labeled local clip pairs.")
    parser.add_argument("--clips", default="data/labels/clips.csv")
    parser.add_argument("--pairs", default="data/labels/pair_labels.csv")
    parser.add_argument("--output-json", default="logs/clip_eval/results.json")
    parser.add_argument("--output-md", default="docs/reports/CLIP_MATCH_EVAL_REPORT.md")
    parser.add_argument("--max-frames", type=int, default=150)
    parser.add_argument("--sample-every", type=int, default=1)
    parser.add_argument("--vote-frame-window", type=int, default=75)
    parser.add_argument("--match-threshold", type=float, default=0.80)
    parser.add_argument("--ambiguous-threshold", type=float, default=0.60)
    args = parser.parse_args()

    json_path = resolve_inside_project(args.output_json)
    md_path = resolve_inside_project(args.output_md)
    report = evaluate_pairs(args)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown_report(md_path, report)
    print(f"Wrote {project_relative(json_path)}")
    print(f"Wrote {project_relative(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
