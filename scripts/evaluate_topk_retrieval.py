#!/usr/bin/env python3
"""Evaluate labeled local clips as a Top-K retrieval problem."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from evaluate_labeled_clips import (
    PROJECT_ROOT,
    analyze_clip,
    build_weight_sets,
    compare_profiles,
    load_clips,
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
class RetrievalCandidate:
    query_id: str
    candidate_id: str
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
    query_clip,
    candidate_clip,
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
    hard_negative = query_clip.identity_id != candidate_clip.identity_id and query_clip.cam_id == candidate_clip.cam_id

    return {
        "query_id": query_clip.clip_id,
        "candidate_id": candidate_clip.clip_id,
        "query_identity": query_clip.identity_id,
        "candidate_identity": candidate_clip.identity_id,
        "query_cam": query_clip.cam_id,
        "candidate_cam": candidate_clip.cam_id,
        "same_identity": query_clip.identity_id == candidate_clip.identity_id,
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


def topk_metrics(query_identity: str, ranked: list[dict[str, object]], k: int, pool_k: int) -> dict[str, object]:
    top_k = ranked[:k]
    top_pool = ranked[:pool_k]
    returned_at_k = len(top_k)
    returned_at_pool = len(top_pool)
    positives_available = sum(1 for row in ranked if row["candidate_identity"] == query_identity)
    own_at_k = sum(1 for row in top_k if row["candidate_identity"] == query_identity)
    own_at_pool = sum(1 for row in top_pool if row["candidate_identity"] == query_identity)
    wrong_at_k = len(top_k) - own_at_k
    wrong_at_pool = len(top_pool) - own_at_pool
    ambiguous_at_k = sum(1 for row in top_k if row["outcome"] == "ambiguous")
    false_match_at_k = sum(
        1 for row in top_k if row["outcome"] == "matched" and row["candidate_identity"] != query_identity
    )
    hard_negative_at_k = sum(1 for row in top_k if row["hard_negative"])

    kth_score = float(top_k[-1]["retrieval_score"]) if top_k else 0.0
    next_score = float(ranked[k]["retrieval_score"]) if len(ranked) > k else None
    first_wrong_high_risk = next(
        (
            row
            for row in ranked
            if row["candidate_identity"] != query_identity
            and (row["outcome"] == "matched" or row["hard_negative"])
        ),
        None,
    )
    wrong_margin = (
        round(kth_score - float(first_wrong_high_risk["retrieval_score"]), 4)
        if first_wrong_high_risk is not None
        else None
    )

    return {
        "positives_available": positives_available,
        f"returned_at_{k}": returned_at_k,
        f"own_at_{k}": own_at_k,
        f"wrong_at_{k}": wrong_at_k,
        f"recall_at_{k}": round(own_at_k / positives_available, 4) if positives_available else 0.0,
        f"precision_at_{k}": round(own_at_k / returned_at_k, 4) if returned_at_k else 0.0,
        f"returned_at_{pool_k}": returned_at_pool,
        f"own_at_{pool_k}": own_at_pool,
        f"wrong_at_{pool_k}": wrong_at_pool,
        f"recall_at_{pool_k}": round(own_at_pool / positives_available, 4) if positives_available else 0.0,
        f"precision_at_{pool_k}": round(own_at_pool / returned_at_pool, 4) if returned_at_pool else 0.0,
        f"ambiguous_rate_at_{k}": round(ambiguous_at_k / returned_at_k, 4) if returned_at_k else 0.0,
        f"false_match_rate_at_{k}": round(false_match_at_k / returned_at_k, 4) if returned_at_k else 0.0,
        f"hard_negative_rate_at_{k}": round(hard_negative_at_k / returned_at_k, 4) if returned_at_k else 0.0,
        "rank_k_margin": round(kth_score - next_score, 4) if next_score is not None else None,
        "rank_k_margin_to_first_wrong_high_risk": wrong_margin,
    }


def micro_rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def summarize_queries(query_results: list[dict[str, object]], k: int, pool_k: int) -> dict[str, object]:
    if not query_results:
        return {}

    metric_keys = [
        f"own_at_{k}",
        f"wrong_at_{k}",
        f"recall_at_{k}",
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
        values = [float(row["metrics"][key]) for row in query_results]
        means[f"mean_{key}"] = round(sum(values) / len(values), 4)

    own_values = [int(row["metrics"][f"own_at_{k}"]) for row in query_results]
    majority_target = (k // 2) + 1
    total_positives = sum(int(row["metrics"]["positives_available"]) for row in query_results)
    total_returned_at_k = sum(int(row["metrics"][f"returned_at_{k}"]) for row in query_results)
    total_own_at_k = sum(int(row["metrics"][f"own_at_{k}"]) for row in query_results)
    total_wrong_at_k = sum(int(row["metrics"][f"wrong_at_{k}"]) for row in query_results)
    total_returned_at_pool = sum(int(row["metrics"][f"returned_at_{pool_k}"]) for row in query_results)
    total_own_at_pool = sum(int(row["metrics"][f"own_at_{pool_k}"]) for row in query_results)
    total_wrong_at_pool = sum(int(row["metrics"][f"wrong_at_{pool_k}"]) for row in query_results)
    return {
        **means,
        "total_positives_available": total_positives,
        f"total_returned_at_{k}": total_returned_at_k,
        f"total_own_at_{k}": total_own_at_k,
        f"total_wrong_at_{k}": total_wrong_at_k,
        f"micro_recall_at_{k}": micro_rate(total_own_at_k, total_positives),
        f"micro_precision_at_{k}": micro_rate(total_own_at_k, total_returned_at_k),
        f"total_returned_at_{pool_k}": total_returned_at_pool,
        f"total_own_at_{pool_k}": total_own_at_pool,
        f"total_wrong_at_{pool_k}": total_wrong_at_pool,
        f"micro_recall_at_{pool_k}": micro_rate(total_own_at_pool, total_positives),
        f"micro_precision_at_{pool_k}": micro_rate(total_own_at_pool, total_returned_at_pool),
        f"min_own_at_{k}": min(own_values),
        f"max_own_at_{k}": max(own_values),
        f"queries_with_majority_own_at_{k}": sum(1 for value in own_values if value >= majority_target),
        "query_count": len(query_results),
    }


def summarize_identities(query_results: list[dict[str, object]], k: int) -> list[dict[str, object]]:
    by_identity: dict[str, list[dict[str, object]]] = {}
    for row in query_results:
        by_identity.setdefault(str(row["identity_id"]), []).append(row)

    summaries = []
    majority_target = (k // 2) + 1
    for identity_id, rows in sorted(by_identity.items()):
        total_positives = sum(int(row["metrics"]["positives_available"]) for row in rows)
        total_returned = sum(int(row["metrics"][f"returned_at_{k}"]) for row in rows)
        total_own = sum(int(row["metrics"][f"own_at_{k}"]) for row in rows)
        total_wrong = sum(int(row["metrics"][f"wrong_at_{k}"]) for row in rows)
        recalls = [float(row["metrics"][f"recall_at_{k}"]) for row in rows]
        own_values = [int(row["metrics"][f"own_at_{k}"]) for row in rows]
        summaries.append(
            {
                "identity_id": identity_id,
                "query_count": len(rows),
                "total_positives_available": total_positives,
                f"total_own_at_{k}": total_own,
                f"total_wrong_at_{k}": total_wrong,
                f"micro_recall_at_{k}": micro_rate(total_own, total_positives),
                f"micro_precision_at_{k}": micro_rate(total_own, total_returned),
                f"mean_recall_at_{k}": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
                f"min_own_at_{k}": min(own_values) if own_values else 0,
                f"max_own_at_{k}": max(own_values) if own_values else 0,
                f"queries_with_majority_own_at_{k}": sum(1 for value in own_values if value >= majority_target),
            }
        )
    return summaries


def evaluate_retrieval(args: argparse.Namespace) -> dict[str, object]:
    clips = load_clips(resolve_inside_project(args.clips))
    same_camera_weights, cross_camera_weights = build_weight_sets(args)
    analyzer = WalnutAnalyzer(vote_frame_window=args.vote_frame_window)

    profile_cache = {}
    for clip_id, clip in clips.items():
        profile_cache[clip_id] = analyze_clip(
            analyzer,
            clip,
            max_frames=args.max_frames,
            sample_every=args.sample_every,
        )

    query_results = []
    for query_clip in clips.values():
        candidates = []
        query_analysis = profile_cache[query_clip.clip_id]
        for candidate_clip in clips.values():
            if candidate_clip.clip_id == query_clip.clip_id:
                continue
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
        metrics = topk_metrics(query_clip.identity_id, ranked, args.k, args.candidate_pool)
        query_results.append(
            {
                "query_id": query_clip.clip_id,
                "identity_id": query_clip.identity_id,
                "cam_id": query_clip.cam_id,
                "take_id": query_clip.take_id,
                "clip_path": project_relative(query_clip.clip_path),
                "analysis": query_analysis,
                "metrics": metrics,
                "top_k": ranked[: args.k],
                "candidate_pool": ranked[: args.candidate_pool],
            }
        )

    return {
        "clips_path": args.clips,
        "query_count": len(query_results),
        "gallery_count": len(clips),
        "k": args.k,
        "candidate_pool": args.candidate_pool,
        "match_threshold": args.match_threshold,
        "ambiguous_threshold": args.ambiguous_threshold,
        "min_available_weight": args.min_available_weight,
        "same_camera_weights": same_camera_weights,
        "cross_camera_weights": cross_camera_weights,
        "summary": summarize_queries(query_results, args.k, args.candidate_pool),
        "identity_summary": summarize_identities(query_results, args.k),
        "queries": query_results,
    }


def write_eval_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    k = int(report["k"])
    pool_k = int(report["candidate_pool"])
    summary = report["summary"]
    identity_summary = report["identity_summary"]
    queries = report["queries"]
    assert isinstance(summary, dict)
    assert isinstance(identity_summary, list)
    assert isinstance(queries, list)

    with path.open("w", encoding="utf-8") as fh:
        fh.write("# YOLO-ReID Top-K Retrieval Evaluation Report\n\n")
        fh.write(
            "This evaluates labeled clips by ranking every other clip as a gallery candidate for each query.\n\n"
        )
        fh.write(f"- Clips manifest: `{report['clips_path']}`\n")
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
            f"({summary[f'total_own_at_{k}']}/{summary['total_positives_available']})\n"
        )
        fh.write(f"- `Precision@{k}` macro/query mean: `{summary[f'mean_precision_at_{k}']}`\n")
        fh.write(f"- `Top-{k} own clips per query`: `{summary[f'mean_own_at_{k}']}` mean\n")
        fh.write(f"- `Queries with majority own@{k}`: `{summary[f'queries_with_majority_own_at_{k}']}`\n\n")

        fh.write("## Summary Metrics\n\n")
        for key in sorted(summary):
            fh.write(f"- `{key}`: `{summary[key]}`\n")

        fh.write("\n## Per Identity\n\n")
        fh.write(
            f"| identity | queries | own@{k} total | wrong@{k} total | recall@{k} micro | "
            f"recall@{k} mean | precision@{k} micro | own@{k} min-max | majority-own queries |\n"
        )
        fh.write("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |\n")
        for row in identity_summary:
            fh.write(
                f"| {row['identity_id']} | {row['query_count']} | {row[f'total_own_at_{k}']} | "
                f"{row[f'total_wrong_at_{k}']} | {row[f'micro_recall_at_{k}']} | "
                f"{row[f'mean_recall_at_{k}']} | {row[f'micro_precision_at_{k}']} | "
                f"{row[f'min_own_at_{k}']}-{row[f'max_own_at_{k}']} | "
                f"{row[f'queries_with_majority_own_at_{k}']} |\n"
            )

        fh.write("\n## Per Query Top-K\n\n")
        fh.write(
            f"| query | identity | positives_available | own@{k} | wrong@{k} | "
            f"recall@{k} | precision@{k} | ambiguous_rate@{k} | false_match_rate@{k} | top candidates |\n"
        )
        fh.write("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |\n")
        for row in queries:
            metrics = row["metrics"]
            top_candidates = ", ".join(
                f"{candidate['candidate_id']}:{candidate['outcome']}:{candidate['retrieval_score']}"
                for candidate in row["top_k"]
            )
            fh.write(
                f"| {row['query_id']} | {row['identity_id']} | {metrics['positives_available']} | "
                f"{metrics[f'own_at_{k}']} | {metrics[f'wrong_at_{k}']} | "
                f"{metrics[f'recall_at_{k}']} | {metrics[f'precision_at_{k}']} | "
                f"{metrics[f'ambiguous_rate_at_{k}']} | {metrics[f'false_match_rate_at_{k}']} | "
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
            int(row["metrics"][f"own_at_{k}"]),
            -int(row["metrics"][f"wrong_at_{k}"]),
            str(row["query_id"]),
        ),
    )[:8]

    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Top-K Retrieval Debug Report\n\n")
        fh.write("This report inspects retrieval failures and high-risk candidates without running cameras, RTSP, TouchDesigner, or full tracking.\n\n")
        fh.write("## Worst Queries\n\n")
        fh.write(f"| query | identity | own@{k} | wrong@{k} | hard_negative_rate@{k} | margin_to_wrong_high_risk | top wrong candidates |\n")
        fh.write("| --- | --- | ---: | ---: | ---: | ---: | --- |\n")
        for row in worst:
            metrics = row["metrics"]
            wrong_candidates = [
                candidate
                for candidate in row["top_k"]
                if candidate["candidate_identity"] != row["identity_id"]
            ]
            wrong_text = ", ".join(
                f"{candidate['candidate_id']}:{candidate['outcome']}:{candidate['retrieval_score']}"
                for candidate in wrong_candidates[:5]
            )
            fh.write(
                f"| {row['query_id']} | {row['identity_id']} | {metrics[f'own_at_{k}']} | "
                f"{metrics[f'wrong_at_{k}']} | {metrics[f'hard_negative_rate_at_{k}']} | "
                f"{metrics['rank_k_margin_to_first_wrong_high_risk']} | {wrong_text} |\n"
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
    parser.add_argument("--k", type=int, default=9)
    parser.add_argument("--candidate-pool", type=int, default=12)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
