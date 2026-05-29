#!/usr/bin/env python3
"""Sweep live best-crop similarity grouping thresholds."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from visual_reid import create_visual_embedder, normalize_vector  # noqa: E402


def parse_thresholds(value: str) -> list[float]:
    thresholds = []
    for item in str(value).split(","):
        item = item.strip()
        if item:
            thresholds.append(float(item))
    if not thresholds:
        raise argparse.ArgumentTypeError("at least one threshold is required")
    return thresholds


def resolve_events_path(args: argparse.Namespace) -> Path:
    if args.events_path:
        return Path(args.events_path).expanduser().resolve()
    if not args.session:
        raise SystemExit("--session or --events-path is required")
    return PROJECT_ROOT / "logs" / "topk_live" / args.session / "gallery_events.jsonl"


def read_events(path: Path) -> list[dict[str, object]]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def connected_components(vectors: list[np.ndarray], threshold: float) -> list[list[int]]:
    parent = list(range(len(vectors)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for left in range(len(vectors)):
        for right in range(left + 1, len(vectors)):
            score = float(np.dot(vectors[left], vectors[right]))
            if score >= threshold:
                union(left, right)

    groups: dict[int, list[int]] = defaultdict(list)
    for index in range(len(vectors)):
        groups[find(index)].append(index)
    return sorted(groups.values(), key=lambda group: (-len(group), group[0]))


def centroid_groups(vectors: list[np.ndarray], threshold: float) -> list[list[int]]:
    groups: list[dict[str, object]] = []
    for index, vector in enumerate(vectors):
        best_group = None
        best_score = -1.0
        for group in groups:
            centroid = group["centroid"]
            score = float(np.dot(vector, centroid))
            if score > best_score:
                best_score = score
                best_group = group
        if best_group is None or best_score < threshold:
            groups.append({"centroid": vector, "indices": [index]})
            continue
        indices = best_group["indices"]
        indices.append(index)
        updated = normalize_vector(np.vstack([vectors[i] for i in indices]).mean(axis=0))
        best_group["centroid"] = vector if updated is None else updated
    return sorted((group["indices"] for group in groups), key=lambda group: (-len(group), group[0]))


def format_sizes(groups: list[list[int]]) -> str:
    return "[" + ", ".join(str(len(group)) for group in groups) + "]"


def write_report(
    path: Path,
    source_path: Path,
    model_name: str,
    method: str,
    rows: list[dict[str, object]],
    threshold_results: list[dict[str, object]],
    pairwise_scores: list[float],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Live OSNet Similarity Grouping Sweep",
        "",
        "This report re-embeds saved live `_best.jpg` crops only. It does not run RTSP, webcam, TouchDesigner, or live tracking.",
        "",
        "## Source",
        "",
        f"- Events: `{source_path.relative_to(PROJECT_ROOT).as_posix()}`",
        f"- Records embedded: `{len(rows)}`",
        f"- Embedding model: `{model_name}`",
        f"- Embedding method: `{method}`",
        "",
        "## Threshold Sweep",
        "",
        "| threshold | connected groups | connected sizes | live-centroid groups | live-centroid sizes |",
        "| ---: | ---: | --- | ---: | --- |",
    ]
    for result in threshold_results:
        lines.append(
            "| {threshold} | {connected_count} | {connected_sizes} | {centroid_count} | {centroid_sizes} |".format(
                **result
            )
        )
    lines.extend(
        [
            "",
            "## Pairwise Similarity",
            "",
        ]
    )
    if pairwise_scores:
        lines.extend(
            [
                f"- Min: `{min(pairwise_scores):.4f}`",
                f"- Mean: `{float(np.mean(pairwise_scores)):.4f}`",
                f"- Median: `{float(np.median(pairwise_scores)):.4f}`",
                f"- Max: `{max(pairwise_scores):.4f}`",
            ]
        )
    else:
        lines.append("- Not enough records for pairwise statistics.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- For a single-person smoke session, a lower group count is desirable.",
            "- The connected grouping column shows whether the embedding space links the saved crops together.",
            "- The live-centroid column approximates the current online export grouping logic.",
            "- If different visitors merge in future tests, raise `--similarity-group-threshold`; if the same visitor splits, lower it or add session-end merge.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", help="logs/topk_live/<session> to analyze.")
    parser.add_argument("--events-path", help="Explicit gallery_events.jsonl path.")
    parser.add_argument("--embedding-model", default="osnet_x0_25")
    parser.add_argument("--thresholds", type=parse_thresholds, default=parse_thresholds("0.50,0.55,0.60,0.65,0.70"))
    parser.add_argument("--output-report", default="")
    args = parser.parse_args()

    events_path = resolve_events_path(args)
    rows = read_events(events_path)
    embedder = create_visual_embedder(model_name=args.embedding_model)

    vectors = []
    kept_rows = []
    failures = []
    for row in rows:
        image_path = Path(str(row.get("best_frame_path") or "")).expanduser()
        if not image_path.is_absolute():
            image_path = (PROJECT_ROOT / image_path).resolve()
        image = cv2.imread(str(image_path))
        if image is None:
            failures.append({"clip_id": row.get("clip_id"), "reason": "best_frame_read_failed", "path": str(image_path)})
            continue
        embedding, _method = embedder.embed_bgr(image)
        if embedding is None:
            failures.append({"clip_id": row.get("clip_id"), "reason": "embedding_failed", "path": str(image_path)})
            continue
        vectors.append(embedding)
        kept_rows.append(row)

    pairwise_scores = []
    for left in range(len(vectors)):
        for right in range(left + 1, len(vectors)):
            pairwise_scores.append(float(np.dot(vectors[left], vectors[right])))

    results = []
    for threshold in args.thresholds:
        connected = connected_components(vectors, threshold)
        centroid = centroid_groups(vectors, threshold)
        result = {
            "threshold": f"{threshold:.2f}",
            "connected_count": len(connected),
            "connected_sizes": format_sizes(connected),
            "centroid_count": len(centroid),
            "centroid_sizes": format_sizes(centroid),
        }
        results.append(result)
        print(
            "threshold={threshold} connected_groups={connected_count} connected_sizes={connected_sizes} "
            "centroid_groups={centroid_count} centroid_sizes={centroid_sizes}".format(**result)
        )

    print(f"records={len(kept_rows)} failures={len(failures)} method={embedder.method}")
    if pairwise_scores:
        print(
            "pairwise min={:.4f} mean={:.4f} median={:.4f} max={:.4f}".format(
                min(pairwise_scores),
                float(np.mean(pairwise_scores)),
                float(np.median(pairwise_scores)),
                max(pairwise_scores),
            )
        )

    if args.output_report:
        write_report(
            Path(args.output_report),
            events_path,
            args.embedding_model,
            embedder.method,
            kept_rows,
            results,
            pairwise_scores,
        )
        print(f"report={args.output_report}")

    if failures:
        print(json.dumps({"failures": failures[:10]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
