#!/usr/bin/env python3
"""Regroup finished live gallery clips after a session ends."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

import cv2

from visual_grouping import VisualGroupRecord, group_records
from visual_reid import create_visual_embedder


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def sanitize_id(value: object) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("_")
    return text or "unknown"


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def read_jsonl(path: Path) -> list[dict[str, object]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def export_asset(source_path: str, destination: Path, mode: str, path_txt_name: str) -> str:
    source = Path(str(source_path or "")).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    path_txt = destination.parent / path_txt_name
    path_txt.write_text(str(source), encoding="utf-8")

    if mode == "path" or not str(source_path or "").strip() or not source.exists():
        return str(path_txt.resolve()).replace("\\", "/")

    if destination.exists() or destination.is_symlink():
        destination.unlink()

    if mode == "copy":
        shutil.copy2(source, destination)
    else:
        try:
            relative_source = os.path.relpath(source.resolve(), start=destination.parent.resolve())
            destination.symlink_to(relative_source)
        except OSError:
            shutil.copy2(source, destination)
    return str((destination.parent.resolve() / destination.name)).replace("\\", "/")


def resolve_events_path(session_id: str | None = None, events_path: Path | None = None) -> tuple[str, Path]:
    if events_path is not None:
        resolved = events_path.expanduser().resolve()
        session = str(session_id or resolved.parent.name)
        return session, resolved
    if not session_id:
        raise ValueError("session_id or events_path is required")
    session = sanitize_id(session_id)
    return session, PROJECT_ROOT / "logs" / "topk_live" / session / "gallery_events.jsonl"


def embed_gallery_events(
    rows: list[dict[str, object]],
    embedding_model: str,
) -> tuple[list[VisualGroupRecord], list[dict[str, object]], str]:
    embedder = create_visual_embedder(model_name=embedding_model)
    records: list[VisualGroupRecord] = []
    failures: list[dict[str, object]] = []

    for row in rows:
        clip_id = str(row.get("clip_id") or "")
        best_frame_path = Path(str(row.get("best_frame_path") or "")).expanduser()
        if not best_frame_path.is_absolute():
            best_frame_path = (PROJECT_ROOT / best_frame_path).resolve()
        image = cv2.imread(str(best_frame_path))
        if image is None:
            failures.append(
                {
                    "clip_id": clip_id,
                    "reason": "best_frame_read_failed",
                    "best_frame_path": str(best_frame_path),
                }
            )
            continue

        embedding, method = embedder.embed_bgr(image)
        if embedding is None:
            failures.append(
                {
                    "clip_id": clip_id,
                    "reason": "embedding_failed",
                    "best_frame_path": str(best_frame_path),
                }
            )
            continue

        metadata = dict(row)
        metadata["regroup_embedding_method"] = method
        records.append(
            VisualGroupRecord(
                clip_id=clip_id,
                clip_path=str(row.get("clip_path") or ""),
                best_frame_path=str(best_frame_path),
                embedding=embedding,
                metadata=metadata,
            )
        )
    return records, failures, str(getattr(embedder, "method", embedding_model))


def export_merged_groups(
    group_report: dict[str, object],
    output_root: Path,
    export_mode: str,
) -> None:
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    for group in group_report.get("groups", []):
        group_label = sanitize_id(group.get("group_label", "group"))
        group_dir = output_root / group_label
        group_dir.mkdir(parents=True, exist_ok=True)
        exported_members = []
        for member in group.get("members", []):
            clip_id = sanitize_id(member.get("clip_id", "clip"))
            clip_path = str(member.get("clip_path") or "")
            best_frame_path = str(member.get("best_frame_path") or "")
            clip_suffix = Path(clip_path).suffix or ".mp4"
            best_suffix = Path(best_frame_path).suffix or ".jpg"
            exported = dict(member)
            exported["exported_clip"] = export_asset(
                clip_path,
                group_dir / f"{clip_id}{clip_suffix}",
                export_mode,
                f"{clip_id}_clip_path.txt",
            )
            exported["exported_best_frame"] = export_asset(
                best_frame_path,
                group_dir / f"{clip_id}_best{best_suffix}",
                export_mode,
                f"{clip_id}_best_path.txt",
            )
            write_json(group_dir / f"{clip_id}.json", exported)
            exported_members.append(exported)

        group_payload = dict(group)
        group_payload["members"] = exported_members
        write_json(group_dir / "group.json", group_payload)


def write_markdown_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    grouping = payload.get("grouping", {})
    lines = [
        "# Live Session Regroup Report",
        "",
        "This report is generated from saved live gallery clips and best ReID crops. It does not run cameras.",
        "",
        "## Summary",
        "",
        f"- Session: `{payload.get('session_id')}`",
        f"- Events: `{payload.get('events_path')}`",
        f"- Output: `{payload.get('output_dir')}`",
        f"- Embedding model: `{payload.get('embedding_model')}`",
        f"- Embedding method: `{payload.get('embedding_method')}`",
        f"- Method: `{grouping.get('method')}`",
        f"- Threshold: `{grouping.get('threshold')}`",
        f"- Reciprocal top-N: `{grouping.get('reciprocal_topn')}`",
        f"- Records grouped: `{grouping.get('record_count')}`",
        f"- Group count: `{grouping.get('group_count')}`",
        f"- Group sizes: `{grouping.get('group_sizes')}`",
        f"- Failures: `{len(payload.get('failures', []))}`",
        "",
        "## Groups",
        "",
        "| group | clips | pairwise min | pairwise mean | pairwise max | members |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for group in grouping.get("groups", []):
        pairwise = group.get("pairwise", {})
        members = [str(member.get("clip_id")) for member in group.get("members", [])]
        lines.append(
            "| {label} | {count} | {min_score} | {mean_score} | {max_score} | {members} |".format(
                label=group.get("group_label"),
                count=group.get("count"),
                min_score=pairwise.get("min"),
                mean_score=pairwise.get("mean"),
                max_score=pairwise.get("max"),
                members=", ".join(members[:8]) + ("..." if len(members) > 8 else ""),
            )
        )
    if payload.get("failures"):
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(f"- `{failure.get('clip_id')}`: {failure.get('reason')} `{failure.get('best_frame_path')}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def regroup_live_session(
    session_id: str | None = None,
    events_path: Path | None = None,
    embedding_model: str = "osnet_x0_25",
    method: str = "reciprocal",
    threshold: float = 0.60,
    reciprocal_topn: int = 3,
    export_mode: str = "symlink",
    snapshot_root: Path | None = None,
    output_subdir: str = "similarity_groups_merged",
    write_report: Path | None = None,
) -> dict[str, object]:
    session, events = resolve_events_path(session_id=session_id, events_path=events_path)
    rows = read_jsonl(events)
    records, failures, embedding_method = embed_gallery_events(rows, embedding_model)
    grouping = group_records(records, method=method, threshold=threshold, reciprocal_topn=reciprocal_topn)

    root = (snapshot_root or (PROJECT_ROOT / "snapshots" / "live_topk")).expanduser().resolve()
    output_root = root / sanitize_id(session) / sanitize_id(output_subdir)
    export_merged_groups(grouping, output_root, export_mode)

    payload = {
        "session_id": session,
        "events_path": project_relative(events),
        "output_dir": project_relative(output_root),
        "embedding_model": embedding_model,
        "embedding_method": embedding_method,
        "export_mode": export_mode,
        "source_event_count": len(rows),
        "failures": failures,
        "grouping": grouping,
    }

    summary_path = PROJECT_ROOT / "logs" / "topk_live" / sanitize_id(session) / "merged_similarity_groups.json"
    write_json(summary_path, payload)
    payload["summary_path"] = project_relative(summary_path)
    if write_report is not None:
        report_path = write_report.expanduser().resolve()
        write_markdown_report(report_path, payload)
        payload["report_path"] = project_relative(report_path)
    return payload
