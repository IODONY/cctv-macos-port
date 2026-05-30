#!/usr/bin/env python3
"""Sweep live best-crop similarity grouping thresholds."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from visual_grouping import VisualGroupRecord, group_records  # noqa: E402
from visual_reid import create_visual_embedder  # noqa: E402


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
            if line:
                rows.append(json.loads(line))
    return rows


def embed_events(rows: list[dict[str, object]], model_name: str):
    embedder = create_visual_embedder(model_name=model_name)
    records = []
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
        records.append(
            VisualGroupRecord(
                clip_id=str(row.get("clip_id") or ""),
                clip_path=str(row.get("clip_path") or ""),
                best_frame_path=str(image_path),
                embedding=embedding,
                metadata=dict(row),
            )
        )
    return records, failures, embedder.method


def format_sizes(report: dict[str, object]) -> str:
    return "[" + ", ".join(str(size) for size in report.get("group_sizes", [])) + "]"


def write_report(
    path: Path,
    source_path: Path,
    model_name: str,
    method: str,
    records: list[VisualGroupRecord],
    threshold_results: list[dict[str, object]],
    pairwise: dict[str, object],
    reciprocal_topn: int,
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
        f"- Records embedded: `{len(records)}`",
        f"- Embedding model: `{model_name}`",
        f"- Embedding method: `{method}`",
        f"- Reciprocal top-N: `{reciprocal_topn}`",
        "",
        "## Threshold Sweep",
        "",
        "| threshold | connected groups | connected sizes | reciprocal groups | reciprocal sizes | centroid groups | centroid sizes |",
        "| ---: | ---: | --- | ---: | --- | ---: | --- |",
    ]
    for result in threshold_results:
        lines.append(
            "| {threshold} | {connected_count} | {connected_sizes} | {reciprocal_count} | {reciprocal_sizes} | {centroid_count} | {centroid_sizes} |".format(
                **result
            )
        )
    lines.extend(
        [
            "",
            "## Pairwise Similarity",
            "",
            f"- Count: `{pairwise.get('count')}`",
            f"- Min: `{pairwise.get('min')}`",
            f"- Mean: `{pairwise.get('mean')}`",
            f"- Median: `{pairwise.get('median')}`",
            f"- Max: `{pairwise.get('max')}`",
            "",
            "## Interpretation",
            "",
            "- For a single-person smoke session, a lower group count is desirable.",
            "- `connected` shows whether saved crops are linked by any threshold path.",
            "- `reciprocal` is the intended final session-end grouping mode.",
            "- `centroid` approximates the online temporary grouping behavior.",
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
    parser.add_argument("--reciprocal-topn", type=int, default=3)
    parser.add_argument("--output-report", default="")
    args = parser.parse_args()

    events_path = resolve_events_path(args)
    rows = read_events(events_path)
    records, failures, embedding_method = embed_events(rows, args.embedding_model)

    threshold_results = []
    pairwise_summary = {"count": 0, "min": None, "mean": None, "median": None, "max": None}
    for threshold in args.thresholds:
        connected = group_records(records, method="connected", threshold=threshold, reciprocal_topn=args.reciprocal_topn)
        reciprocal = group_records(records, method="reciprocal", threshold=threshold, reciprocal_topn=args.reciprocal_topn)
        centroid = group_records(records, method="centroid", threshold=threshold, reciprocal_topn=args.reciprocal_topn)
        pairwise_summary = connected["pairwise"]
        result = {
            "threshold": f"{threshold:.2f}",
            "connected_count": connected["group_count"],
            "connected_sizes": format_sizes(connected),
            "reciprocal_count": reciprocal["group_count"],
            "reciprocal_sizes": format_sizes(reciprocal),
            "centroid_count": centroid["group_count"],
            "centroid_sizes": format_sizes(centroid),
        }
        threshold_results.append(result)
        print(
            "threshold={threshold} connected_groups={connected_count} connected_sizes={connected_sizes} "
            "reciprocal_groups={reciprocal_count} reciprocal_sizes={reciprocal_sizes} "
            "centroid_groups={centroid_count} centroid_sizes={centroid_sizes}".format(**result)
        )

    print(f"records={len(records)} failures={len(failures)} method={embedding_method}")
    if pairwise_summary.get("count"):
        print(
            "pairwise min={min} mean={mean} median={median} max={max}".format(
                **pairwise_summary,
            )
        )

    if args.output_report:
        write_report(
            Path(args.output_report),
            events_path,
            args.embedding_model,
            embedding_method,
            records,
            threshold_results,
            pairwise_summary,
            args.reciprocal_topn,
        )
        print(f"report={args.output_report}")

    if failures:
        print(json.dumps({"failures": failures[:10]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
