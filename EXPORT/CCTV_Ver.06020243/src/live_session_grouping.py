#!/usr/bin/env python3
"""Regroup finished live gallery clips after a session ends."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

import cv2
import numpy as np

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


def resolve_image_path(path_value: str) -> Path:
    image_path = Path(str(path_value or "")).expanduser()
    if not image_path.is_absolute():
        image_path = (PROJECT_ROOT / image_path).resolve()
    return image_path


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


def clip_sort_key(member: dict[str, object]) -> tuple[float, str]:
    metadata = member.get("metadata") if isinstance(member.get("metadata"), dict) else {}
    created_at = metadata.get("created_at") if isinstance(metadata, dict) else None
    try:
        timestamp = float(created_at)
    except (TypeError, ValueError):
        event_text = str(metadata.get("event_id") or member.get("clip_id") or "")
        digits = re.sub(r"\D+", "", event_text)
        timestamp = float(digits) if digits else 0.0
    return timestamp, str(member.get("clip_id") or "")


def create_clip_writer(path: Path, fps: float, frame_size: tuple[int, int]):
    path.parent.mkdir(parents=True, exist_ok=True)
    for codec in ("mp4v", "avc1", "H264", "MJPG"):
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*codec), fps, frame_size)
        if writer.isOpened():
            return writer, codec
        writer.release()
    return None, ""


def merge_group_clips(
    group_label: str,
    members: list[dict[str, object]],
    group_dir: Path,
) -> dict[str, object]:
    ordered_members = sorted(members, key=clip_sort_key)
    output_path = group_dir / f"{sanitize_id(group_label)}_merged.mp4"
    source_clip_ids: list[str] = []
    failures: list[dict[str, object]] = []
    writer = None
    codec = ""
    output_size: tuple[int, int] | None = None
    output_fps = 25.0
    frame_count = 0

    try:
        for member in ordered_members:
            clip_id = str(member.get("clip_id") or "")
            source_path = Path(str(member.get("clip_path") or "")).expanduser()
            if not source_path.is_absolute():
                source_path = (PROJECT_ROOT / source_path).resolve()
            cap = cv2.VideoCapture(str(source_path))
            if not cap.isOpened():
                failures.append({"clip_id": clip_id, "reason": "open_failed", "clip_path": str(source_path)})
                continue
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            if writer is None:
                output_fps = fps if fps > 1.0 else 25.0
                output_size = (width, height) if width > 0 and height > 0 else None
                if output_size is None:
                    failures.append({"clip_id": clip_id, "reason": "invalid_frame_size", "clip_path": str(source_path)})
                    cap.release()
                    continue
                writer, codec = create_clip_writer(output_path, output_fps, output_size)
                if writer is None:
                    cap.release()
                    failures.append({"clip_id": clip_id, "reason": "writer_open_failed", "clip_path": str(output_path)})
                    break

            written_for_clip = 0
            while True:
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                if output_size is not None and (frame.shape[1], frame.shape[0]) != output_size:
                    frame = cv2.resize(frame, output_size, interpolation=cv2.INTER_AREA)
                writer.write(frame)
                frame_count += 1
                written_for_clip += 1
            cap.release()
            if written_for_clip > 0:
                source_clip_ids.append(clip_id)
            else:
                failures.append({"clip_id": clip_id, "reason": "no_frames_read", "clip_path": str(source_path)})
    finally:
        if writer is not None:
            writer.release()

    if frame_count <= 0:
        if output_path.exists():
            output_path.unlink()
        payload = {
            "created": False,
            "reason": "no_frames_written",
            "failures": failures,
            "source_clip_ids": source_clip_ids,
        }
        write_json(group_dir / f"{sanitize_id(group_label)}_merged.json", payload)
        return payload

    payload = {
        "created": True,
        "clip_path": str(output_path.resolve()).replace("\\", "/"),
        "codec": codec,
        "fps": round(float(output_fps), 3),
        "frame_count": int(frame_count),
        "duration_seconds": round(float(frame_count) / max(1.0, float(output_fps)), 3),
        "source_clip_count": len(source_clip_ids),
        "source_clip_ids": source_clip_ids,
        "failures": failures,
    }
    write_json(group_dir / f"{sanitize_id(group_label)}_merged.json", payload)
    return payload


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
    embedding_aggregation: str = "topn",
) -> tuple[list[VisualGroupRecord], list[dict[str, object]], str]:
    embedder = create_visual_embedder(model_name=embedding_model)
    records: list[VisualGroupRecord] = []
    failures: list[dict[str, object]] = []
    normalized_aggregation = str(embedding_aggregation or "topn").strip().lower()

    for row in rows:
        clip_id = str(row.get("clip_id") or "")
        best_frame_path = resolve_image_path(str(row.get("best_frame_path") or ""))
        crop_paths = [best_frame_path]
        if normalized_aggregation == "topn":
            top_crop_paths = [
                resolve_image_path(str(path))
                for path in row.get("top_crop_paths", []) or []
                if str(path or "").strip()
            ]
            if top_crop_paths:
                crop_paths = top_crop_paths

        crop_embeddings = []
        method = str(getattr(embedder, "method", embedding_model))
        failed_paths = []
        for crop_path in crop_paths:
            image = cv2.imread(str(crop_path))
            if image is None:
                failed_paths.append(str(crop_path))
                continue
            embedding, method = embedder.embed_bgr(image)
            if embedding is not None:
                crop_embeddings.append(embedding)

        if not crop_embeddings:
            failures.append(
                {
                    "clip_id": clip_id,
                    "reason": "crop_embedding_failed",
                    "best_frame_path": str(best_frame_path),
                    "attempted_crop_paths": [str(path) for path in crop_paths],
                    "failed_read_paths": failed_paths,
                }
            )
            continue

        if len(crop_embeddings) == 1:
            embedding = crop_embeddings[0]
        else:
            embedding = np.vstack(crop_embeddings).mean(axis=0)
        prototype_embeddings = np.vstack(crop_embeddings).astype(np.float32)

        metadata = dict(row)
        metadata["regroup_embedding_method"] = method
        metadata["regroup_embedding_aggregation"] = (
            f"prototype_mean_top_{len(crop_embeddings)}" if len(crop_embeddings) > 1 else "single_best"
        )
        metadata["regroup_prototype_count"] = int(prototype_embeddings.shape[0])
        records.append(
            VisualGroupRecord(
                clip_id=clip_id,
                clip_path=str(row.get("clip_path") or ""),
                best_frame_path=str(best_frame_path),
                embedding=embedding,
                prototype_embeddings=prototype_embeddings,
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
        group_payload["merged_clip"] = merge_group_clips(group_label, exported_members, group_dir)
        write_json(group_dir / "group.json", group_payload)


def write_markdown_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    grouping = payload.get("grouping", {})
    lines = [
        "# Live Session Regroup Report",
        "",
        "This report is generated from saved live gallery clips and saved ReID crops. It does not run cameras.",
        "",
        "## Summary",
        "",
        f"- Session: `{payload.get('session_id')}`",
        f"- Events: `{payload.get('events_path')}`",
        f"- Output: `{payload.get('output_dir')}`",
        f"- Embedding model: `{payload.get('embedding_model')}`",
        f"- Embedding method: `{payload.get('embedding_method')}`",
        f"- Embedding aggregation: `{payload.get('embedding_aggregation')}`",
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
    embedding_aggregation: str = "topn",
    method: str = "reciprocal",
    threshold: float = 0.65,
    reciprocal_topn: int = 4,
    export_mode: str = "symlink",
    snapshot_root: Path | None = None,
    output_subdir: str = "similarity_groups_merged",
    write_report: Path | None = None,
) -> dict[str, object]:
    session, events = resolve_events_path(session_id=session_id, events_path=events_path)
    rows = read_jsonl(events)
    records, failures, embedding_method = embed_gallery_events(rows, embedding_model, embedding_aggregation)
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
        "embedding_aggregation": embedding_aggregation,
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
