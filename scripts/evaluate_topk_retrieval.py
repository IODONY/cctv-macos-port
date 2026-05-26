#!/usr/bin/env python3
"""Evaluate labeled local clips as a Top-K retrieval problem."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from evaluate_labeled_clips import (
    PROJECT_ROOT,
    analyze_clip,
    build_weight_sets,
    compare_profiles,
    project_relative,
    resolve_inside_project,
)
from walnut_core import WalnutAnalyzer


OUTCOME_RANK = {
    "matched": 3,
    "ambiguous": 2,
    "no_match": 1,
    "low_confidence": 0,
}


@dataclass(frozen=True)
class RetrievalClip:
    clip_id: str
    dataset_id: str
    identity_id: str
    cam_id: str
    take_id: str
    event_id: str
    clip_path: Path
    layout_type: str = ""
    notes: str = ""


@dataclass(frozen=True)
class QuerySpec:
    query_clip: RetrievalClip
    gallery_clips: list[RetrievalClip]


@dataclass(frozen=True)
class RetrievalCandidate:
    query_id: str
    candidate_id: str
    query_dataset: str
    candidate_dataset: str
    query_identity: str
    candidate_identity: str
    query_cam: str
    candidate_cam: str
    rank: int
    same_identity: bool
    pair_mode: str
    retrieval_score: float
    matching_score: float
    profile_confidence: float
    available_weight: float
    outcome: str
    weighted_components: dict[str, float]
    strong_no_match_reasons: list[str]
    missing_comparison_keys: list[str]
    hard_negative: bool


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def parse_csv_list(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def same_identity(left: RetrievalClip, right: RetrievalClip) -> bool:
    return left.dataset_id == right.dataset_id and left.identity_id == right.identity_id


def identity_key(clip: RetrievalClip) -> tuple[str, str]:
    return clip.dataset_id, clip.identity_id


def load_retrieval_clips(path: Path) -> dict[str, RetrievalClip]:
    clips: dict[str, RetrievalClip] = {}
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        required = {"clip_id", "identity_id", "cam_id", "take_id", "clip_path", "notes"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing clips.csv columns: {sorted(missing)}")
        for row in reader:
            clip_path = resolve_inside_project(row["clip_path"])
            if not clip_path.is_file():
                raise FileNotFoundError(f"Clip does not exist: {clip_path}")
            clip_id = row["clip_id"]
            if clip_id in clips:
                raise ValueError(f"Duplicate clip_id in manifest: {clip_id}")
            clips[clip_id] = RetrievalClip(
                clip_id=clip_id,
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


def build_query_specs(clips: dict[str, RetrievalClip], args: argparse.Namespace) -> list[QuerySpec]:
    dataset_filter = args.dataset.strip() if args.dataset else ""
    query_cams = parse_csv_list(args.query_cams)
    gallery_cams = parse_csv_list(args.gallery_cams)

    eligible = [
        clip
        for clip in clips.values()
        if not dataset_filter or clip.dataset_id == dataset_filter
    ]
    if not eligible:
        raise ValueError(f"No clips match dataset filter: {dataset_filter}")

    if query_cams:
        queries = [clip for clip in eligible if clip.cam_id in query_cams]
    else:
        queries = list(eligible)
    if not queries:
        raise ValueError(f"No query clips match query camera filter: {sorted(query_cams)}")

    specs = []
    for query_clip in queries:
        gallery = []
        for candidate in eligible:
            if candidate.clip_id == query_clip.clip_id:
                continue
            if query_cams and not gallery_cams and candidate.cam_id in query_cams:
                continue
            if gallery_cams and candidate.cam_id not in gallery_cams:
                continue
            gallery.append(candidate)
        specs.append(QuerySpec(query_clip=query_clip, gallery_clips=gallery))
    return specs


def analysis_confidence(analysis: dict[str, object]) -> float:
    evidence = analysis.get("evidence")
    if not isinstance(evidence, dict):
        return 0.0

    field_confidence = evidence.get("field_confidence")
    if not isinstance(field_confidence, dict):
        field_score = 0.0
    else:
        values = []
        for value in field_confidence.values():
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue
        field_score = sum(values) / len(values) if values else 0.0

    try:
        sample_count = float(evidence.get("sample_count") or 0.0)
    except (TypeError, ValueError):
        sample_count = 0.0
    sample_score = min(1.0, sample_count / 75.0)
    return round(clamp((field_score * 0.7) + (sample_score * 0.3)), 4)


def retrieval_score(
    comparison: dict[str, object],
    query_analysis: dict[str, object],
    candidate_analysis: dict[str, object],
    total_available_weight: float,
) -> float:
    matching_score = float(comparison.get("matching_score") or 0.0)
    available_weight = float(comparison.get("available_weight") or 0.0)
    available_fraction = available_weight / total_available_weight if total_available_weight > 0.0 else 0.0
    confidence = min(analysis_confidence(query_analysis), analysis_confidence(candidate_analysis))
    outcome = str(comparison.get("outcome") or "low_confidence")
    outcome_bonus = {
        "matched": 0.12,
        "ambiguous": 0.04,
        "no_match": -0.08,
        "low_confidence": -0.18,
    }.get(outcome, -0.18)
    strong_reasons = comparison.get("strong_no_match_reasons")
    strong_penalty = min(0.24, 0.12 * len(strong_reasons if isinstance(strong_reasons, list) else []))
    return round(
        clamp(
            (matching_score * 0.76)
            + (confidence * 0.12)
            + (available_fraction * 0.12)
            + outcome_bonus
            - strong_penalty
        ),
        4,
    )


def score_candidate(
    args: argparse.Namespace,
    query_clip: RetrievalClip,
    candidate_clip: RetrievalClip,
    query_analysis: dict[str, object],
    candidate_analysis: dict[str, object],
    same_camera_weights: dict[str, float],
    cross_camera_weights: dict[str, float],
) -> dict[str, object]:
    pair_mode = "same_camera" if query_clip.cam_id == candidate_clip.cam_id else "cross_camera"
    weights = same_camera_weights if pair_mode == "same_camera" else cross_camera_weights
    comparison = compare_profiles(
        query_analysis.get("profile"),
        candidate_analysis.get("profile"),
        match_threshold=args.match_threshold,
        ambiguous_threshold=args.ambiguous_threshold,
        weights=weights,
        allow_provisional=args.allow_provisional,
        left_status=str(query_analysis.get("profile_status") or "missing"),
        right_status=str(candidate_analysis.get("profile_status") or "missing"),
        pair_mode=pair_mode,
        min_available_weight=args.min_available_weight,
    )
    total_available_weight = sum(max(0.0, float(value)) for value in weights.values())
    score = retrieval_score(comparison, query_analysis, candidate_analysis, total_available_weight)
    strong_reasons = comparison.get("strong_no_match_reasons")
    if not isinstance(strong_reasons, list):
        strong_reasons = []
    missing_keys = comparison.get("missing_comparison_keys")
    if not isinstance(missing_keys, list):
        missing_keys = []
    components = comparison.get("weighted_components")
    if not isinstance(components, dict):
        components = {}
    is_same_identity = same_identity(query_clip, candidate_clip)
    hard_negative = not is_same_identity and query_clip.cam_id == candidate_clip.cam_id

    return {
        "query_id": query_clip.clip_id,
        "candidate_id": candidate_clip.clip_id,
        "query_dataset": query_clip.dataset_id,
        "candidate_dataset": candidate_clip.dataset_id,
        "query_identity": query_clip.identity_id,
        "candidate_identity": candidate_clip.identity_id,
        "query_cam": query_clip.cam_id,
        "candidate_cam": candidate_clip.cam_id,
        "candidate_clip_path": project_relative(candidate_clip.clip_path),
        "same_identity": is_same_identity,
        "pair_mode": pair_mode,
        "retrieval_score": score,
        "matching_score": float(comparison.get("matching_score") or 0.0),
        "profile_confidence": min(analysis_confidence(query_analysis), analysis_confidence(candidate_analysis)),
        "available_weight": float(comparison.get("available_weight") or 0.0),
        "outcome": str(comparison.get("outcome") or "low_confidence"),
        "weighted_components": components,
        "strong_no_match_reasons": strong_reasons,
        "missing_comparison_keys": missing_keys,
        "hard_negative": hard_negative,
    }


def rank_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    ranked = sorted(
        candidates,
        key=lambda row: (
            float(row["retrieval_score"]),
            OUTCOME_RANK.get(str(row["outcome"]), 0),
            float(row["matching_score"]),
            float(row["profile_confidence"]),
            -len(row["strong_no_match_reasons"]),
            str(row["candidate_id"]),
        ),
        reverse=True,
    )
    for index, candidate in enumerate(ranked, start=1):
        candidate["rank"] = index
    return ranked


def output_readiness(k: int, own_at_k: int, wrong_at_k: int, insufficient_gallery: bool, insufficient_same: bool) -> str:
    if insufficient_gallery:
        return "insufficient_gallery"
    if insufficient_same:
        return "insufficient_same_identity_gallery"
    if own_at_k <= 2:
        return "failed_low_own_count"
    if wrong_at_k <= 2:
        return "ready"
    if own_at_k >= ((k // 2) + 1):
        return "partial_majority_own"
    return "needs_ranking_improvement"


def topk_metrics(query_clip: RetrievalClip, ranked: list[dict[str, object]], k: int, pool_k: int) -> dict[str, object]:
    top_k = ranked[:k]
    top_pool = ranked[:pool_k]
    returned_at_k = len(top_k)
    returned_at_pool = len(top_pool)
    available_positive_count = sum(1 for row in ranked if row["same_identity"])
    max_possible_own = min(k, available_positive_count)
    own_at_k = sum(1 for row in top_k if row["same_identity"])
    own_at_pool = sum(1 for row in top_pool if row["same_identity"])
    wrong_at_k = returned_at_k - own_at_k
    wrong_at_pool = returned_at_pool - own_at_pool
    ambiguous_at_k = sum(1 for row in top_k if row["outcome"] == "ambiguous")
    false_match_at_k = sum(1 for row in top_k if row["outcome"] == "matched" and not row["same_identity"])
    hard_negative_at_k = sum(1 for row in top_k if row["hard_negative"])
    insufficient_gallery = len(ranked) < k
    insufficient_same = available_positive_count < k

    kth_score = float(top_k[-1]["retrieval_score"]) if top_k else 0.0
    next_score = float(ranked[k]["retrieval_score"]) if len(ranked) > k else None
    first_wrong_high_risk = next(
        (
            row
            for row in ranked
            if not row["same_identity"] and (row["outcome"] == "matched" or row["hard_negative"])
        ),
        None,
    )
    wrong_margin = (
        round(kth_score - float(first_wrong_high_risk["retrieval_score"]), 4)
        if first_wrong_high_risk is not None
        else None
    )

    readiness = output_readiness(k, own_at_k, wrong_at_k, insufficient_gallery, insufficient_same)
    return {
        "query_dataset": query_clip.dataset_id,
        "query_identity": query_clip.identity_id,
        "query_cam": query_clip.cam_id,
        "gallery_count": len(ranked),
        "available_positive_count": available_positive_count,
        "positives_available": available_positive_count,
        f"max_possible_own_count_at_{k}": max_possible_own,
        f"returned_at_{k}": returned_at_k,
        f"topk_output_count_at_{k}": returned_at_k,
        f"own_at_{k}": own_at_k,
        f"wrong_at_{k}": wrong_at_k,
        f"recall_at_{k}": round(own_at_k / available_positive_count, 4) if available_positive_count else 0.0,
        f"normalized_own_recall_at_{k}": round(own_at_k / max_possible_own, 4) if max_possible_own else 0.0,
        f"precision_at_{k}": round(own_at_k / returned_at_k, 4) if returned_at_k else 0.0,
        f"returned_at_{pool_k}": returned_at_pool,
        f"own_at_{pool_k}": own_at_pool,
        f"wrong_at_{pool_k}": wrong_at_pool,
        f"recall_at_{pool_k}": round(own_at_pool / available_positive_count, 4) if available_positive_count else 0.0,
        f"precision_at_{pool_k}": round(own_at_pool / returned_at_pool, 4) if returned_at_pool else 0.0,
        f"ambiguous_rate_at_{k}": round(ambiguous_at_k / returned_at_k, 4) if returned_at_k else 0.0,
        f"false_match_rate_at_{k}": round(false_match_at_k / returned_at_k, 4) if returned_at_k else 0.0,
        f"hard_negative_rate_at_{k}": round(hard_negative_at_k / returned_at_k, 4) if returned_at_k else 0.0,
        "insufficient_gallery": insufficient_gallery,
        "insufficient_same_identity_gallery": insufficient_same,
        "output_readiness": readiness,
        "rank_k_margin": round(kth_score - next_score, 4) if next_score is not None else None,
        "rank_k_margin_to_first_wrong_high_risk": wrong_margin,
    }


def micro_rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def summarize_group(rows: list[dict[str, object]], k: int, pool_k: int) -> dict[str, object]:
    query_count = len(rows)
    total_returned_at_k = sum(int(row["metrics"][f"returned_at_{k}"]) for row in rows)
    total_own_at_k = sum(int(row["metrics"][f"own_at_{k}"]) for row in rows)
    total_wrong_at_k = sum(int(row["metrics"][f"wrong_at_{k}"]) for row in rows)
    total_available = sum(int(row["metrics"]["available_positive_count"]) for row in rows)
    total_max_possible = sum(int(row["metrics"][f"max_possible_own_count_at_{k}"]) for row in rows)
    max_available_for_any_query = max((int(row["metrics"]["available_positive_count"]) for row in rows), default=0)
    total_returned_at_pool = sum(int(row["metrics"][f"returned_at_{pool_k}"]) for row in rows)
    total_own_at_pool = sum(int(row["metrics"][f"own_at_{pool_k}"]) for row in rows)
    total_wrong_at_pool = sum(int(row["metrics"][f"wrong_at_{pool_k}"]) for row in rows)
    own_values = [int(row["metrics"][f"own_at_{k}"]) for row in rows]
    majority_target = (k // 2) + 1
    readiness_counts = Counter(str(row["metrics"]["output_readiness"]) for row in rows)

    metric_keys = [
        f"topk_output_count_at_{k}",
        f"own_at_{k}",
        f"wrong_at_{k}",
        f"recall_at_{k}",
        f"normalized_own_recall_at_{k}",
        f"precision_at_{k}",
        f"own_at_{pool_k}",
        f"wrong_at_{pool_k}",
        f"recall_at_{pool_k}",
        f"precision_at_{pool_k}",
        f"ambiguous_rate_at_{k}",
        f"false_match_rate_at_{k}",
        f"hard_negative_rate_at_{k}",
    ]
    means = {}
    for key in metric_keys:
        values = [float(row["metrics"][key]) for row in rows]
        means[f"mean_{key}"] = round(sum(values) / len(values), 4) if values else 0.0

    return {
        **means,
        "query_count": query_count,
        "total_available_positive_count": total_available,
        "max_available_positive_count_for_any_query": max_available_for_any_query,
        f"additional_gallery_clips_needed_for_top_{k}_own": max(0, k - max_available_for_any_query),
        f"total_max_possible_own_count_at_{k}": total_max_possible,
        f"total_returned_at_{k}": total_returned_at_k,
        f"total_own_at_{k}": total_own_at_k,
        f"total_wrong_at_{k}": total_wrong_at_k,
        f"micro_recall_at_{k}": micro_rate(total_own_at_k, total_available),
        f"micro_normalized_own_recall_at_{k}": micro_rate(total_own_at_k, total_max_possible),
        f"micro_precision_at_{k}": micro_rate(total_own_at_k, total_returned_at_k),
        f"total_returned_at_{pool_k}": total_returned_at_pool,
        f"total_own_at_{pool_k}": total_own_at_pool,
        f"total_wrong_at_{pool_k}": total_wrong_at_pool,
        f"micro_recall_at_{pool_k}": micro_rate(total_own_at_pool, total_available),
        f"micro_precision_at_{pool_k}": micro_rate(total_own_at_pool, total_returned_at_pool),
        f"min_own_at_{k}": min(own_values) if own_values else 0,
        f"max_own_at_{k}": max(own_values) if own_values else 0,
        f"queries_with_majority_own_at_{k}": sum(1 for value in own_values if value >= majority_target),
        "queries_with_insufficient_gallery": sum(1 for row in rows if row["metrics"]["insufficient_gallery"]),
        "queries_with_insufficient_same_identity_gallery": sum(
            1 for row in rows if row["metrics"]["insufficient_same_identity_gallery"]
        ),
        "output_readiness_counts": dict(sorted(readiness_counts.items())),
    }


def summarize_queries(query_results: list[dict[str, object]], k: int, pool_k: int) -> dict[str, object]:
    if not query_results:
        return {}
    return summarize_group(query_results, k, pool_k)


def summarize_identities(query_results: list[dict[str, object]], k: int, pool_k: int) -> list[dict[str, object]]:
    by_identity: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in query_results:
        by_identity.setdefault((str(row["dataset_id"]), str(row["identity_id"])), []).append(row)

    summaries = []
    for (dataset_id, identity_id), rows in sorted(by_identity.items()):
        summaries.append(
            {
                "dataset_id": dataset_id,
                "identity_id": identity_id,
                **summarize_group(rows, k, pool_k),
            }
        )
    return summaries


def summarize_datasets(query_results: list[dict[str, object]], k: int, pool_k: int) -> list[dict[str, object]]:
    by_dataset: dict[str, list[dict[str, object]]] = {}
    for row in query_results:
        by_dataset.setdefault(str(row["dataset_id"]), []).append(row)

    summaries = []
    for dataset_id, rows in sorted(by_dataset.items()):
        summaries.append({"dataset_id": dataset_id, **summarize_group(rows, k, pool_k)})
    return summaries


def summarize_camera_pairs(query_results: list[dict[str, object]], k: int) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in query_results:
        for candidate in row["top_k"]:
            groups.setdefault((str(candidate["query_cam"]), str(candidate["candidate_cam"])), []).append(candidate)

    summaries = []
    for (query_cam, candidate_cam), rows in sorted(groups.items()):
        count = len(rows)
        own = sum(1 for row in rows if row["same_identity"])
        wrong = count - own
        mean_score = round(sum(float(row["retrieval_score"]) for row in rows) / count, 4) if count else 0.0
        outcomes = Counter(str(row["outcome"]) for row in rows)
        summaries.append(
            {
                "query_cam": query_cam,
                "candidate_cam": candidate_cam,
                "topk_candidate_count": count,
                "own_count": own,
                "wrong_count": wrong,
                "precision": micro_rate(own, count),
                "mean_score": mean_score,
                "outcomes": dict(sorted(outcomes.items())),
            }
        )
    return summaries


def evaluate_retrieval(args: argparse.Namespace) -> dict[str, object]:
    clips = load_retrieval_clips(resolve_inside_project(args.clips))
    same_camera_weights, cross_camera_weights = build_weight_sets(args)
    specs = build_query_specs(clips, args)
    analyzer = WalnutAnalyzer(vote_frame_window=args.vote_frame_window)

    clips_to_analyze: dict[str, RetrievalClip] = {}
    for spec in specs:
        clips_to_analyze[spec.query_clip.clip_id] = spec.query_clip
        for candidate in spec.gallery_clips:
            clips_to_analyze[candidate.clip_id] = candidate

    profile_cache = {}
    for clip_id, clip in clips_to_analyze.items():
        profile_cache[clip_id] = analyze_clip(
            analyzer,
            clip,
            max_frames=args.max_frames,
            sample_every=args.sample_every,
        )

    query_results = []
    unique_gallery_ids = set()
    for spec in specs:
        query_clip = spec.query_clip
        candidates = []
        query_analysis = profile_cache[query_clip.clip_id]
        for candidate_clip in spec.gallery_clips:
            unique_gallery_ids.add(candidate_clip.clip_id)
            candidate_analysis = profile_cache[candidate_clip.clip_id]
            candidates.append(
                score_candidate(
                    args,
                    query_clip,
                    candidate_clip,
                    query_analysis,
                    candidate_analysis,
                    same_camera_weights,
                    cross_camera_weights,
                )
            )
        ranked = rank_candidates(candidates)
        metrics = topk_metrics(query_clip, ranked, args.k, args.candidate_pool)
        query_results.append(
            {
                "query_id": query_clip.clip_id,
                "dataset_id": query_clip.dataset_id,
                "identity_id": query_clip.identity_id,
                "cam_id": query_clip.cam_id,
                "take_id": query_clip.take_id,
                "event_id": query_clip.event_id,
                "clip_path": project_relative(query_clip.clip_path),
                "analysis": query_analysis,
                "metrics": metrics,
                "top_k": ranked[: args.k],
                "candidate_pool": ranked[: args.candidate_pool],
            }
        )

    query_cams = sorted(parse_csv_list(args.query_cams))
    gallery_cams = sorted(parse_csv_list(args.gallery_cams))
    evaluation_mode = "camera_split" if query_cams else "leave_one_out"
    summary = summarize_queries(query_results, args.k, args.candidate_pool)
    return {
        "clips_path": args.clips,
        "dataset_filter": args.dataset or "",
        "query_cams": query_cams,
        "gallery_cams": gallery_cams,
        "evaluation_mode": evaluation_mode,
        "eligible_clip_count": len({clip_id for clip_id in clips_to_analyze}),
        "query_count": len(query_results),
        "gallery_count": len(unique_gallery_ids),
        "k": args.k,
        "candidate_pool": args.candidate_pool,
        "match_threshold": args.match_threshold,
        "ambiguous_threshold": args.ambiguous_threshold,
        "min_available_weight": args.min_available_weight,
        "same_camera_weights": same_camera_weights,
        "cross_camera_weights": cross_camera_weights,
        "summary": summary,
        "identity_summary": summarize_identities(query_results, args.k, args.candidate_pool),
        "dataset_summary": summarize_datasets(query_results, args.k, args.candidate_pool),
        "camera_pair_summary": summarize_camera_pairs(query_results, args.k),
        "queries": query_results,
    }


def format_readiness_counts(counts: dict[str, object]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"


def write_eval_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    k = int(report["k"])
    pool_k = int(report["candidate_pool"])
    summary = report["summary"]
    identity_summary = report["identity_summary"]
    dataset_summary = report["dataset_summary"]
    camera_pair_summary = report["camera_pair_summary"]
    queries = report["queries"]
    assert isinstance(summary, dict)
    assert isinstance(identity_summary, list)
    assert isinstance(dataset_summary, list)
    assert isinstance(camera_pair_summary, list)
    assert isinstance(queries, list)

    dataset_filter = report["dataset_filter"] or "all"
    query_cams = ", ".join(report["query_cams"]) if report["query_cams"] else "all"
    gallery_cams = ", ".join(report["gallery_cams"]) if report["gallery_cams"] else "all eligible"

    with path.open("w", encoding="utf-8") as fh:
        fh.write("# YOLO-ReID Top-K Retrieval Evaluation Report\n\n")
        fh.write(
            "This evaluates labeled clips by ranking gallery clips for each query and checking whether "
            f"the final Top-{k} output is usable for display.\n\n"
        )
        fh.write(f"- Clips manifest: `{report['clips_path']}`\n")
        fh.write(f"- Dataset filter: `{dataset_filter}`\n")
        fh.write(f"- Evaluation mode: `{report['evaluation_mode']}`\n")
        fh.write(f"- Query cameras: `{query_cams}`\n")
        fh.write(f"- Gallery cameras: `{gallery_cams}`\n")
        fh.write(f"- Query count: `{report['query_count']}`\n")
        fh.write(f"- Gallery count: `{report['gallery_count']}`\n")
        fh.write(f"- K: `{k}`\n")
        fh.write(f"- Candidate pool: `{pool_k}`\n")
        fh.write(f"- Match threshold: `{report['match_threshold']}`\n")
        fh.write(f"- Ambiguous threshold: `{report['ambiguous_threshold']}`\n\n")

        fh.write("## Headline\n\n")
        fh.write(f"- `Recall@{k}` macro/query mean: `{summary[f'mean_recall_at_{k}']}`\n")
        fh.write(
            f"- `Recall@{k}` micro/positive-weighted: `{summary[f'micro_recall_at_{k}']}` "
            f"({summary[f'total_own_at_{k}']}/{summary['total_available_positive_count']})\n"
        )
        fh.write(
            f"- `Normalized OwnRecall@{k}` micro: `{summary[f'micro_normalized_own_recall_at_{k}']}` "
            f"({summary[f'total_own_at_{k}']}/{summary[f'total_max_possible_own_count_at_{k}']})\n"
        )
        fh.write(f"- `Precision@{k}` macro/query mean: `{summary[f'mean_precision_at_{k}']}`\n")
        fh.write(f"- `OwnCount@{k}` mean: `{summary[f'mean_own_at_{k}']}`\n")
        fh.write(f"- `Wrong@{k}` mean: `{summary[f'mean_wrong_at_{k}']}`\n")
        fh.write(f"- `TopK output count` mean: `{summary[f'mean_topk_output_count_at_{k}']}`\n")
        fh.write(
            f"- Insufficient same-identity gallery queries: "
            f"`{summary['queries_with_insufficient_same_identity_gallery']}`\n"
        )
        fh.write(f"- Output readiness counts: `{format_readiness_counts(summary['output_readiness_counts'])}`\n\n")

        fh.write("## Summary Metrics\n\n")
        for key in sorted(summary):
            fh.write(f"- `{key}`: `{summary[key]}`\n")

        fh.write("\n## Dataset Breakdown\n\n")
        fh.write(
            f"| dataset | queries | OwnCount@{k} total | Wrong@{k} total | "
            f"Recall@{k} micro | Normalized OwnRecall@{k} micro | Precision@{k} micro | readiness |\n"
        )
        fh.write("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |\n")
        for row in dataset_summary:
            fh.write(
                f"| {row['dataset_id']} | {row['query_count']} | {row[f'total_own_at_{k}']} | "
                f"{row[f'total_wrong_at_{k}']} | {row[f'micro_recall_at_{k}']} | "
                f"{row[f'micro_normalized_own_recall_at_{k}']} | {row[f'micro_precision_at_{k}']} | "
                f"{format_readiness_counts(row['output_readiness_counts'])} |\n"
            )

        fh.write("\n## Identity Breakdown\n\n")
        fh.write(
            f"| dataset | identity | queries | available positives | max possible own@{k} | "
            f"additional clips needed | OwnCount@{k} total | Wrong@{k} total | Recall@{k} micro | "
            f"Normalized OwnRecall@{k} micro | own@{k} min-max | readiness |\n"
        )
        fh.write("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |\n")
        for row in identity_summary:
            fh.write(
                f"| {row['dataset_id']} | {row['identity_id']} | {row['query_count']} | "
                f"{row['total_available_positive_count']} | {row[f'total_max_possible_own_count_at_{k}']} | "
                f"{row[f'additional_gallery_clips_needed_for_top_{k}_own']} | "
                f"{row[f'total_own_at_{k}']} | {row[f'total_wrong_at_{k}']} | "
                f"{row[f'micro_recall_at_{k}']} | {row[f'micro_normalized_own_recall_at_{k}']} | "
                f"{row[f'min_own_at_{k}']}-{row[f'max_own_at_{k}']} | "
                f"{format_readiness_counts(row['output_readiness_counts'])} |\n"
            )

        fh.write("\n## Additional Clips Needed\n\n")
        fh.write(
            f"`additional clips needed` is the minimum extra same-identity gallery clips needed so a query can "
            f"theoretically return {k} own clips. This is a dataset coverage limit, not a live identity field.\n"
        )

        fh.write("\n## Camera Pair Breakdown\n\n")
        fh.write("| query_cam | candidate_cam | top-k candidates | own | wrong | precision | mean_score | outcomes |\n")
        fh.write("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |\n")
        for row in camera_pair_summary:
            fh.write(
                f"| {row['query_cam']} | {row['candidate_cam']} | {row['topk_candidate_count']} | "
                f"{row['own_count']} | {row['wrong_count']} | {row['precision']} | "
                f"{row['mean_score']} | {format_readiness_counts(row['outcomes'])} |\n"
            )

        fh.write("\n## Per Query Top-K\n\n")
        fh.write(
            f"| query | dataset | identity | cam | gallery | available_positive_count | "
            f"max_possible_own_count_at_{k} | output_count | OwnCount@{k} | Wrong@{k} | "
            f"Precision@{k} | Recall@{k} | Normalized OwnRecall@{k} | insufficient_same_identity_gallery | "
            "readiness | top candidates |\n"
        )
        fh.write("| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |\n")
        for row in queries:
            metrics = row["metrics"]
            top_candidates = ", ".join(
                f"{candidate['candidate_id']}:{candidate['outcome']}:{candidate['retrieval_score']}"
                for candidate in row["top_k"]
            )
            fh.write(
                f"| {row['query_id']} | {row['dataset_id']} | {row['identity_id']} | {row['cam_id']} | "
                f"{metrics['gallery_count']} | {metrics['available_positive_count']} | "
                f"{metrics[f'max_possible_own_count_at_{k}']} | {metrics[f'topk_output_count_at_{k}']} | "
                f"{metrics[f'own_at_{k}']} | {metrics[f'wrong_at_{k}']} | "
                f"{metrics[f'precision_at_{k}']} | {metrics[f'recall_at_{k}']} | "
                f"{metrics[f'normalized_own_recall_at_{k}']} | "
                f"{metrics['insufficient_same_identity_gallery']} | {metrics['output_readiness']} | "
                f"{top_candidates} |\n"
            )


def write_debug_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    k = int(report["k"])
    queries = report["queries"]
    assert isinstance(queries, list)
    worst = sorted(
        queries,
        key=lambda row: (
            str(row["metrics"]["output_readiness"]) == "insufficient_same_identity_gallery",
            int(row["metrics"][f"own_at_{k}"]),
            -int(row["metrics"][f"wrong_at_{k}"]),
            str(row["query_id"]),
        ),
    )[:10]

    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Top-K Retrieval Debug Report\n\n")
        fh.write(
            "This report inspects retrieval failures and high-risk candidates without running cameras, "
            "RTSP, TouchDesigner, or full tracking.\n\n"
        )
        fh.write("## Worst Queries\n\n")
        fh.write(
            f"| query | dataset | identity | own@{k} | wrong@{k} | max_possible_own@{k} | "
            f"normalized_own_recall@{k} | readiness | top wrong candidates |\n"
        )
        fh.write("| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |\n")
        for row in worst:
            metrics = row["metrics"]
            wrong_candidates = [
                candidate
                for candidate in row["top_k"]
                if not candidate["same_identity"]
            ]
            wrong_text = ", ".join(
                f"{candidate['candidate_id']}:{candidate['outcome']}:{candidate['retrieval_score']}"
                for candidate in wrong_candidates[:5]
            )
            fh.write(
                f"| {row['query_id']} | {row['dataset_id']} | {row['identity_id']} | "
                f"{metrics[f'own_at_{k}']} | {metrics[f'wrong_at_{k}']} | "
                f"{metrics[f'max_possible_own_count_at_{k}']} | "
                f"{metrics[f'normalized_own_recall_at_{k}']} | {metrics['output_readiness']} | "
                f"{wrong_text} |\n"
            )

        fh.write("\n## Hard Negatives In Top-K\n\n")
        fh.write("| query | candidate | rank | score | outcome | reasons |\n")
        fh.write("| --- | --- | ---: | ---: | --- | --- |\n")
        for row in queries:
            for candidate in row["top_k"]:
                if not candidate["hard_negative"]:
                    continue
                reasons = ",".join(candidate["strong_no_match_reasons"])
                fh.write(
                    f"| {row['query_id']} | {candidate['candidate_id']} | {candidate['rank']} | "
                    f"{candidate['retrieval_score']} | {candidate['outcome']} | {reasons} |\n"
                )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate labeled local clips as Top-K retrieval.")
    parser.add_argument("--clips", default="data/labels/clips.csv")
    parser.add_argument("--output-json", default="logs/topk_retrieval/results.json")
    parser.add_argument("--output-md", default="docs/reports/TOPK_RETRIEVAL_EVAL_REPORT.md")
    parser.add_argument("--debug-md", default="docs/reports/TOPK_RETRIEVAL_DEBUG_REPORT.md")
    parser.add_argument("--dataset-output-md", default="docs/reports/TEST_CLIP_0527_EVAL_REPORT.md")
    parser.add_argument("--k", type=int, default=9)
    parser.add_argument("--candidate-pool", type=int, default=12)
    parser.add_argument("--dataset", default="")
    parser.add_argument("--query-cams", default="")
    parser.add_argument("--gallery-cams", default="")
    parser.add_argument("--leave-one-out", action="store_true", default=True)
    parser.add_argument("--max-frames", type=int, default=150)
    parser.add_argument("--sample-every", type=int, default=1)
    parser.add_argument("--vote-frame-window", type=int, default=75)
    parser.add_argument("--match-threshold", type=float, default=0.72)
    parser.add_argument("--ambiguous-threshold", type=float, default=0.25)
    parser.add_argument("--min-available-weight", type=float, default=2.8)
    parser.add_argument("--weights", default="")
    parser.add_argument("--same-camera-weights", default="")
    parser.add_argument("--cross-camera-weights", default="")
    parser.add_argument("--allow-provisional", action="store_true", default=True)
    parser.add_argument("--no-allow-provisional", action="store_false", dest="allow_provisional")
    args = parser.parse_args()

    if args.k < 1:
        raise SystemExit("--k must be at least 1")
    if args.candidate_pool < args.k:
        raise SystemExit("--candidate-pool must be greater than or equal to --k")

    report = evaluate_retrieval(args)
    json_path = resolve_inside_project(args.output_json)
    eval_path = resolve_inside_project(args.output_md)
    debug_path = resolve_inside_project(args.debug_md)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_eval_report(eval_path, report)
    write_debug_report(debug_path, report)

    print(f"Wrote {project_relative(json_path)}")
    print(f"Wrote {project_relative(eval_path)}")
    print(f"Wrote {project_relative(debug_path)}")
    if args.dataset == "test_clip_0527" and not args.query_cams:
        dataset_path = resolve_inside_project(args.dataset_output_md)
        write_eval_report(dataset_path, report)
        print(f"Wrote {project_relative(dataset_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
