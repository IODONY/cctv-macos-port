#!/usr/bin/env python3
"""Evaluate whether labeled local clips appear to show the same identity."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import median


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
LOG_ROOT = PROJECT_ROOT / "logs" / "clip_eval"
os.environ.setdefault("YOLO_CONFIG_DIR", str(PROJECT_ROOT / "logs" / "ultralytics"))
sys.path.insert(0, str(SRC_ROOT))

VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}
PROFILE_KEYS = ("top", "bottom", "bag", "is_long_sleeve", "is_long_pants", "torso_ratio", "brightness_ratio")
DEFAULT_WEIGHTS = {
    "top": 1.4,
    "bottom": 1.0,
    "bag": 0.8,
    "is_long_sleeve": 0.7,
    "is_long_pants": 0.5,
    "torso_ratio": 1.0,
    "brightness_ratio": 0.8,
}
DEFAULT_SAME_CAMERA_WEIGHTS = {
    "top": 1.5,
    "bottom": 0.9,
    "bag": 0.8,
    "is_long_sleeve": 0.6,
    "is_long_pants": 0.4,
    "torso_ratio": 1.0,
    "brightness_ratio": 0.7,
}
DEFAULT_CROSS_CAMERA_WEIGHTS = {
    "top": 1.9,
    "bottom": 0.35,
    "bag": 0.7,
    "is_long_sleeve": 0.45,
    "is_long_pants": 0.25,
    "torso_ratio": 1.25,
    "brightness_ratio": 0.2,
}
CATEGORICAL_KEYS = ("top", "bottom", "bag", "is_long_sleeve", "is_long_pants")
NUMERIC_KEYS = ("torso_ratio", "brightness_ratio")


@dataclass(frozen=True)
class ClipRecord:
    clip_id: str
    dataset_id: str
    identity_id: str
    cam_id: str
    take_id: str
    event_id: str
    clip_path: Path
    layout_type: str = ""
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
                dataset_id=row.get("dataset_id") or "root",
                identity_id=row["identity_id"],
                cam_id=row["cam_id"],
                take_id=row["take_id"],
                event_id=row.get("event_id", ""),
                clip_path=clip_path,
                layout_type=row.get("layout_type", ""),
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


def profile_from_person_view(person: dict) -> dict[str, object]:
    profile = {
        "bag": "yes" if person.get("bags") else "no",
        "is_long_sleeve": person.get("is_long_sleeve", "unknown"),
        "is_long_pants": person.get("is_long_pants", "unknown"),
        "torso_ratio": person.get("torso_ratio"),
        "brightness_ratio": person.get("brightness_ratio"),
    }
    for region_name in ("top", "bottom"):
        region = person.get("regions", {}).get(region_name)
        profile[region_name] = region.get("color_name", "unknown") if region is not None else "unknown"
    return profile


def valid_profile_value(value: object) -> bool:
    return not missing_profile_value(value)


def categorical_vote(values: list[object]) -> tuple[object, int, float]:
    valid_values = [value for value in values if valid_profile_value(value)]
    if not valid_values:
        return "unknown", 0, 0.0
    counter = Counter(valid_values)
    value, count = counter.most_common(1)[0]
    return value, count, float(count) / float(len(valid_values))


def numeric_median(values: list[object], ndigits: int) -> tuple[float | None, int, float]:
    numeric_values: list[float] = []
    for value in values:
        if missing_profile_value(value):
            continue
        try:
            numeric_values.append(float(value))
        except (TypeError, ValueError):
            continue
    if not numeric_values:
        return None, 0, 0.0
    return round(float(median(numeric_values)), ndigits), len(numeric_values), 1.0


def build_evidence_profile(samples: list[dict[str, object]]) -> dict[str, object]:
    profile: dict[str, object] = {}
    support_counts: dict[str, int] = {}
    confidence: dict[str, float] = {}
    total_samples = len(samples)

    for key in CATEGORICAL_KEYS:
        value, support, field_confidence = categorical_vote([sample.get(key) for sample in samples])
        profile[key] = value
        support_counts[key] = support
        confidence[key] = round(field_confidence, 4)

    for key in NUMERIC_KEYS:
        value, support, field_confidence = numeric_median(
            [sample.get(key) for sample in samples],
            ndigits=4 if key == "brightness_ratio" else 3,
        )
        profile[key] = value
        support_counts[key] = support
        confidence[key] = round(field_confidence, 4)

    missing_fields = [key for key in PROFILE_KEYS if missing_profile_value(profile.get(key))]
    return {
        "profile": profile,
        "sample_count": total_samples,
        "support_counts": support_counts,
        "field_confidence": confidence,
        "missing_fields": missing_fields,
    }


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
    provisional_profile = None
    provisional_frames = 0
    evidence_samples: list[dict[str, object]] = []
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
            evidence_samples.append(profile_from_person_view(person))
            profile = person.get("final_profile")
            if profile is not None:
                best_person = person
                best_profile = profile.copy()
                continue
            if best_person is None or person_rank(person, frame_width) > person_rank(best_person, frame_width):
                best_person = person
                provisional_profile = profile_from_person_view(person)
                provisional_frames = int(person.get("observed_frames") or frames_analyzed)
    finally:
        cap.release()

    evidence = build_evidence_profile(evidence_samples)
    evidence_profile = evidence["profile"]
    evidence_status = "evidence" if evidence["sample_count"] else "missing"

    if best_profile is None:
        reason = "no_finalized_profile"
        if frames_read == 0:
            reason = "no_frames_read"
        if provisional_profile is not None:
            reason = "provisional_profile_only"
        return {
            "ok": evidence["sample_count"] > 0 or provisional_profile is not None,
            "clip_id": clip.clip_id,
            "reason": reason,
            "frames_read": frames_read,
            "frames_analyzed": frames_analyzed,
            "profile": evidence_profile if evidence["sample_count"] else provisional_profile,
            "profile_status": evidence_status if evidence["sample_count"] else "provisional" if provisional_profile is not None else "missing",
            "profile_source": "evidence_profile" if evidence["sample_count"] else "provisional_frame",
            "evidence": evidence,
            "provisional_observed_frames": provisional_frames,
            "warning": warning,
        }

    return {
        "ok": True,
        "clip_id": clip.clip_id,
        "reason": "profile_finalized",
        "frames_read": frames_read,
        "frames_analyzed": frames_analyzed,
        "profile": evidence_profile if evidence["sample_count"] else best_profile,
        "final_profile": best_profile,
        "profile_status": "evidence" if evidence["sample_count"] else "finalized",
        "profile_source": "evidence_profile",
        "evidence": evidence,
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


def parse_weights(weights_text: str | None, base_weights: dict[str, float] | None = None) -> dict[str, float]:
    weights = (base_weights or DEFAULT_WEIGHTS).copy()
    if not weights_text:
        return weights
    for item in weights_text.split(","):
        if not item.strip():
            continue
        key, _, value = item.partition("=")
        key = key.strip()
        if key not in weights:
            raise ValueError(f"Unsupported weight key: {key}")
        weights[key] = float(value)
    return weights


def build_weight_sets(args: argparse.Namespace) -> tuple[dict[str, float], dict[str, float]]:
    if args.weights:
        shared = parse_weights(args.weights)
        return shared, shared.copy()
    same_camera = parse_weights(args.same_camera_weights, DEFAULT_SAME_CAMERA_WEIGHTS)
    cross_camera = parse_weights(args.cross_camera_weights, DEFAULT_CROSS_CAMERA_WEIGHTS)
    return same_camera, cross_camera


def categorical_similarity(left: dict[str, object], right: dict[str, object], key: str) -> float:
    if missing_profile_value(left.get(key)) or missing_profile_value(right.get(key)):
        return 0.0
    return 1.0 if left.get(key) == right.get(key) else 0.0


def categorical_mismatch(left: dict[str, object], right: dict[str, object], key: str) -> bool:
    if missing_profile_value(left.get(key)) or missing_profile_value(right.get(key)):
        return False
    return left.get(key) != right.get(key)


def strong_no_match_reasons(left: dict[str, object], right: dict[str, object]) -> list[str]:
    reasons: list[str] = []
    if categorical_mismatch(left, right, "top") and categorical_mismatch(left, right, "bag"):
        reasons.append("top_and_bag_mismatch")
    if categorical_mismatch(left, right, "is_long_sleeve") and categorical_mismatch(left, right, "is_long_pants"):
        reasons.append("sleeve_and_pants_mismatch")
    return reasons


def numeric_similarity(left: dict[str, object], right: dict[str, object], key: str, scale: float) -> float:
    gap = numeric_gap(left, right, key)
    if gap is None:
        return 0.0
    return 1.0 / (1.0 + (gap / scale))


def values_comparable(left: dict[str, object], right: dict[str, object], key: str) -> bool:
    if key in NUMERIC_KEYS:
        return numeric_gap(left, right, key) is not None
    return not missing_profile_value(left.get(key)) and not missing_profile_value(right.get(key))


def weighted_similarity(
    left: dict[str, object],
    right: dict[str, object],
    weights: dict[str, float],
) -> tuple[float, dict[str, float], float, list[str]]:
    components = {
        "top": categorical_similarity(left, right, "top"),
        "bottom": categorical_similarity(left, right, "bottom"),
        "bag": categorical_similarity(left, right, "bag"),
        "is_long_sleeve": categorical_similarity(left, right, "is_long_sleeve"),
        "is_long_pants": categorical_similarity(left, right, "is_long_pants"),
        "torso_ratio": numeric_similarity(left, right, "torso_ratio", 0.12),
        "brightness_ratio": numeric_similarity(left, right, "brightness_ratio", 0.45),
    }
    missing_keys = [key for key in components if not values_comparable(left, right, key)]
    available_weight = sum(max(0.0, weights[key]) for key in components if key not in missing_keys)
    if available_weight <= 0.0:
        return 0.0, components, 0.0, missing_keys
    score = sum(
        components[key] * max(0.0, weights[key])
        for key in components
        if key not in missing_keys
    ) / available_weight
    return score, components, available_weight, missing_keys


def compare_profiles(
    left: dict[str, object] | None,
    right: dict[str, object] | None,
    match_threshold: float,
    ambiguous_threshold: float,
    weights: dict[str, float],
    allow_provisional: bool,
    left_status: str,
    right_status: str,
    pair_mode: str,
    min_available_weight: float,
) -> dict[str, object]:
    if left is None or right is None:
        return {
            "outcome": "low_confidence",
            "matching_score": 0.0,
            "type_c_raw_score": 0.0,
            "type_a_match": False,
            "type_b_match": False,
            "reason": "missing_stable_profile",
            "pair_mode": pair_mode,
        }

    raw_score = type_c_raw_score(left, right)
    matching_score, components, available_weight, missing_keys = weighted_similarity(left, right, weights)
    matching_score = max(0.0, min(1.0, matching_score))
    a_match = type_a_match(left, right)
    b_match = type_b_match(left, right)
    score_match = matching_score >= match_threshold
    no_match_reasons = strong_no_match_reasons(left, right)
    provisional = left_status not in {"finalized", "evidence"} or right_status not in {"finalized", "evidence"}

    if available_weight < min_available_weight:
        outcome = "low_confidence"
    elif provisional and not allow_provisional:
        outcome = "low_confidence"
    elif score_match and no_match_reasons:
        outcome = "ambiguous"
    elif provisional and score_match:
        outcome = "ambiguous"
    elif provisional:
        outcome = "low_confidence"
    elif score_match:
        outcome = "matched"
    elif no_match_reasons:
        outcome = "no_match"
    elif matching_score >= ambiguous_threshold or len({a_match, b_match, score_match}) > 1:
        outcome = "ambiguous"
    else:
        outcome = "no_match"

    return {
        "outcome": outcome,
        "matching_score": round(matching_score, 4),
        "type_c_raw_score": round(raw_score, 4),
        "weighted_components": {key: round(value, 4) for key, value in components.items()},
        "available_weight": round(available_weight, 4),
        "missing_comparison_keys": missing_keys,
        "strong_no_match_reasons": no_match_reasons,
        "type_a_match": a_match,
        "type_b_match": b_match,
        "reason": "profile_comparison",
        "pair_mode": pair_mode,
    }


def evaluate_pairs(args: argparse.Namespace) -> dict[str, object]:
    from walnut_core import WalnutAnalyzer

    clips = load_clips(resolve_inside_project(args.clips))
    pairs = load_pairs(resolve_inside_project(args.pairs))
    same_camera_weights, cross_camera_weights = build_weight_sets(args)
    analyzer = WalnutAnalyzer(vote_frame_window=args.vote_frame_window)
    profile_cache: dict[str, dict[str, object]] = {}
    results: list[dict[str, object]] = []

    for pair in pairs:
        left_clip = clips[pair["clip_id_a"]]
        right_clip = clips[pair["clip_id_b"]]
        pair_mode = "same_camera" if left_clip.cam_id == right_clip.cam_id else "cross_camera"
        weights = same_camera_weights if pair_mode == "same_camera" else cross_camera_weights
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
            weights=weights,
            allow_provisional=args.allow_provisional,
            left_status=str(left_result.get("profile_status") or "missing"),
            right_status=str(right_result.get("profile_status") or "missing"),
            pair_mode=pair_mode,
            min_available_weight=args.min_available_weight,
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
        "same_camera_weights": same_camera_weights,
        "cross_camera_weights": cross_camera_weights,
        "weights": {"same_camera": same_camera_weights, "cross_camera": cross_camera_weights},
        "match_threshold": args.match_threshold,
        "ambiguous_threshold": args.ambiguous_threshold,
        "min_available_weight": args.min_available_weight,
        "allow_provisional": args.allow_provisional,
        "results": results,
    }


def summarize_rows(rows: list[dict[str, object]]) -> dict[str, dict[str, int]]:
    outcome_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    label_outcomes: dict[str, int] = {}
    for row in rows:
        outcome = str(row["outcome"])
        status = str(row["evaluation_status"])
        label_key = f"{row['label']}:{outcome}"
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1
        label_outcomes[label_key] = label_outcomes.get(label_key, 0) + 1
    return {
        "outcomes": outcome_counts,
        "evaluation_status": status_counts,
        "label_outcomes": label_outcomes,
    }


def evaluate_status(label: str, outcome: str) -> str:
    if outcome in {"ambiguous", "low_confidence"}:
        return "uncertain"
    predicted_same = outcome == "matched"
    expected_same = label == "1"
    return "correct" if expected_same == predicted_same else "incorrect"


def rescore_rows(
    rows: list[dict[str, object]],
    *,
    same_camera_weights: dict[str, float],
    cross_camera_weights: dict[str, float],
    match_threshold: float,
    ambiguous_threshold: float,
    min_available_weight: float,
    allow_provisional: bool,
) -> list[dict[str, object]]:
    rescored: list[dict[str, object]] = []
    for row in rows:
        pair_mode = str(row.get("pair_mode") or "cross_camera")
        weights = same_camera_weights if pair_mode == "same_camera" else cross_camera_weights
        left_result = row["clip_a_analysis"]
        right_result = row["clip_b_analysis"]
        assert isinstance(left_result, dict)
        assert isinstance(right_result, dict)
        comparison = compare_profiles(
            left_result.get("profile"),
            right_result.get("profile"),
            match_threshold=match_threshold,
            ambiguous_threshold=ambiguous_threshold,
            weights=weights,
            allow_provisional=allow_provisional,
            left_status=str(left_result.get("profile_status") or "missing"),
            right_status=str(right_result.get("profile_status") or "missing"),
            pair_mode=pair_mode,
            min_available_weight=min_available_weight,
        )
        rescored.append(
            {
                **row,
                **comparison,
                "evaluation_status": evaluate_status(str(row["label"]), str(comparison["outcome"])),
            }
        )
    return rescored


def build_calibration_candidates(report: dict[str, object]) -> list[dict[str, object]]:
    rows = report["results"]
    assert isinstance(rows, list)
    same_camera_weights = report["same_camera_weights"]
    cross_camera_weights = report["cross_camera_weights"]
    assert isinstance(same_camera_weights, dict)
    assert isinstance(cross_camera_weights, dict)
    top_torso_cross = {
        **cross_camera_weights,
        "top": 2.1,
        "bottom": 0.25,
        "torso_ratio": 1.45,
        "brightness_ratio": 0.12,
    }
    weight_sets = [
        ("camera_aware_default", same_camera_weights, cross_camera_weights),
        ("top_torso_cross_camera", same_camera_weights, top_torso_cross),
    ]

    candidates: list[dict[str, object]] = []
    for weight_name, same_weights, cross_weights in weight_sets:
        for match_threshold in (0.68, 0.70, 0.72, 0.74, 0.76, 0.78):
            for ambiguous_threshold in (0.20, 0.25, 0.30, 0.40, 0.50, 0.55, 0.60, 0.65):
                if ambiguous_threshold >= match_threshold:
                    continue
                rescored = rescore_rows(
                    rows,
                    same_camera_weights=same_weights,
                    cross_camera_weights=cross_weights,
                    match_threshold=match_threshold,
                    ambiguous_threshold=ambiguous_threshold,
                    min_available_weight=float(report["min_available_weight"]),
                    allow_provisional=bool(report["allow_provisional"]),
                )
                summary = summarize_rows(rescored)
                status_counts = summary["evaluation_status"]
                outcome_counts = summary["outcomes"]
                candidates.append(
                    {
                        "weight_set": weight_name,
                        "match_threshold": match_threshold,
                        "ambiguous_threshold": ambiguous_threshold,
                        "correct": status_counts.get("correct", 0),
                        "incorrect": status_counts.get("incorrect", 0),
                        "uncertain": status_counts.get("uncertain", 0),
                        "low_confidence": outcome_counts.get("low_confidence", 0),
                        "ambiguous": outcome_counts.get("ambiguous", 0),
                        "matched": outcome_counts.get("matched", 0),
                        "no_match": outcome_counts.get("no_match", 0),
                    }
                )

    candidates.sort(
        key=lambda candidate: (
            int(candidate["incorrect"]),
            -int(candidate["correct"]),
            int(candidate["low_confidence"]),
            int(candidate["uncertain"]),
        )
    )
    zero_incorrect = [candidate for candidate in candidates if int(candidate["incorrect"]) == 0]
    return (zero_incorrect or candidates)[:8]


def write_calibration_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidates = build_calibration_candidates(report)
    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Clip Match Calibration Report\n\n")
        fh.write("This report uses the current labeled clips as a development set. ")
        fh.write("It is for tuning the evaluator, not proof of generalization.\n\n")
        fh.write("## Selected Runtime Settings\n\n")
        fh.write(f"- Match threshold: `{report.get('match_threshold')}`\n")
        fh.write(f"- Ambiguous threshold: `{report.get('ambiguous_threshold')}`\n")
        fh.write(f"- Minimum available weight: `{report.get('min_available_weight')}`\n")
        fh.write(f"- Same-camera weights: `{report.get('same_camera_weights')}`\n")
        fh.write(f"- Cross-camera weights: `{report.get('cross_camera_weights')}`\n\n")
        fh.write("## Best Zero-Incorrect Candidates\n\n")
        fh.write("| weight_set | match | ambiguous | correct | incorrect | uncertain | low_confidence | matched | no_match |\n")
        fh.write("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n")
        for candidate in candidates:
            fh.write(
                f"| {candidate['weight_set']} | {candidate['match_threshold']} | "
                f"{candidate['ambiguous_threshold']} | {candidate['correct']} | "
                f"{candidate['incorrect']} | {candidate['uncertain']} | "
                f"{candidate['low_confidence']} | {candidate['matched']} | {candidate['no_match']} |\n"
            )
        fh.write("\n## Tuning Direction\n\n")
        fh.write("- Keep `incorrect=0` as the first constraint.\n")
        fh.write("- Prefer candidates that reduce `low_confidence` without turning hard negatives into `matched`.\n")
        fh.write("- Cross-camera brightness remains a weak feature because camera exposure shifts are visible in the current clips.\n")


def write_markdown_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = report["results"]
    assert isinstance(rows, list)
    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Clip Match Evaluation Report\n\n")
        fh.write(f"- Clips manifest: `{report['clips_path']}`\n")
        fh.write(f"- Pair labels: `{report['pairs_path']}`\n")
        fh.write(f"- Evaluated pairs: `{len(rows)}`\n\n")
        summary = summarize_rows(rows)
        outcome_counts = summary["outcomes"]
        status_counts = summary["evaluation_status"]
        fh.write("## Summary\n\n")
        fh.write(f"- Outcomes: `{outcome_counts}`\n")
        fh.write(f"- Evaluation status: `{status_counts}`\n")
        fh.write(f"- Same-camera weights: `{report.get('same_camera_weights', {})}`\n")
        fh.write(f"- Cross-camera weights: `{report.get('cross_camera_weights', {})}`\n\n")
        fh.write(f"- Match threshold: `{report.get('match_threshold')}`\n")
        fh.write(f"- Ambiguous threshold: `{report.get('ambiguous_threshold')}`\n")
        fh.write(f"- Minimum available weight: `{report.get('min_available_weight')}`\n")
        fh.write(f"- Allow provisional profiles: `{report.get('allow_provisional')}`\n\n")
        fh.write("| pair_id | label | mode | outcome | score | available_weight | status | clip_a | clip_b |\n")
        fh.write("| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |\n")
        for row in rows:
            fh.write(
                f"| {row['pair_id']} | {row['label']} | {row.get('pair_mode')} | "
                f"{row['outcome']} | {row['matching_score']} | {row.get('available_weight')} | "
                f"{row['evaluation_status']} | "
                f"{row['clip_id_a']} | {row['clip_id_b']} |\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate labeled local clip pairs.")
    parser.add_argument("--clips", default="data/labels/clips.csv")
    parser.add_argument("--pairs", default="data/labels/pair_labels.csv")
    parser.add_argument("--output-json", default="logs/clip_eval/results.json")
    parser.add_argument("--output-md", default="docs/reports/CLIP_MATCH_EVAL_REPORT.md")
    parser.add_argument("--calibration-md", default="docs/reports/CLIP_MATCH_CALIBRATION_REPORT.md")
    parser.add_argument("--max-frames", type=int, default=150)
    parser.add_argument("--sample-every", type=int, default=1)
    parser.add_argument("--vote-frame-window", type=int, default=75)
    parser.add_argument("--match-threshold", type=float, default=0.72)
    parser.add_argument("--ambiguous-threshold", type=float, default=0.25)
    parser.add_argument("--min-available-weight", type=float, default=2.8)
    parser.add_argument("--weights", default="")
    parser.add_argument("--same-camera-weights", default="")
    parser.add_argument("--cross-camera-weights", default="")
    parser.add_argument("--allow-provisional", action="store_true")
    args = parser.parse_args()

    json_path = resolve_inside_project(args.output_json)
    md_path = resolve_inside_project(args.output_md)
    calibration_path = resolve_inside_project(args.calibration_md)
    report = evaluate_pairs(args)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown_report(md_path, report)
    write_calibration_report(calibration_path, report)
    print(f"Wrote {project_relative(json_path)}")
    print(f"Wrote {project_relative(md_path)}")
    print(f"Wrote {project_relative(calibration_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
