#!/usr/bin/env python3
"""Appearance embedding grouping helpers for live ReID clips."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Iterable

import numpy as np

from visual_reid import normalize_vector


@dataclass
class VisualGroupRecord:
    clip_id: str
    clip_path: str
    best_frame_path: str
    embedding: np.ndarray
    prototype_embeddings: np.ndarray | None = None
    metadata: dict[str, object] = field(default_factory=dict)


def _safe_embedding(record: VisualGroupRecord) -> np.ndarray | None:
    return normalize_vector(record.embedding)


def _safe_prototypes(record: VisualGroupRecord) -> np.ndarray | None:
    if record.prototype_embeddings is None:
        embedding = _safe_embedding(record)
        return None if embedding is None else embedding.reshape(1, -1)
    array = np.asarray(record.prototype_embeddings, dtype=np.float32)
    if array.ndim == 1:
        normalized = normalize_vector(array)
        return None if normalized is None else normalized.reshape(1, -1)
    rows = []
    for row in array:
        normalized = normalize_vector(row)
        if normalized is not None:
            rows.append(normalized)
    if not rows:
        return None
    return np.vstack(rows).astype(np.float32)


def cosine_similarity_matrix(records: list[VisualGroupRecord]) -> np.ndarray:
    if not records:
        return np.zeros((0, 0), dtype=np.float32)
    prototypes = []
    for record in records:
        matrix = _safe_prototypes(record)
        if matrix is None:
            raise ValueError(f"record has invalid embedding: {record.clip_id}")
        prototypes.append(matrix)
    scores = np.eye(len(records), dtype=np.float32)
    for left in range(len(records)):
        for right in range(left + 1, len(records)):
            pair_scores = prototypes[left] @ prototypes[right].T
            score = float(np.max(pair_scores)) if pair_scores.size else 0.0
            scores[left, right] = score
            scores[right, left] = score
    return np.clip(scores, -1.0, 1.0)


def _connected_components_from_edges(size: int, edges: Iterable[tuple[int, int]]) -> list[list[int]]:
    parent = list(range(size))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for left, right in edges:
        union(left, right)

    groups: dict[int, list[int]] = {}
    for index in range(size):
        groups.setdefault(find(index), []).append(index)
    return sorted(groups.values(), key=lambda group: (-len(group), group[0]))


def connected_groups(scores: np.ndarray, threshold: float) -> list[list[int]]:
    size = int(scores.shape[0])
    edges = []
    for left in range(size):
        for right in range(left + 1, size):
            if float(scores[left, right]) >= float(threshold):
                edges.append((left, right))
    return _connected_components_from_edges(size, edges)


def reciprocal_groups(scores: np.ndarray, threshold: float, reciprocal_topn: int = 5) -> list[list[int]]:
    size = int(scores.shape[0])
    if size <= 1:
        return [[index] for index in range(size)]

    topn = max(1, int(reciprocal_topn))
    top_neighbors: list[set[int]] = []
    for index in range(size):
        order = [candidate for candidate in np.argsort(scores[index])[::-1].tolist() if candidate != index]
        top_neighbors.append(set(order[:topn]))

    edges = []
    for left in range(size):
        for right in range(left + 1, size):
            if float(scores[left, right]) < float(threshold):
                continue
            if right in top_neighbors[left] and left in top_neighbors[right]:
                edges.append((left, right))
    return _connected_components_from_edges(size, edges)


def centroid_groups(records: list[VisualGroupRecord], threshold: float) -> list[list[int]]:
    size = len(records)
    groups: list[list[int]] = []
    centroids: list[np.ndarray] = []
    vectors = []
    for record in records:
        embedding = _safe_embedding(record)
        if embedding is None:
            raise ValueError(f"record has invalid embedding: {record.clip_id}")
        vectors.append(embedding)
    for index in range(size):
        vector = vectors[index]
        best_index = -1
        best_score = -1.0
        for group_index, centroid in enumerate(centroids):
            score = float(np.dot(vector, centroid))
            if score > best_score:
                best_score = score
                best_index = group_index
        if best_index < 0 or best_score < float(threshold):
            groups.append([index])
            centroids.append(vector)
            continue
        groups[best_index].append(index)
        updated = normalize_vector(np.vstack([vectors[item] for item in groups[best_index]]).mean(axis=0))
        centroids[best_index] = vector if updated is None else updated
    return sorted(groups, key=lambda group: (-len(group), group[0]))


def score_summary(values: Iterable[float]) -> dict[str, object]:
    rounded = [float(value) for value in values]
    if not rounded:
        return {"count": 0, "min": None, "mean": None, "median": None, "max": None}
    return {
        "count": len(rounded),
        "min": round(min(rounded), 6),
        "mean": round(float(np.mean(rounded)), 6),
        "median": round(float(median(rounded)), 6),
        "max": round(max(rounded), 6),
    }


def group_pairwise_scores(group: list[int], scores: np.ndarray) -> list[float]:
    values = []
    for left_pos, left in enumerate(group):
        for right in group[left_pos + 1 :]:
            values.append(float(scores[left, right]))
    return values


def build_group_report(
    records: list[VisualGroupRecord],
    groups: list[list[int]],
    scores: np.ndarray,
    method: str,
    threshold: float,
    reciprocal_topn: int,
) -> dict[str, object]:
    group_payloads = []
    for group_number, group in enumerate(groups, start=1):
        label = f"group_{group_number:03d}"
        pairwise = group_pairwise_scores(group, scores)
        members = []
        for index in group:
            record = records[index]
            other_scores = [float(scores[index, other]) for other in group if other != index]
            members.append(
                {
                    "clip_id": record.clip_id,
                    "clip_path": record.clip_path,
                    "best_frame_path": record.best_frame_path,
                    "member_mean_score": round(float(np.mean(other_scores)), 6) if other_scores else 1.0,
                    "metadata": record.metadata,
                }
            )
        group_payloads.append(
            {
                "group_id": group_number,
                "group_label": label,
                "count": len(group),
                "member_indices": group,
                "pairwise": score_summary(pairwise),
                "members": members,
            }
        )

    all_pairwise = []
    for left in range(len(records)):
        for right in range(left + 1, len(records)):
            all_pairwise.append(float(scores[left, right]))

    return {
        "method": method,
        "threshold": float(threshold),
        "reciprocal_topn": int(reciprocal_topn),
        "record_count": len(records),
        "group_count": len(group_payloads),
        "group_sizes": [len(group) for group in groups],
        "pairwise": score_summary(all_pairwise),
        "groups": group_payloads,
    }


def group_records(
    records: list[VisualGroupRecord],
    method: str = "reciprocal",
    threshold: float = 0.55,
    reciprocal_topn: int = 5,
) -> dict[str, object]:
    normalized_method = str(method or "reciprocal").strip().lower()
    scores = cosine_similarity_matrix(records)
    if normalized_method == "connected":
        groups = connected_groups(scores, threshold)
    elif normalized_method == "reciprocal":
        groups = reciprocal_groups(scores, threshold, reciprocal_topn)
    elif normalized_method == "centroid":
        groups = centroid_groups(records, threshold)
    else:
        raise ValueError(f"Unsupported visual grouping method: {method}")
    return build_group_report(records, groups, scores, normalized_method, threshold, reciprocal_topn)
