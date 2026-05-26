#!/usr/bin/env python3
"""Generate clip and pair-label manifests from labeled local clip folders.

The preferred source root is data/labeled_clips/. The older misspelled
data/labeld_clips/ root is still supported when the preferred root is absent.
This script never renames, moves, or deletes video files.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREFERRED_CLIP_ROOT = PROJECT_ROOT / "data" / "labeled_clips"
LEGACY_CLIP_ROOT = PROJECT_ROOT / "data" / "labeld_clips"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "labels"
DEFAULT_K = 9
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}
CAM_STEM_RE = re.compile(r"^(cam_\d+)(?:_(.+))?$", re.IGNORECASE)
IDENTITY_DIR_RE = re.compile(r"^person[_-]\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class ClipRecord:
    clip_id: str
    dataset_id: str
    identity_id: str
    cam_id: str
    take_id: str
    event_id: str
    clip_path: str
    layout_type: str
    notes: str = ""


@dataclass(frozen=True)
class IdentityDir:
    path: Path
    dataset_id: str
    identity_id: str
    layout_type: str
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


def default_clip_root() -> Path:
    if PREFERRED_CLIP_ROOT.is_dir():
        return PREFERRED_CLIP_ROOT
    return LEGACY_CLIP_ROOT


def sanitize_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned.lower() or "unknown"


def is_identity_dir(path: Path) -> bool:
    return path.is_dir() and bool(IDENTITY_DIR_RE.match(path.name))


def parse_clip_filename(path: Path) -> tuple[str, str, str, str]:
    """Return cam_id, take_id, event_id, and a filename-pattern label."""
    stem = path.stem
    match = CAM_STEM_RE.match(stem)
    if not match:
        return "unknown", stem, stem, "unparsed_filename"

    cam_id = match.group(1).lower()
    remainder = match.group(2) or ""
    if not remainder:
        return cam_id, "", "", "cam_only"
    if remainder.isdigit():
        return cam_id, remainder, "", "take_index"

    event_number = re.search(r"(?:event|even)[_-]?(\d+)", remainder, re.IGNORECASE)
    if event_number:
        return cam_id, event_number.group(1), remainder, "event_id"

    trailing_number = re.search(r"(\d+)$", remainder)
    take_id = trailing_number.group(1) if trailing_number else remainder
    return cam_id, take_id, stem, "uncertain_event_id"


def make_clip_id(record: ClipRecord, seen: set[str]) -> str:
    base_parts = []
    if record.dataset_id != "root":
        base_parts.append(record.dataset_id)
    base_parts.extend([record.identity_id, record.cam_id])
    base_parts.append(record.event_id or record.take_id or Path(record.clip_path).stem)
    base = sanitize_id("_".join(part for part in base_parts if part))
    clip_id = base
    suffix = 2
    while clip_id in seen:
        clip_id = f"{base}_{suffix}"
        suffix += 1
    seen.add(clip_id)
    return clip_id


def iter_identity_dirs(root: Path, include_origin: bool) -> list[IdentityDir]:
    identity_dirs: list[IdentityDir] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if child.name == "Origin":
            if include_origin:
                for origin_child in sorted(child.iterdir(), key=lambda p: p.name):
                    if origin_child.is_dir():
                        identity_dirs.append(
                            IdentityDir(
                                path=origin_child,
                                dataset_id="origin",
                                identity_id=f"origin_{origin_child.name}",
                                layout_type="origin_raw",
                                notes="origin_raw_included",
                            )
                        )
            continue
        if is_identity_dir(child):
            identity_dirs.append(
                IdentityDir(
                    path=child,
                    dataset_id="root",
                    identity_id=child.name,
                    layout_type="direct_identity",
                )
            )
            continue
        for nested in sorted(child.iterdir(), key=lambda p: p.name):
            if nested.name == "Origin":
                continue
            if is_identity_dir(nested):
                identity_dirs.append(
                    IdentityDir(
                        path=nested,
                        dataset_id=child.name,
                        identity_id=nested.name,
                        layout_type="nested_dataset_identity",
                    )
                )
    return identity_dirs


def origin_dirs(root: Path) -> list[Path]:
    origins = []
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if child.is_dir() and child.name == "Origin":
            origins.append(child)
        if child.is_dir() and child.name != "Origin":
            nested_origin = child / "Origin"
            if nested_origin.is_dir():
                origins.append(nested_origin)
    return origins


def scan_clips(root: Path, include_origin: bool) -> tuple[list[ClipRecord], bool, Counter[str]]:
    records: list[ClipRecord] = []
    patterns: Counter[str] = Counter()
    origin_excluded = bool(origin_dirs(root)) and not include_origin
    seen_clip_ids: set[str] = set()

    for identity_dir in iter_identity_dirs(root, include_origin):
        for clip_path in sorted(identity_dir.path.iterdir(), key=lambda p: p.name):
            if not clip_path.is_file() or clip_path.suffix.lower() not in VIDEO_SUFFIXES:
                continue
            resolved = resolve_inside_project(clip_path)
            cam_id, take_id, event_id, pattern = parse_clip_filename(resolved)
            patterns[pattern] += 1
            notes = ",".join(part for part in (identity_dir.notes, pattern) if part)
            provisional = ClipRecord(
                clip_id="",
                dataset_id=identity_dir.dataset_id,
                identity_id=identity_dir.identity_id,
                cam_id=cam_id,
                take_id=take_id,
                event_id=event_id,
                clip_path=project_relative(resolved),
                layout_type=identity_dir.layout_type,
                notes=notes,
            )
            records.append(
                ClipRecord(
                    clip_id=make_clip_id(provisional, seen_clip_ids),
                    dataset_id=provisional.dataset_id,
                    identity_id=provisional.identity_id,
                    cam_id=provisional.cam_id,
                    take_id=provisional.take_id,
                    event_id=provisional.event_id,
                    clip_path=provisional.clip_path,
                    layout_type=provisional.layout_type,
                    notes=provisional.notes,
                )
            )
    return records, origin_excluded, patterns


def identity_key(record: ClipRecord) -> tuple[str, str]:
    return record.dataset_id, record.identity_id


def generate_same_pairs(records: list[ClipRecord]) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    by_identity: dict[tuple[str, str], list[ClipRecord]] = {}
    for record in records:
        by_identity.setdefault(identity_key(record), []).append(record)

    for key in sorted(by_identity):
        clips = sorted(by_identity[key], key=lambda r: (r.cam_id, r.take_id, r.event_id, r.clip_id))
        combos = list(itertools.combinations(clips, 2))
        combos.sort(key=lambda pair: (pair[0].cam_id == pair[1].cam_id, pair[0].clip_id, pair[1].clip_id))
        for left, right in combos:
            pair_type = "same_cross_camera" if left.cam_id != right.cam_id else "same_same_camera"
            pairs.append(
                {
                    "clip_id_a": left.clip_id,
                    "clip_id_b": right.clip_id,
                    "identity_id_a": left.identity_id,
                    "identity_id_b": right.identity_id,
                    "label": "1",
                    "pair_type": pair_type,
                    "notes": f"dataset={left.dataset_id}",
                }
            )
    return pairs


def generate_negative_pairs(records: list[ClipRecord], max_negative_pairs: int) -> list[dict[str, str]]:
    candidates: list[tuple[bool, str, str, ClipRecord, ClipRecord]] = []
    sorted_records = sorted(records, key=lambda r: (r.dataset_id, r.identity_id, r.cam_id, r.take_id, r.clip_id))
    for left, right in itertools.combinations(sorted_records, 2):
        if identity_key(left) == identity_key(right):
            continue
        same_camera = left.cam_id == right.cam_id
        candidates.append((not same_camera, left.clip_id, right.clip_id, left, right))

    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    pairs: list[dict[str, str]] = []
    for _, _, _, left, right in candidates[: max(0, max_negative_pairs)]:
        pair_type = "hard_negative_same_camera" if left.cam_id == right.cam_id else "negative_cross_camera"
        pairs.append(
            {
                "clip_id_a": left.clip_id,
                "clip_id_b": right.clip_id,
                "identity_id_a": left.identity_id,
                "identity_id_b": right.identity_id,
                "label": "0",
                "pair_type": pair_type,
                "notes": f"datasets={left.dataset_id},{right.dataset_id}",
            }
        )
    return pairs


def write_clips_csv(path: Path, records: list[ClipRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "clip_id",
                "dataset_id",
                "identity_id",
                "cam_id",
                "take_id",
                "event_id",
                "clip_path",
                "layout_type",
                "notes",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)


def write_pairs_csv(path: Path, pairs: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "pair_id",
            "clip_id_a",
            "clip_id_b",
            "identity_id_a",
            "identity_id_b",
            "label",
            "pair_type",
            "notes",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for index, pair in enumerate(pairs, start=1):
            row = {"pair_id": f"pair_{index:06d}"}
            row.update(pair)
            writer.writerow(row)


def grouped_counts(records: list[ClipRecord]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for record in records:
        counts[identity_key(record)] = counts.get(identity_key(record), 0) + 1
    return counts


def write_manifest_report(
    path: Path,
    *,
    root: Path,
    records: list[ClipRecord],
    pairs: list[dict[str, str]],
    origin_excluded: bool,
    patterns: Counter[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataset_counts = Counter(record.dataset_id for record in records)
    layout_counts = Counter(record.layout_type for record in records)

    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Clip Manifest Report\n\n")
        fh.write(f"- Source root: `{project_relative(root)}`\n")
        fh.write(f"- Preferred root exists: `{PREFERRED_CLIP_ROOT.is_dir()}`\n")
        fh.write(f"- Legacy root exists: `{LEGACY_CLIP_ROOT.is_dir()}`\n")
        fh.write(f"- Origin excluded: `{origin_excluded}`\n")
        fh.write(f"- Clip count: `{len(records)}`\n")
        fh.write(f"- Pair count: `{len(pairs)}`\n\n")

        fh.write("## Datasets\n\n")
        for dataset_id, count in sorted(dataset_counts.items()):
            fh.write(f"- `{dataset_id}`: `{count}` clips\n")

        fh.write("\n## Layout Types\n\n")
        for layout_type, count in sorted(layout_counts.items()):
            fh.write(f"- `{layout_type}`: `{count}` clips\n")

        fh.write("\n## Filename Patterns\n\n")
        for pattern, count in sorted(patterns.items()):
            fh.write(f"- `{pattern}`: `{count}` clips\n")


def write_structure_report(
    path: Path,
    *,
    root: Path,
    records: list[ClipRecord],
    origin_excluded: bool,
    patterns: Counter[str],
    k: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = grouped_counts(records)
    dataset_dirs = sorted({record.dataset_id for record in records})

    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Labeled Clip Structure Report\n\n")
        fh.write(f"- Inspected source root: `{project_relative(root)}`\n")
        fh.write(f"- Preferred `data/labeled_clips/` exists: `{PREFERRED_CLIP_ROOT.is_dir()}`\n")
        fh.write(f"- Legacy `data/labeld_clips/` exists: `{LEGACY_CLIP_ROOT.is_dir()}`\n")
        fh.write(f"- Origin excluded: `{origin_excluded}`\n")
        fh.write(f"- Total labeled clips: `{len(records)}`\n")
        fh.write(f"- Top-K target: `{k}`\n\n")

        fh.write("## Detected Dataset Folders\n\n")
        for dataset_id in dataset_dirs:
            label = "direct root identities" if dataset_id == "root" else dataset_id
            fh.write(f"- `{label}`\n")

        fh.write("\n## Detected Filename Patterns\n\n")
        for pattern, count in sorted(patterns.items()):
            fh.write(f"- `{pattern}`: `{count}` clips\n")

        fh.write("\n## Identity Clip Counts\n\n")
        fh.write(
            "| dataset_id | identity_id | clips | available_positive_count | "
            f"max_possible_own_count_at_{k} | normalized_own_recall_at_{k} | "
            f"additional_clips_needed_for_top_{k}_own | enough_same_identity_for_top_{k} | layout_type |\n"
        )
        fh.write("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |\n")
        layout_by_identity = {
            identity_key(record): record.layout_type
            for record in records
        }
        for key, count in sorted(counts.items()):
            available_positive = max(0, count - 1)
            max_possible = min(k, available_positive)
            normalized = 1.0 if max_possible > 0 else 0.0
            additional_needed = max(0, k - available_positive)
            enough = available_positive >= k
            fh.write(
                f"| {key[0]} | {key[1]} | {count} | {available_positive} | "
                f"{max_possible} | {normalized:.4f} | {additional_needed} | {enough} | "
                f"{layout_by_identity.get(key, '')} |\n"
            )

        fh.write("\n## Interpretation\n\n")
        fh.write(
            f"- `available_positive_count` is the same-identity gallery count for leave-one-out evaluation.\n"
        )
        fh.write(
            f"- `max_possible_own_count_at_{k}` is capped by both `{k}` and available same-identity gallery clips.\n"
        )
        fh.write(
            "- A low own-count is not automatically an algorithm failure when the same-identity gallery is too small.\n"
        )
        fh.write(
            f"- `additional_clips_needed_for_top_{k}_own` counts extra same-identity gallery clips needed per query.\n"
        )


def summarize(records: list[ClipRecord], pairs: list[dict[str, str]], origin_excluded: bool) -> None:
    counts = grouped_counts(records)
    print("Detected identity folders:")
    for (dataset_id, identity_id), count in sorted(counts.items()):
        print(f"- {dataset_id}/{identity_id}: {count} clips")
    print(f"Total clips: {len(records)}")
    print(f"Total pairs: {len(pairs)}")
    print(f"Origin excluded: {origin_excluded}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate labeled clip manifests.")
    parser.add_argument("--root", default=project_relative(default_clip_root()))
    parser.add_argument("--out-dir", default=project_relative(DEFAULT_OUT_DIR))
    parser.add_argument("--max-negative-pairs", type=int, default=100)
    parser.add_argument("--include-origin", action="store_true")
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--manifest-report", default="docs/reports/CLIP_MANIFEST_REPORT.md")
    parser.add_argument("--structure-report", default="docs/reports/LABELED_CLIP_STRUCTURE_REPORT.md")
    args = parser.parse_args()

    clip_root = resolve_inside_project(args.root)
    out_dir = resolve_inside_project(args.out_dir)
    if not clip_root.is_dir():
        raise SystemExit(f"Clip root does not exist: {clip_root}")

    records, origin_excluded, patterns = scan_clips(clip_root, args.include_origin)
    same_pairs = generate_same_pairs(records)
    negative_pairs = generate_negative_pairs(records, args.max_negative_pairs)
    pairs = same_pairs + negative_pairs

    clips_path = out_dir / "clips.csv"
    pairs_path = out_dir / "pair_labels.csv"
    write_clips_csv(clips_path, records)
    write_pairs_csv(pairs_path, pairs)
    write_manifest_report(
        resolve_inside_project(args.manifest_report),
        root=clip_root,
        records=records,
        pairs=pairs,
        origin_excluded=origin_excluded,
        patterns=patterns,
    )
    write_structure_report(
        resolve_inside_project(args.structure_report),
        root=clip_root,
        records=records,
        origin_excluded=origin_excluded,
        patterns=patterns,
        k=args.k,
    )

    print(f"Wrote {project_relative(clips_path)}")
    print(f"Wrote {project_relative(pairs_path)}")
    print(f"Wrote {args.manifest_report}")
    print(f"Wrote {args.structure_report}")
    summarize(records, pairs, origin_excluded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
