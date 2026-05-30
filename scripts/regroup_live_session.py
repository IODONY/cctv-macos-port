#!/usr/bin/env python3
"""Regroup saved live Top-K gallery clips by appearance similarity."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from live_session_grouping import regroup_live_session  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", default="", help="Session id under logs/topk_live/<session>.")
    parser.add_argument("--events-path", default="", help="Explicit gallery_events.jsonl path.")
    parser.add_argument("--embedding-model", default="osnet_x0_25")
    parser.add_argument("--method", choices=("connected", "reciprocal"), default="reciprocal")
    parser.add_argument("--threshold", type=float, default=0.65)
    parser.add_argument("--reciprocal-topn", type=int, default=8)
    parser.add_argument("--export-mode", choices=("symlink", "copy", "path"), default="symlink")
    parser.add_argument("--snapshot-root", default="snapshots/live_topk")
    parser.add_argument("--output-subdir", default="similarity_groups_merged")
    parser.add_argument("--write-report", default="")
    args = parser.parse_args()

    events_path = Path(args.events_path).expanduser().resolve() if args.events_path else None
    report_path = Path(args.write_report).expanduser().resolve() if args.write_report else None
    payload = regroup_live_session(
        session_id=args.session or None,
        events_path=events_path,
        embedding_model=args.embedding_model,
        method=args.method,
        threshold=args.threshold,
        reciprocal_topn=args.reciprocal_topn,
        export_mode=args.export_mode,
        snapshot_root=(PROJECT_ROOT / args.snapshot_root).resolve()
        if not Path(args.snapshot_root).expanduser().is_absolute()
        else Path(args.snapshot_root).expanduser().resolve(),
        output_subdir=args.output_subdir,
        write_report=report_path,
    )
    grouping = payload["grouping"]
    print(
        "REGROUP_OK "
        f"session={payload['session_id']} "
        f"records={grouping['record_count']} "
        f"groups={grouping['group_count']} "
        f"sizes={grouping['group_sizes']} "
        f"method={grouping['method']} "
        f"threshold={grouping['threshold']} "
        f"output={payload['output_dir']} "
        f"summary={payload['summary_path']}"
    )
    if payload.get("report_path"):
        print(f"REPORT {payload['report_path']}")
    if payload.get("failures"):
        print(f"FAILURES {len(payload['failures'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
