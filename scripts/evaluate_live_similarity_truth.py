#!/usr/bin/env python3
"""Tune live similarity grouping against a manually sorted truth folder."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from live_session_grouping import export_merged_groups, project_relative, read_jsonl, write_json  # noqa: E402
from visual_grouping import VisualGroupRecord, group_records  # noqa: E402
from visual_reid import (  # noqa: E402
    analyze_clip_visual,
    create_visual_embedder,
    crop_person,
    crop_quality,
    normalize_vector,
    reset_analyzer_state,
)
from walnut_core import WalnutAnalyzer  # noqa: E402


def parse_csv(value: str, cast=str) -> list:
    items = []
    for raw in str(value or "").split(","):
        raw = raw.strip()
        if raw:
            items.append(cast(raw))
    return items


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
    stem = re.sub(r"_crop_\d+$", "", stem)
    stem = re.sub(r"_best$", "", stem)
    return stem


def load_truth_assignments(root: Path, duplicate_policy: str) -> dict[str, object]:
    raw: dict[str, list[str]] = defaultdict(list)
    files_by_clip: dict[str, list[str]] = defaultdict(list)
    labels: dict[str, list[str]] = defaultdict(list)

    for label_dir in sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")):
        label = label_dir.name
        for path in sorted(label_dir.iterdir()):
            if path.name.startswith(".") or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".mp4"}:
                continue
            clip_id = clip_id_from_asset(path)
            raw[clip_id].append(label)
            labels[label].append(clip_id)
            files_by_clip[clip_id].append(project_relative(path))

    conflicts = {
        clip_id: {"labels": sorted(set(label_list)), "files": files_by_clip[clip_id]}
        for clip_id, label_list in raw.items()
        if len(set(label_list)) > 1
    }

    assignments: dict[str, str] = {}
    for clip_id, label_list in raw.items():
        unique_labels = list(dict.fromkeys(label_list))
        if len(unique_labels) == 1:
            assignments[clip_id] = unique_labels[0]
        elif duplicate_policy == "first":
            assignments[clip_id] = unique_labels[0]
        elif duplicate_policy == "last":
            assignments[clip_id] = unique_labels[-1]
        elif duplicate_policy == "exclude":
            continue
        else:
            raise ValueError(f"Unsupported duplicate policy: {duplicate_policy}")

    effective_labels: dict[str, list[str]] = defaultdict(list)
    for clip_id, label in assignments.items():
        effective_labels[label].append(clip_id)

    return {
        "truth_root": project_relative(root),
        "duplicate_policy": duplicate_policy,
        "raw_label_count": len(labels),
        "raw_labels": {label: sorted(items) for label, items in sorted(labels.items())},
        "conflicts": conflicts,
        "assignments": assignments,
        "effective_label_count": len(effective_labels),
        "effective_labels": {label: sorted(items) for label, items in sorted(effective_labels.items())},
    }


def read_image_embedding(embedder, image_path: Path) -> tuple[np.ndarray | None, str]:
    image = cv2.imread(str(image_path))
    if image is None:
        return None, str(getattr(embedder, "method", "unknown"))
    return embedder.embed_bgr(image)


def embed_saved_crops(
    rows: list[dict[str, object]],
    embedder,
    source: str,
) -> tuple[list[VisualGroupRecord], list[dict[str, object]], str]:
    records: list[VisualGroupRecord] = []
    failures: list[dict[str, object]] = []
    method = str(getattr(embedder, "method", "unknown"))

    for row in rows:
        clip_id = str(row.get("clip_id") or "")
        candidate_paths: list[Path] = []
        if source == "top-crops":
            for item in row.get("top_crop_paths") or []:
                candidate_paths.append(resolve_project_path(str(item)))
        if not candidate_paths:
            candidate_paths.append(resolve_project_path(str(row.get("best_frame_path") or "")))

        embeddings = []
        methods = []
        failed_paths = []
        for image_path in candidate_paths:
            embedding, item_method = read_image_embedding(embedder, image_path)
            if embedding is None:
                failed_paths.append(project_relative(image_path))
                continue
            embeddings.append(embedding)
            methods.append(item_method)

        if not embeddings:
            failures.append({"clip_id": clip_id, "reason": "crop_embedding_failed", "paths": failed_paths})
            continue

        aggregate = normalize_vector(np.vstack(embeddings).mean(axis=0))
        if aggregate is None:
            failures.append({"clip_id": clip_id, "reason": "embedding_normalize_failed"})
            continue

        metadata = dict(row)
        metadata["truth_eval_embedding_source"] = source
        metadata["truth_eval_embedding_count"] = len(embeddings)
        records.append(
            VisualGroupRecord(
                clip_id=clip_id,
                clip_path=str(row.get("clip_path") or ""),
                best_frame_path=str(resolve_project_path(str(row.get("best_frame_path") or ""))),
                embedding=aggregate,
                metadata=metadata,
            )
        )
        if methods:
            method = methods[-1]

    return records, failures, method


def embed_full_mp4(
    rows: list[dict[str, object]],
    embedder,
    args: argparse.Namespace,
) -> tuple[list[VisualGroupRecord], list[dict[str, object]], str]:
    analyzer = WalnutAnalyzer(vote_frame_window=args.visual_vote_frame_window)
    cache_dir = resolve_project_path(args.embedding_cache_dir)
    debug_dir = resolve_project_path(args.debug_dir)
    records: list[VisualGroupRecord] = []
    failures: list[dict[str, object]] = []
    method = str(getattr(embedder, "method", "unknown"))

    for row in rows:
        clip_id = str(row.get("clip_id") or "")
        clip_path = resolve_project_path(str(row.get("clip_path") or ""))
        analysis = analyze_clip_visual(
            analyzer,
            embedder,
            clip_path,
            clip_id,
            max_frames=args.max_frames,
            sample_every=args.sample_every,
            top_n=args.top_n,
            save_debug_crops=args.save_debug_crops,
            debug_dir=debug_dir,
            embedding_cache_dir=cache_dir,
            crop_expand_ratio=args.crop_expand_ratio,
        )
        embedding = analysis.get("embedding")
        if embedding is None:
            failures.append(
                {
                    "clip_id": clip_id,
                    "reason": analysis.get("reason", "full_mp4_embedding_failed"),
                    "clip_path": project_relative(clip_path),
                }
            )
            continue

        metadata = dict(row)
        metadata.update({f"truth_eval_{key}": value for key, value in analysis.items() if key != "embedding"})
        records.append(
            VisualGroupRecord(
                clip_id=clip_id,
                clip_path=str(clip_path),
                best_frame_path=str(resolve_project_path(str(row.get("best_frame_path") or ""))),
                embedding=embedding,
                metadata=metadata,
            )
        )
        method = str(analysis.get("embedding_method") or method)

    return records, failures, method


def build_anchor_embedding(
    row: dict[str, object],
    embedder,
    anchor_source: str,
) -> tuple[np.ndarray | None, str, int]:
    paths: list[Path] = []
    if anchor_source == "top-crops":
        for item in row.get("top_crop_paths") or []:
            paths.append(resolve_project_path(str(item)))
    if not paths:
        paths.append(resolve_project_path(str(row.get("best_frame_path") or "")))

    embeddings = []
    method = str(getattr(embedder, "method", "unknown"))
    for path in paths:
        embedding, item_method = read_image_embedding(embedder, path)
        if embedding is not None:
            embeddings.append(embedding)
            method = item_method
    if not embeddings:
        return None, method, 0
    return normalize_vector(np.vstack(embeddings).mean(axis=0)), method, len(embeddings)


def embed_full_mp4_anchored(
    rows: list[dict[str, object]],
    embedder,
    args: argparse.Namespace,
) -> tuple[list[VisualGroupRecord], list[dict[str, object]], str]:
    analyzer = WalnutAnalyzer(vote_frame_window=args.visual_vote_frame_window)
    records: list[VisualGroupRecord] = []
    failures: list[dict[str, object]] = []
    method = str(getattr(embedder, "method", "unknown"))
    anchor_weight = max(0.0, min(1.0, float(args.anchor_weight)))

    for row in rows:
        clip_id = str(row.get("clip_id") or "")
        anchor, anchor_method, anchor_count = build_anchor_embedding(row, embedder, args.anchor_source)
        method = anchor_method or method
        if anchor is None:
            failures.append({"clip_id": clip_id, "reason": "anchor_embedding_failed"})
            continue

        reset_analyzer_state(analyzer)
        clip_path = resolve_project_path(str(row.get("clip_path") or ""))
        cap = cv2.VideoCapture(str(clip_path))
        if not cap.isOpened():
            failures.append({"clip_id": clip_id, "reason": "video_open_failed", "clip_path": project_relative(clip_path)})
            continue

        frames_read = 0
        frames_analyzed = 0
        candidates = []
        try:
            while frames_read < int(args.max_frames):
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                frames_read += 1
                if frames_read % max(1, int(args.sample_every)) != 0:
                    continue
                frames_analyzed += 1
                people = analyzer.analyze_frame(frame)
                for person in people:
                    crop = crop_person(frame, person.get("box", (0, 0, 0, 0)), args.crop_expand_ratio)
                    if crop is None:
                        continue
                    embedding, item_method = embedder.embed_bgr(crop)
                    if embedding is None:
                        continue
                    method = item_method
                    anchor_similarity = float(np.dot(anchor, embedding))
                    if anchor_similarity < float(args.min_anchor_similarity):
                        continue
                    quality = float(crop_quality(crop, person, frame.shape))
                    score = (anchor_similarity * anchor_weight) + (quality * (1.0 - anchor_weight))
                    candidates.append(
                        {
                            "score": score,
                            "anchor_similarity": anchor_similarity,
                            "quality": quality,
                            "embedding": embedding,
                            "frame_index": frames_read,
                        }
                    )
        finally:
            cap.release()

        candidates.sort(key=lambda item: item["score"], reverse=True)
        selected = candidates[: max(1, int(args.top_n))]
        if not selected:
            failures.append(
                {
                    "clip_id": clip_id,
                    "reason": "no_anchored_person_crop",
                    "clip_path": project_relative(clip_path),
                    "frames_read": frames_read,
                    "frames_analyzed": frames_analyzed,
                }
            )
            continue

        aggregate = normalize_vector(np.vstack([item["embedding"] for item in selected]).mean(axis=0))
        if aggregate is None:
            failures.append({"clip_id": clip_id, "reason": "embedding_normalize_failed"})
            continue

        metadata = dict(row)
        metadata.update(
            {
                "truth_eval_embedding_source": "full-mp4-anchored",
                "truth_eval_anchor_source": args.anchor_source,
                "truth_eval_anchor_count": anchor_count,
                "truth_eval_anchor_weight": anchor_weight,
                "truth_eval_frames_read": frames_read,
                "truth_eval_frames_analyzed": frames_analyzed,
                "truth_eval_selected_frame_indices": [int(item["frame_index"]) for item in selected],
                "truth_eval_selected_anchor_scores": [round(float(item["anchor_similarity"]), 6) for item in selected],
                "truth_eval_selected_quality_scores": [round(float(item["quality"]), 6) for item in selected],
            }
        )
        records.append(
            VisualGroupRecord(
                clip_id=clip_id,
                clip_path=str(clip_path),
                best_frame_path=str(resolve_project_path(str(row.get("best_frame_path") or ""))),
                embedding=aggregate,
                metadata=metadata,
            )
        )

    return records, failures, method


def prediction_map(grouping: dict[str, object], records: list[VisualGroupRecord]) -> dict[str, str]:
    result = {}
    for group in grouping.get("groups", []):
        label = str(group.get("group_label"))
        for index in group.get("member_indices", []):
            result[records[int(index)].clip_id] = label
    return result


def summarize_predicted_groups(
    grouping: dict[str, object],
    records: list[VisualGroupRecord],
    truth: dict[str, str],
) -> list[dict[str, object]]:
    summary = []
    for group in grouping.get("groups", []):
        members = [records[int(index)].clip_id for index in group.get("member_indices", [])]
        truth_counts = Counter(truth.get(clip_id, "unlabeled") for clip_id in members)
        summary.append(
            {
                "group_label": group.get("group_label"),
                "count": len(members),
                "truth_counts": dict(sorted(truth_counts.items())),
                "members": members,
                "pairwise": group.get("pairwise", {}),
            }
        )
    return summary


def evaluate_grouping(
    grouping: dict[str, object],
    records: list[VisualGroupRecord],
    truth: dict[str, str],
) -> dict[str, object]:
    predicted = prediction_map(grouping, records)
    eval_ids = sorted(clip_id for clip_id in truth if clip_id in predicted)
    missing_truth_ids = sorted(clip_id for clip_id in truth if clip_id not in predicted)

    tp = fp = fn = tn = 0
    for left_pos, left in enumerate(eval_ids):
        for right in eval_ids[left_pos + 1 :]:
            same_truth = truth[left] == truth[right]
            same_pred = predicted[left] == predicted[right]
            if same_truth and same_pred:
                tp += 1
            elif same_truth and not same_pred:
                fn += 1
            elif not same_truth and same_pred:
                fp += 1
            else:
                tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) else 1.0

    pred_groups = defaultdict(list)
    for clip_id in eval_ids:
        pred_groups[predicted[clip_id]].append(clip_id)
    purity_numerator = 0
    for members in pred_groups.values():
        counts = Counter(truth[clip_id] for clip_id in members)
        purity_numerator += counts.most_common(1)[0][1]
    purity = purity_numerator / len(eval_ids) if eval_ids else 1.0

    truth_label_count = len(set(truth[clip_id] for clip_id in eval_ids))
    return {
        "pair_precision": round(float(precision), 6),
        "pair_recall": round(float(recall), 6),
        "pair_f1": round(float(f1), 6),
        "pair_accuracy": round(float(accuracy), 6),
        "purity": round(float(purity), 6),
        "tp": tp,
        "fp_overmerge_pairs": fp,
        "fn_split_pairs": fn,
        "tn": tn,
        "evaluated_clip_count": len(eval_ids),
        "truth_label_count": truth_label_count,
        "predicted_group_count": grouping.get("group_count"),
        "predicted_group_sizes": grouping.get("group_sizes"),
        "missing_truth_clip_ids": missing_truth_ids,
        "predicted_groups": summarize_predicted_groups(grouping, records, truth),
    }


def rank_key(result: dict[str, object]) -> tuple[float, float, float, int, int, int]:
    metrics = result["metrics"]
    return (
        float(metrics["pair_f1"]),
        float(metrics["pair_precision"]),
        float(metrics["purity"]),
        -int(metrics["fp_overmerge_pairs"]),
        -int(metrics["fn_split_pairs"]),
        -abs(int(metrics["predicted_group_count"]) - int(metrics["truth_label_count"])),
    )


def write_markdown_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best = payload.get("best_result", {})
    best_metrics = best.get("metrics", {})
    truth = payload.get("truth", {})
    lines = [
        "# Live Similarity Truth Evaluation",
        "",
        "This report compares automatic live similarity grouping against a manually sorted truth folder.",
        "",
        "## Summary",
        "",
        f"- Session: `{payload.get('session_id')}`",
        f"- Events: `{payload.get('events_path')}`",
        f"- Truth root: `{truth.get('truth_root')}`",
        f"- Embedding source: `{payload.get('embedding_source')}`",
        f"- Embedding model: `{payload.get('embedding_model')}`",
        f"- Embedding method: `{payload.get('embedding_method')}`",
        f"- Records embedded: `{payload.get('record_count')}`",
        f"- Embedding failures: `{len(payload.get('failures', []))}`",
        f"- Duplicate truth policy: `{truth.get('duplicate_policy')}`",
        f"- Truth conflicts: `{len(truth.get('conflicts', {}))}`",
        "",
        "## Best Configuration",
        "",
        f"- Method: `{best.get('method')}`",
        f"- Threshold: `{best.get('threshold')}`",
        f"- Reciprocal top-N: `{best.get('reciprocal_topn')}`",
        f"- Predicted group count: `{best_metrics.get('predicted_group_count')}`",
        f"- Predicted sizes: `{best_metrics.get('predicted_group_sizes')}`",
        f"- Pairwise F1: `{best_metrics.get('pair_f1')}`",
        f"- Pairwise precision: `{best_metrics.get('pair_precision')}`",
        f"- Pairwise recall: `{best_metrics.get('pair_recall')}`",
        f"- Purity: `{best_metrics.get('purity')}`",
        f"- Over-merged different-person pairs: `{best_metrics.get('fp_overmerge_pairs')}`",
        f"- Split same-person pairs: `{best_metrics.get('fn_split_pairs')}`",
        "",
        "## Truth Labels",
        "",
        "| label | clips |",
        "| --- | ---: |",
    ]
    for label, clips in truth.get("effective_labels", {}).items():
        lines.append(f"| `{label}` | {len(clips)} |")

    if truth.get("conflicts"):
        lines.extend(["", "## Duplicate Truth Conflicts", ""])
        for clip_id, conflict in truth["conflicts"].items():
            lines.append(f"- `{clip_id}` appears in labels `{conflict.get('labels')}`")

    lines.extend(
        [
            "",
            "## Top Configurations",
            "",
            "| rank | method | threshold | top-N | groups | sizes | pair F1 | precision | recall | purity | overmerge | split |",
            "| ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for index, result in enumerate(payload.get("results", [])[:20], start=1):
        metrics = result["metrics"]
        lines.append(
            "| {rank} | {method} | {threshold} | {topn} | {groups} | {sizes} | {f1} | {precision} | {recall} | {purity} | {fp} | {fn} |".format(
                rank=index,
                method=result["method"],
                threshold=result["threshold"],
                topn=result["reciprocal_topn"],
                groups=metrics["predicted_group_count"],
                sizes=metrics["predicted_group_sizes"],
                f1=metrics["pair_f1"],
                precision=metrics["pair_precision"],
                recall=metrics["pair_recall"],
                purity=metrics["purity"],
                fp=metrics["fp_overmerge_pairs"],
                fn=metrics["fn_split_pairs"],
            )
        )

    lines.extend(["", "## Best Predicted Groups", ""])
    for group in best_metrics.get("predicted_groups", []):
        lines.append(
            "- `{label}` count={count} truth_counts={truth_counts} pairwise={pairwise}".format(
                label=group["group_label"],
                count=group["count"],
                truth_counts=group["truth_counts"],
                pairwise=group["pairwise"],
            )
        )
        for clip_id in group["members"]:
            lines.append(f"  - `{clip_id}`")

    if payload.get("exported_best_subdir"):
        lines.extend(["", "## Export", "", f"- Best grouping export: `{payload['exported_best_subdir']}`"])

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", default="")
    parser.add_argument("--events-path", default="")
    parser.add_argument(
        "--truth-root",
        default="",
        help="Manual truth folder. Defaults to snapshots/live_topk/<session>/similarity_groups_merged/group_001/jpg.",
    )
    parser.add_argument("--duplicate-policy", choices=("exclude", "first", "last"), default="exclude")
    parser.add_argument(
        "--embedding-source",
        choices=("best-crops", "top-crops", "full-mp4", "full-mp4-anchored"),
        default="best-crops",
    )
    parser.add_argument("--embedding-model", default="osnet_x0_25")
    parser.add_argument("--methods", default="reciprocal,centroid,connected")
    parser.add_argument("--thresholds", default="0.45,0.50,0.55,0.60,0.65,0.70,0.75,0.80")
    parser.add_argument("--reciprocal-topns", default="1,2,3,4,5")
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--max-frames", type=int, default=240)
    parser.add_argument("--sample-every", type=int, default=5)
    parser.add_argument("--crop-expand-ratio", type=float, default=0.10)
    parser.add_argument("--anchor-source", choices=("best-crops", "top-crops"), default="best-crops")
    parser.add_argument("--anchor-weight", type=float, default=0.85)
    parser.add_argument("--min-anchor-similarity", type=float, default=-1.0)
    parser.add_argument("--visual-vote-frame-window", type=int, default=20)
    parser.add_argument("--visual-color-weight", type=float, default=0.20)
    parser.add_argument("--save-debug-crops", action="store_true")
    parser.add_argument("--debug-dir", default="snapshots/reid_debug/live_similarity_truth")
    parser.add_argument("--embedding-cache-dir", default="logs/embedding_cache/live_similarity_truth")
    parser.add_argument("--write-report", default="docs/reports/LIVE_SIMILARITY_TRUTH_EVAL_REPORT.md")
    parser.add_argument("--write-json", default="")
    parser.add_argument("--export-best-subdir", default="")
    parser.add_argument("--export-mode", choices=("symlink", "copy", "path"), default="symlink")
    args = parser.parse_args()

    session_id = args.session or (Path(args.events_path).expanduser().resolve().parent.name if args.events_path else "")
    events_path = resolve_events_path(session_id, args.events_path)
    truth_root_arg = args.truth_root or f"snapshots/live_topk/{session_id}/similarity_groups_merged/group_001/jpg"
    truth_root = resolve_project_path(truth_root_arg)
    rows = read_jsonl(events_path)
    truth_payload = load_truth_assignments(truth_root, args.duplicate_policy)
    truth_assignments = dict(truth_payload["assignments"])

    embedder = create_visual_embedder(model_name=args.embedding_model, color_weight=args.visual_color_weight)
    if args.embedding_source == "full-mp4":
        records, failures, embedding_method = embed_full_mp4(rows, embedder, args)
    elif args.embedding_source == "full-mp4-anchored":
        records, failures, embedding_method = embed_full_mp4_anchored(rows, embedder, args)
    else:
        records, failures, embedding_method = embed_saved_crops(rows, embedder, args.embedding_source)

    methods = parse_csv(args.methods)
    thresholds = parse_csv(args.thresholds, float)
    reciprocal_topns = parse_csv(args.reciprocal_topns, int)
    results = []
    for method in methods:
        topns = reciprocal_topns if method == "reciprocal" else [reciprocal_topns[0] if reciprocal_topns else 1]
        for threshold in thresholds:
            for topn in topns:
                grouping = group_records(records, method=method, threshold=threshold, reciprocal_topn=topn)
                metrics = evaluate_grouping(grouping, records, truth_assignments)
                results.append(
                    {
                        "method": method,
                        "threshold": round(float(threshold), 4),
                        "reciprocal_topn": int(topn),
                        "grouping": grouping,
                        "metrics": metrics,
                    }
                )

    results.sort(key=rank_key, reverse=True)
    best = results[0] if results else {}
    output_json = resolve_project_path(args.write_json) if args.write_json else events_path.parent / "similarity_truth_eval.json"
    payload = {
        "session_id": session_id or events_path.parent.name,
        "events_path": project_relative(events_path),
        "truth": truth_payload,
        "embedding_source": args.embedding_source,
        "embedding_model": args.embedding_model,
        "embedding_method": embedding_method,
        "record_count": len(records),
        "source_event_count": len(rows),
        "failures": failures,
        "best_result": best,
        "results": results,
    }

    if args.export_best_subdir and best:
        output_root = PROJECT_ROOT / "snapshots" / "live_topk" / (session_id or events_path.parent.name) / args.export_best_subdir
        export_merged_groups(best["grouping"], output_root, args.export_mode)
        payload["exported_best_subdir"] = project_relative(output_root)

    write_json(output_json, payload)
    payload["json_path"] = project_relative(output_json)

    if args.write_report:
        report_path = resolve_project_path(args.write_report)
        write_markdown_report(report_path, payload)
        payload["report_path"] = project_relative(report_path)

    best_metrics = best.get("metrics", {}) if best else {}
    print(
        "TRUTH_EVAL_OK "
        f"session={payload['session_id']} "
        f"source={args.embedding_source} "
        f"records={len(records)} "
        f"truth_clips={len(truth_assignments)} "
        f"conflicts={len(truth_payload['conflicts'])} "
        f"best_method={best.get('method')} "
        f"best_threshold={best.get('threshold')} "
        f"best_topn={best.get('reciprocal_topn')} "
        f"best_groups={best_metrics.get('predicted_group_count')} "
        f"best_sizes={best_metrics.get('predicted_group_sizes')} "
        f"pair_f1={best_metrics.get('pair_f1')} "
        f"precision={best_metrics.get('pair_precision')} "
        f"recall={best_metrics.get('pair_recall')} "
        f"json={payload['json_path']}"
    )
    if payload.get("report_path"):
        print(f"REPORT {payload['report_path']}")
    if payload.get("exported_best_subdir"):
        print(f"EXPORT {payload['exported_best_subdir']}")
    if failures:
        print(json.dumps({"failures": failures[:10]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
