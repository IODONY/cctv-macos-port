# ReID Top-K Debugging Workflow

## Purpose

Use labeled clips to continuously debug the appearance-based Top-K retrieval system without running live cameras, RTSP, TouchDesigner, or full tracking. The goal is to improve the final ranked clip output, especially OwnCount@9 and normalized OwnRecall@9.

## Loop

1. Add more labeled clips per identity.
2. Regenerate the manifest:

```bash
python scripts/generate_clip_manifest.py
```

3. Extract or reuse YOLO person crops from each clip.
4. Select best shots or tracklet-level representative frames.
5. Extract ReID embeddings or the current appearance retrieval profile.
6. Evaluate Top-K retrieval:

```bash
python scripts/evaluate_topk_retrieval.py --dataset test_clip_0527 --k 9 --leave-one-out
```

7. Inspect:
   - `docs/reports/LABELED_CLIP_STRUCTURE_REPORT.md`
   - `docs/reports/CLIP_MANIFEST_REPORT.md`
   - `docs/reports/TEST_CLIP_0527_EVAL_REPORT.md`
   - `docs/reports/TOPK_RETRIEVAL_DEBUG_REPORT.md`

8. Tune crop quality, best-shot selection, embedding/profile scoring, camera weighting, and fallback ordering.
9. Repeat with new clips and compare the report metrics.

## Useful Evaluation Modes

Leave-one-out over a dataset:

```bash
python scripts/evaluate_topk_retrieval.py --dataset test_clip_0527 --k 9 --leave-one-out
```

Camera split simulation:

```bash
python scripts/evaluate_topk_retrieval.py \
  --dataset test_clip_0527 \
  --k 9 \
  --query-cams cam_5 \
  --gallery-cams cam_1,cam_2,cam_3,cam_4
```

The camera split is only a simulation helper. Do not assume `cam_5` is always the third-floor camera.

## Failure Categories

- `insufficient_same_identity_gallery`: The labeled dataset does not contain enough same-identity gallery clips for a query to return 9 own clips.
- `insufficient_gallery`: The total gallery is too small to return K clips.
- `weak_yolo_crop`: YOLO selected a small, partial, occluded, or off-center person crop.
- `bad_best_shot_selection`: The chosen representative frame does not show stable clothing or body proportions.
- `lighting_mismatch`: Exposure or white balance differs enough to distort color-based retrieval.
- `camera_angle_mismatch`: A camera angle changes visible clothing regions or bag visibility.
- `hard_negative_identity`: A different person has similar clothing and camera context.
- `too_many_wrong_clips_in_top_9`: The output returns 9 clips but the own-identity count is too low.
- `query_crop_too_small_or_blurred`: The query crop lacks enough detail for reliable scoring.

## Reading Reports

Use `available_positive_count` before judging a query. If it is below 9, Top-9 cannot be all own-identity clips. In that case, prioritize `normalized_own_recall_at_9` over raw OwnCount@9.

Use these metrics together:

- `TopK output count`: whether the system returned enough clips.
- `OwnCount@9`: how many Top-9 clips match the labeled query identity.
- `Wrong@9`: how many Top-9 clips are not the labeled query identity.
- `Recall@9`: own clips found out of all available positives.
- `Normalized OwnRecall@9`: own clips found out of the maximum possible own clips at K.
- `output_readiness`: whether the result is ready, data-limited, or ranking-limited.

## Live Track Debugging

For the Tapo + MacBook runtime, debug one local person track at a time:

1. Start the live bridge with `--osc-dry-run --max-runtime-seconds 30`.
2. Confirm each detected person creates a separate cropped clip under `snapshots/live_topk/`.
3. Confirm each clip has a matching `_best.jpg` ReID frame.
4. Inspect `logs/topk_live/<session>/gallery_events.jsonl` for clip quality and embedding method.
5. Stand in front of the MacBook query camera and inspect `query_results.jsonl`.
6. Check whether rank 1 through rank 9 are visually plausible before opening TouchDesigner.
7. If ranking is weak, inspect the query crop and gallery best frames before changing thresholds.

## Stability Rules

- Do not use face recognition or demographic inference.
- Keep identity labels limited to offline evaluation.
- Do not mutate source MP4 files.
- Keep generated logs, crops, contact sheets, and snapshots out of Git.
- Prefer adding more labeled clips before over-tuning thresholds to a thin dataset.
