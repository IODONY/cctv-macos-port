#!/usr/bin/env python3
"""Export per-file Top-K rankings for a finished live session."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from live_session_grouping import project_relative, read_jsonl, write_json  # noqa: E402
from visual_grouping import VisualGroupRecord, cosine_similarity_matrix  # noqa: E402
from visual_reid import create_visual_embedder, normalize_vector  # noqa: E402


def parse_label_prefixes(value: str) -> list[str]:
    return [item.strip().lower() for item in str(value or "").split(",") if item.strip()]


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def resolve_events_path(session: str, events_path: str) -> Path:
    if events_path:
        return resolve_project_path(events_path)
    if not session:
        raise SystemExit("--session or --events-path is required")
    return PROJECT_ROOT / "logs" / "topk_live" / session / "gallery_events.jsonl"


def clip_id_from_asset(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_best"):
        stem = stem[: -len("_best")]
    if "_best_crop_" in stem:
        stem = stem.split("_best_crop_", 1)[0]
    return stem


def load_truth_labels(root: Path | None, label_prefixes: list[str]) -> dict[str, str]:
    if root is None or not root.exists():
        return {}
    labels: dict[str, str] = {}
    for label_dir in sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")):
        name = label_dir.name
        if label_prefixes and not any(name.lower().startswith(prefix) for prefix in label_prefixes):
            continue
        for path in sorted(label_dir.iterdir()):
            if path.name.startswith(".") or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".mp4"}:
                continue
            labels[clip_id_from_asset(path)] = name
    return labels


def embed_records(
    rows: list[dict[str, object]],
    embedding_model: str,
    embedding_source: str,
) -> tuple[list[VisualGroupRecord], list[dict[str, object]], str]:
    embedder = create_visual_embedder(model_name=embedding_model)
    records: list[VisualGroupRecord] = []
    failures: list[dict[str, object]] = []
    method = str(getattr(embedder, "method", embedding_model))

    for row in rows:
        clip_id = str(row.get("clip_id") or "")
        image_paths: list[Path] = []
        if embedding_source == "top-crops":
            for item in row.get("top_crop_paths") or []:
                image_paths.append(resolve_project_path(str(item)))
        if not image_paths:
            image_paths.append(resolve_project_path(str(row.get("best_frame_path") or "")))

        embeddings = []
        used_paths = []
        for image_path in image_paths:
            image = cv2.imread(str(image_path))
            if image is None:
                continue
            embedding, item_method = embedder.embed_bgr(image)
            if embedding is None:
                continue
            embeddings.append(embedding)
            used_paths.append(project_relative(image_path))
            method = item_method

        if not embeddings:
            failures.append(
                {
                    "clip_id": clip_id,
                    "reason": "embedding_failed",
                    "best_frame_path": str(row.get("best_frame_path") or ""),
                }
            )
            continue

        aggregate = normalize_vector(np.vstack(embeddings).mean(axis=0))
        if aggregate is None:
            failures.append({"clip_id": clip_id, "reason": "embedding_normalize_failed"})
            continue

        metadata = dict(row)
        metadata["file_topk_embedding_source"] = embedding_source
        metadata["file_topk_embedding_paths"] = used_paths
        records.append(
            VisualGroupRecord(
                clip_id=clip_id,
                clip_path=str(row.get("clip_path") or ""),
                best_frame_path=str(row.get("best_frame_path") or ""),
                embedding=aggregate,
                metadata=metadata,
            )
        )
    return records, failures, method


def build_rankings(
    records: list[VisualGroupRecord],
    truth_labels: dict[str, str],
    k: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    scores = cosine_similarity_matrix(records)
    k = max(1, int(k))
    rankings = []
    per_label: dict[str, list[dict[str, object]]] = defaultdict(list)

    for query_index, query in enumerate(records):
        query_label = truth_labels.get(query.clip_id, "")
        order = [index for index in np.argsort(scores[query_index])[::-1].tolist() if index != query_index]
        top_indices = order[:k]
        results = []
        own_count = 0
        labeled_wrong_count = 0
        for rank, candidate_index in enumerate(top_indices, start=1):
            candidate = records[candidate_index]
            candidate_label = truth_labels.get(candidate.clip_id, "")
            is_same = bool(query_label and candidate_label and query_label == candidate_label)
            if is_same:
                own_count += 1
            elif query_label and candidate_label:
                labeled_wrong_count += 1
            results.append(
                {
                    "rank": rank,
                    "score": round(float(scores[query_index, candidate_index]), 6),
                    "clip_id": candidate.clip_id,
                    "truth_label": candidate_label,
                    "same_truth_label": is_same,
                    "clip_path": candidate.clip_path,
                    "best_frame_path": candidate.best_frame_path,
                    "cam_label": candidate.metadata.get("cam_label", ""),
                    "duration_seconds": candidate.metadata.get("duration_seconds", None),
                    "quality": candidate.metadata.get("quality", None),
                }
            )

        available_positive_count = (
            sum(1 for record in records if truth_labels.get(record.clip_id, "") == query_label) - 1 if query_label else 0
        )
        max_possible = min(k, max(0, available_positive_count))
        precision = own_count / len(results) if results else 0.0
        recall = own_count / available_positive_count if available_positive_count > 0 else None
        normalized = own_count / max_possible if max_possible > 0 else None
        row = {
            "query_clip_id": query.clip_id,
            "query_truth_label": query_label,
            "query_clip_path": query.clip_path,
            "query_best_frame_path": query.best_frame_path,
            "query_cam_label": query.metadata.get("cam_label", ""),
            "k": k,
            "result_count": len(results),
            "available_positive_count": available_positive_count,
            "max_possible_own_count_at_k": max_possible,
            "own_count_at_k": own_count,
            "labeled_wrong_count_at_k": labeled_wrong_count,
            "precision_at_k": round(float(precision), 6),
            "recall_at_k": round(float(recall), 6) if recall is not None else None,
            "normalized_own_recall_at_k": round(float(normalized), 6) if normalized is not None else None,
            "results": results,
        }
        rankings.append(row)
        per_label[query_label or "unlabeled"].append(row)

    labeled_rows = [row for row in rankings if row["query_truth_label"] and row["available_positive_count"] > 0]
    summary = {
        "query_count": len(rankings),
        "candidate_count": len(records),
        "k": k,
        "truth_label_counts": dict(sorted(Counter(truth_labels.get(record.clip_id, "unlabeled") for record in records).items())),
        "mean_own_count_at_k": round(float(np.mean([row["own_count_at_k"] for row in labeled_rows])), 6)
        if labeled_rows
        else 0.0,
        "mean_precision_at_k": round(float(np.mean([row["precision_at_k"] for row in labeled_rows])), 6)
        if labeled_rows
        else 0.0,
        "mean_recall_at_k": round(float(np.mean([row["recall_at_k"] for row in labeled_rows if row["recall_at_k"] is not None])), 6)
        if labeled_rows
        else 0.0,
        "mean_normalized_own_recall_at_k": round(
            float(
                np.mean(
                    [
                        row["normalized_own_recall_at_k"]
                        for row in labeled_rows
                        if row["normalized_own_recall_at_k"] is not None
                    ]
                )
            ),
            6,
        )
        if labeled_rows
        else 0.0,
        "per_label": {},
    }
    for label, rows in sorted(per_label.items()):
        rows_with_positive = [row for row in rows if row["available_positive_count"] > 0]
        summary["per_label"][label] = {
            "query_count": len(rows),
            "mean_own_count_at_k": round(float(np.mean([row["own_count_at_k"] for row in rows_with_positive])), 6)
            if rows_with_positive
            else 0.0,
            "mean_precision_at_k": round(float(np.mean([row["precision_at_k"] for row in rows_with_positive])), 6)
            if rows_with_positive
            else 0.0,
            "mean_normalized_own_recall_at_k": round(
                float(
                    np.mean(
                        [
                            row["normalized_own_recall_at_k"]
                            for row in rows_with_positive
                            if row["normalized_own_recall_at_k"] is not None
                        ]
                    )
                ),
                6,
            )
            if rows_with_positive
            else 0.0,
        }
    return rankings, summary


def write_csv(path: Path, rankings: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "query_clip_id",
                "query_truth_label",
                "rank",
                "candidate_clip_id",
                "candidate_truth_label",
                "same_truth_label",
                "score",
                "candidate_clip_path",
                "candidate_best_frame_path",
            ],
        )
        writer.writeheader()
        for row in rankings:
            for result in row["results"]:
                writer.writerow(
                    {
                        "query_clip_id": row["query_clip_id"],
                        "query_truth_label": row["query_truth_label"],
                        "rank": result["rank"],
                        "candidate_clip_id": result["clip_id"],
                        "candidate_truth_label": result["truth_label"],
                        "same_truth_label": result["same_truth_label"],
                        "score": result["score"],
                        "candidate_clip_path": result["clip_path"],
                        "candidate_best_frame_path": result["best_frame_path"],
                    }
                )


def write_markdown(path: Path, payload: dict[str, object], max_queries: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    lines = [
        "# Live File-Level Top-K Rankings",
        "",
        "Each saved gallery clip is treated as one independent object. Merged similarity group membership is not used for ranking.",
        "",
        "## Summary",
        "",
        f"- Session: `{payload['session_id']}`",
        f"- Events: `{payload['events_path']}`",
        f"- Truth root: `{payload.get('truth_root', '')}`",
        f"- Embedding model: `{payload['embedding_model']}`",
        f"- Embedding method: `{payload['embedding_method']}`",
        f"- Embedding source: `{payload['embedding_source']}`",
        f"- Query count: `{summary['query_count']}`",
        f"- Candidate count: `{summary['candidate_count']}`",
        f"- K: `{summary['k']}`",
        f"- Mean OwnCount@K: `{summary['mean_own_count_at_k']}`",
        f"- Mean Precision@K: `{summary['mean_precision_at_k']}`",
        f"- Mean Recall@K: `{summary['mean_recall_at_k']}`",
        f"- Mean Normalized OwnRecall@K: `{summary['mean_normalized_own_recall_at_k']}`",
        "",
        "## Truth Labels",
        "",
        "| label | clips |",
        "| --- | ---: |",
    ]
    for label, count in summary["truth_label_counts"].items():
        lines.append(f"| `{label}` | {count} |")

    lines.extend(
        [
            "",
            "## Per Label",
            "",
            "| label | queries | mean own@K | mean precision@K | mean normalized recall@K |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for label, item in summary["per_label"].items():
        lines.append(
            f"| `{label}` | {item['query_count']} | {item['mean_own_count_at_k']} | "
            f"{item['mean_precision_at_k']} | {item['mean_normalized_own_recall_at_k']} |"
        )

    lines.extend(["", "## Query Rankings", ""])
    for row in payload["rankings"][:max_queries]:
        lines.append(
            f"### {row['query_clip_id']} `{row['query_truth_label'] or 'unlabeled'}` "
            f"own@K={row['own_count_at_k']} precision={row['precision_at_k']}"
        )
        lines.append("")
        lines.append("| rank | score | label | same | clip_id |")
        lines.append("| ---: | ---: | --- | --- | --- |")
        for result in row["results"]:
            lines.append(
                f"| {result['rank']} | {result['score']} | `{result['truth_label'] or 'unlabeled'}` | "
                f"{result['same_truth_label']} | `{result['clip_id']}` |"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", default="")
    parser.add_argument("--events-path", default="")
    parser.add_argument("--truth-root", default="")
    parser.add_argument("--truth-label-prefixes", default="p")
    parser.add_argument("--embedding-model", default="osnet_x0_25")
    parser.add_argument("--embedding-source", choices=("best-crops", "top-crops"), default="best-crops")
    parser.add_argument("--k", type=int, default=7)
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-csv", default="")
    parser.add_argument("--output-report", default="")
    parser.add_argument("--report-max-queries", type=int, default=80)
    args = parser.parse_args()

    session_id = args.session or (Path(args.events_path).expanduser().resolve().parent.name if args.events_path else "")
    events_path = resolve_events_path(session_id, args.events_path)
    if not session_id:
        session_id = events_path.parent.name

    truth_root = resolve_project_path(args.truth_root) if args.truth_root else PROJECT_ROOT / "snapshots" / "live_topk" / session_id / "similarity_groups_merged"
    truth_labels = load_truth_labels(truth_root, parse_label_prefixes(args.truth_label_prefixes))
    rows = read_jsonl(events_path)
    records, failures, embedding_method = embed_records(rows, args.embedding_model, args.embedding_source)
    rankings, summary = build_rankings(records, truth_labels, args.k)

    output_json = resolve_project_path(args.output_json) if args.output_json else events_path.parent / f"file_topk_k{args.k}.json"
    output_csv = resolve_project_path(args.output_csv) if args.output_csv else events_path.parent / f"file_topk_k{args.k}.csv"
    output_report = (
        resolve_project_path(args.output_report)
        if args.output_report
        else PROJECT_ROOT / "docs" / "reports" / f"LIVE_FILE_TOPK_{session_id}_K{args.k}_REPORT.md"
    )
    payload = {
        "session_id": session_id,
        "events_path": project_relative(events_path),
        "truth_root": project_relative(truth_root),
        "embedding_model": args.embedding_model,
        "embedding_method": embedding_method,
        "embedding_source": args.embedding_source,
        "failures": failures,
        "summary": summary,
        "rankings": rankings,
    }
    write_json(output_json, payload)
    write_csv(output_csv, rankings)
    write_markdown(output_report, payload, max_queries=max(1, int(args.report_max_queries)))

    print(
        "FILE_TOPK_OK "
        f"session={session_id} k={args.k} records={len(records)} failures={len(failures)} "
        f"mean_own={summary['mean_own_count_at_k']} "
        f"precision={summary['mean_precision_at_k']} "
        f"normalized_recall={summary['mean_normalized_own_recall_at_k']} "
        f"json={project_relative(output_json)} csv={project_relative(output_csv)} "
        f"report={project_relative(output_report)}"
    )
    if failures:
        print(json.dumps({"failures": failures[:10]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
