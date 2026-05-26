#!/usr/bin/env python3
"""Generate clip and pair-label manifests from data/labeld_clips/.

The existing folder name is intentionally supported as-is. The script never
renames, moves, or deletes video files.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import re
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLIP_ROOT = PROJECT_ROOT / "data" / "labeld_clips"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "labels"
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}
CLIP_NAME_RE = re.compile(r"^(cam_\d+)_(.+)\.(mp4|mov|avi|mkv|m4v)$", re.IGNORECASE)


@dataclass(frozen=True)
class ClipRecord:
    clip_id: str
    identity_id: str
    cam_id: str
    take_id: str
    clip_path: str
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


def parse_clip_filename(path: Path) -> tuple[str, str] | None:
    match = CLIP_NAME_RE.match(path.name)
    if not match:
        return None
    return match.group(1), match.group(2)


def iter_identity_dirs(root: Path, include_origin: bool) -> list[tuple[Path, str, str]]:
    identity_dirs: list[tuple[Path, str, str]] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if child.name == "Origin":
            if include_origin:
                for origin_child in sorted(child.iterdir(), key=lambda p: p.name):
                    if origin_child.is_dir():
                        identity_dirs.append(
                            (origin_child, f"origin_{origin_child.name}", "origin_raw_included")
                        )
            continue
        if child.name.startswith("person_"):
            identity_dirs.append((child, child.name, ""))
    return identity_dirs


def scan_clips(root: Path, include_origin: bool) -> tuple[list[ClipRecord], bool]:
    records: list[ClipRecord] = []
    origin_excluded = (root / "Origin").is_dir() and not include_origin
    for identity_dir, identity_id, identity_note in iter_identity_dirs(root, include_origin):
        for clip_path in sorted(identity_dir.iterdir(), key=lambda p: p.name):
            if not clip_path.is_file() or clip_path.suffix.lower() not in VIDEO_SUFFIXES:
                continue
            resolved = resolve_inside_project(clip_path)
            parsed = parse_clip_filename(resolved)
            if parsed is None:
                continue
            cam_id, take_id = parsed
            clip_id = f"{identity_id}_{cam_id}_{take_id}"
            records.append(
                ClipRecord(
                    clip_id=clip_id,
                    identity_id=identity_id,
                    cam_id=cam_id,
                    take_id=take_id,
                    clip_path=project_relative(resolved),
                    notes=identity_note,
                )
            )
    return records, origin_excluded


def generate_same_pairs(records: list[ClipRecord]) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    by_identity: dict[str, list[ClipRecord]] = {}
    for record in records:
        by_identity.setdefault(record.identity_id, []).append(record)

    for identity_id in sorted(by_identity):
        clips = sorted(by_identity[identity_id], key=lambda r: (r.cam_id, r.take_id, r.clip_id))
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
                    "notes": "",
                }
            )
    return pairs


def generate_negative_pairs(records: list[ClipRecord], max_negative_pairs: int) -> list[dict[str, str]]:
    candidates: list[tuple[bool, str, str, ClipRecord, ClipRecord]] = []
    sorted_records = sorted(records, key=lambda r: (r.identity_id, r.cam_id, r.take_id, r.clip_id))
    for left, right in itertools.combinations(sorted_records, 2):
        if left.identity_id == right.identity_id:
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
                "notes": "",
            }
        )
    return pairs


def write_clips_csv(path: Path, records: list[ClipRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["clip_id", "identity_id", "cam_id", "take_id", "clip_path", "notes"],
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
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for index, pair in enumerate(pairs, start=1):
            row = {"pair_id": f"pair_{index:06d}"}
            row.update(pair)
            writer.writerow(row)


def summarize(records: list[ClipRecord], pairs: list[dict[str, str]], origin_excluded: bool) -> None:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.identity_id] = counts.get(record.identity_id, 0) + 1
    print("Detected identity folders:")
    for identity_id in sorted(counts):
        print(f"- {identity_id}: {counts[identity_id]} clips")
    print(f"Total clips: {len(records)}")
    print(f"Total pairs: {len(pairs)}")
    print(f"Origin excluded: {origin_excluded}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate labeled clip manifests.")
    parser.add_argument("--root", default=project_relative(DEFAULT_CLIP_ROOT))
    parser.add_argument("--out-dir", default=project_relative(DEFAULT_OUT_DIR))
    parser.add_argument("--max-negative-pairs", type=int, default=100)
    parser.add_argument("--include-origin", action="store_true")
    args = parser.parse_args()

    clip_root = resolve_inside_project(args.root)
    out_dir = resolve_inside_project(args.out_dir)
    if not clip_root.is_dir():
        raise SystemExit(f"Clip root does not exist: {clip_root}")

    records, origin_excluded = scan_clips(clip_root, args.include_origin)
    same_pairs = generate_same_pairs(records)
    negative_pairs = generate_negative_pairs(records, args.max_negative_pairs)
    pairs = same_pairs + negative_pairs

    clips_path = out_dir / "clips.csv"
    pairs_path = out_dir / "pair_labels.csv"
    write_clips_csv(clips_path, records)
    write_pairs_csv(pairs_path, pairs)

    print(f"Wrote {project_relative(clips_path)}")
    print(f"Wrote {project_relative(pairs_path)}")
    summarize(records, pairs, origin_excluded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
