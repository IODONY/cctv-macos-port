# Top-K Retrieval Transition Plan

## Summary

The evaluation target is shifting from conservative pairwise identity classification to retrieval. Each query clip should rank all available gallery clips and select the Top-9 to Top-12 likely clips for the 3rd floor display. Pairwise outcomes remain useful internal signals, but success is measured by how many correct clips appear in Top-9.

## Current Architecture Analysis

- `scripts/generate_clip_manifest.py` scans `data/labeld_clips/`, excludes `Origin/`, and writes `data/labels/clips.csv` plus `data/labels/pair_labels.csv`.
- `scripts/evaluate_labeled_clips.py` loads `pair_labels.csv`, analyzes each clip, compares listed pairs, and emits `matched`, `ambiguous`, `low_confidence`, or `no_match`.
- Clip-level evidence is aggregated by `build_evidence_profile()`.
- Main scoring is `weighted_similarity()` with same-camera and cross-camera weights.
- `type_c_raw_score()` remains a reference signal using bag, torso, and brightness similarity.
- Current tuned defaults are `match_threshold=0.72`, `ambiguous_threshold=0.25`, and `min_available_weight=2.8`.
- Current pairwise result is `correct=51`, `incorrect=0`, `uncertain=97`, with outcomes `matched=22`, `ambiguous=97`, `no_match=29`, and `low_confidence=0`.
- This under-retrieves because many useful clips remain `ambiguous`, and pairwise classification does not answer which 9 clips should be displayed.

## Retrieval Architecture Proposal

- Add `scripts/evaluate_topk_retrieval.py`.
- Treat each `clips.csv` row as both a possible query and a gallery item.
- For each query, rank all other clips by a retrieval score.
- Reuse existing clip analysis, evidence profiles, camera-aware pair scoring, Type A/B flags, Type C raw score, and strong contradiction reasons.
- Keep pairwise outcome internally, but final ranking should prioritize coverage:
  - `matched` candidates rank highest.
  - high-score `ambiguous` candidates can fill Top-K.
  - high-confidence non-hard-negative `no_match` candidates are allowed only when the pool is thin.
  - `low_confidence` candidates stay below better-supported options.
- Default retrieval settings:
  - `--k 9`
  - `--candidate-pool 12`
  - query gallery excludes the query clip itself.

## Feature Strategy

- Keep top color, bag presence, torso ratio, sleeve/pants coverage, weak bottom color, Type A/B flags, and Type C raw score.
- Weaken cross-camera brightness, cross-camera bottom color, and unstable low-support fields.
- Add later, after the first retrieval evaluator:
  - top and bottom color histogram similarity
  - brightness-normalized color distance
  - silhouette or box aspect-ratio stability
  - confidence-weighted bag evidence
- Preserve camera-aware weighting and expose per-feature confidence in reports.
- Keep hard-negative contradiction rules as ranking penalties rather than absolute rejection.

## Evaluation Metrics

- Primary metrics:
  - `Recall@9`
  - `Precision@9`
  - `Top-9 Own Count`
  - `Wrong@9`
- Secondary metrics:
  - `Recall@12`
  - `Precision@12`
  - ambiguous rate inside Top-9
  - false-match rate inside Top-9
  - hard-negative error rate inside Top-9
  - ranking margin between the 9th candidate and the first wrong high-risk candidate
  - per-identity mean and worst-case Top-9 Own Count
- Dataset success target:
  - maximize Top-9 Own Count
  - tolerate 1 to 2 wrong clips in Top-9
  - avoid Top-9 sets where correct clips are not the majority
  - keep hard-negative Top-9 entries visible in reports

## Dataset And Labeling Structure

- Keep `data/labels/clips.csv` as the source of query/gallery truth.
- Keep `data/labels/pair_labels.csv` as optional pairwise debugging data.
- Do not require a new label file for v1 because `identity_id` in `clips.csv` provides the ground truth.
- Query/gallery split:
  - every clip is a query once
  - all other clips are gallery candidates
  - same `identity_id` means positive
  - different `identity_id` means negative
- Future optional `data/labels/retrieval_queries.csv` can define manual query subsets.
- Do not modify source MP4 files.

## Debugging System

- Write detailed JSON to `logs/topk_retrieval/results.json`.
- Write Markdown reports to:
  - `docs/reports/TOPK_RETRIEVAL_EVAL_REPORT.md`
  - `docs/reports/TOPK_RETRIEVAL_DEBUG_REPORT.md`
- Include query id, candidate id, rank, retrieval score, pair outcome, feature scores, penalties, support confidence, correctness, and hard-negative markers.
- Add optional contact sheets later under ignored `logs/topk_retrieval/contact_sheets/`.

## Implementation Phases

1. Create this plan file and commit `docs: plan top-k retrieval transition`.
2. Add `scripts/evaluate_topk_retrieval.py` using current safe scoring helpers.
3. Report Recall@9, Precision@9, Top-9 Own Count, Wrong@9, Recall@12, Precision@12, ambiguous rate, false-match rate, hard-negative Top-K count, and ranking margins.
4. Add reports under `docs/reports/` and ignored runtime JSON under `logs/topk_retrieval/`.
5. Validate with `.venv/bin/python -m py_compile scripts/*.py` and `source .venv/bin/activate && scripts/agent_validate.sh`.

## Safety Constraints

- No face recognition.
- No age, gender, race, or demographic inference.
- No biometric identification.
- No RTSP or live camera execution.
- No TouchDesigner execution.
- No source MP4 modification.
- Work only inside `/Users/fullcodex/CCTV_Project`.
- Keep runtime output in ignored `logs/` or `snapshots/`.
- Commit only code, docs, and small text reports.

## Final Target Behavior

At the 3rd floor display, a visitor query clip or tracklet arrives, the system builds or receives an evidence profile, all gallery tracklets are ranked, and the display selects Top-9 clips, optionally from a Top-12 candidate pool. `matched` candidates are preferred, but strong `ambiguous` candidates can fill the retrieval set. The target may tolerate 1 to 2 incorrect clips if most displayed clips belong to the actual visitor.

The current pairwise matcher should be reused as an internal scoring component. The final product layer should be partially replaced by retrieval ranking rather than hard pairwise classification.
