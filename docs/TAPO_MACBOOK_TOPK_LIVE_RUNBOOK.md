# Tapo + MacBook Live Top-K Runbook

## Runtime Goal

The live system is now track-centric, not visitor-id-centric.

1. Gallery cameras, such as Tapo RTSP cameras on the lower floors, run YOLO person detection.
2. When YOLO detects a person track, recording starts immediately for that local track.
3. If several people are visible, each local track gets its own cropped clip and its own ReID best frame.
4. When a track disappears from the frame for a short grace window, that track clip is closed.
5. The best crop from the clip is embedded and added to the live gallery.
6. The MacBook webcam runs as a query camera.
7. While a query person is visible, the webcam periodically extracts an embedding and ranks gallery clips by visual similarity.
8. TouchDesigner receives ranked clip paths and scores, then routes rank 1 through rank 9 to playback slots.

This is appearance-based retrieval. The live runtime does not know identity labels and does not perform face recognition or demographic inference.

## Camera Roles

Use environment variables for Tapo RTSP URLs. Do not commit RTSP credentials.

Example:

```bash
export TAPO_1F_RTSP_URL='rtsp://...'
export TAPO_2F_RTSP_URL='rtsp://...'
```

Run gallery Tapo cameras plus the MacBook internal camera:

```bash
source .venv/bin/activate
python src/live_topk_bridge.py \
  --rtsp-envs TAPO_1F_RTSP_URL,TAPO_2F_RTSP_URL \
  --rtsp webcam:0 \
  --cam-types G,G,Q \
  --topk 9
```

Roles:

- `G`, `A`, `B`: gallery cameras. They create per-person clips and gallery embeddings.
- `Q`, `C`: query cameras. They do not create gallery clips; they periodically send Top-K results.

For a short smoke test, add:

```bash
--max-runtime-seconds 30 --osc-dry-run
```

`--osc-dry-run` prints the OSC payload instead of sending UDP, which is useful before opening TouchDesigner.

## Runtime Outputs

Generated runtime files stay under ignored folders:

- `snapshots/live_topk/<session>/cam_N/*.mp4`: cropped per-person track clips.
- `snapshots/live_topk/<session>/cam_N/*_best.jpg`: best ReID crop per track.
- `logs/topk_live/<session>/gallery_events.jsonl`: gallery record metadata.
- `logs/topk_live/<session>/query_results.jsonl`: query Top-K results.
- `logs/model_cache/torch`: local pretrained model cache.

These files should not be committed.

## TouchDesigner

The live bridge sends the main Top-K payload to:

```text
/walnut/topk/cam/{cam_id}/results
```

Flat payload shape:

```text
event_id, timestamp, query_id, query_cam_id, k, result_count, gallery_count,
rank_1, clip_id_1, clip_path_1, score_1, cam_id_1, fallback_1, ...
```

Use `touchdesigner/touchdesigner_topk_callbacks.py` with an OSC In DAT or Table DAT workflow. The callback appends Top-K rows to `topk_results_table` and routes ranks to:

- `movie_clip_1`
- `movie_clip_2`
- ...
- `movie_clip_9`

Unlike the older Type-C playback callback, routing is by Top-K rank, not by camera number. This matters because multiple high-ranking clips can come from the same camera.

## ReID Behavior

The default embedding path uses `torchvision_mobilenet_v3_large` with a project-local model cache. If that model cannot load, the bridge falls back to an HSV color histogram so the runtime stays alive.

The ranking score is cosine similarity between normalized query and gallery embeddings. Results below `--fallback-score` are still returned to keep the display populated, but they are marked as fallback in logs and OSC payloads.

## Practical Tuning

Important CLI parameters:

- `--track-missing-grace 8`: how many analyzed frames a track can be absent before its clip closes.
- `--query-interval-seconds 1.0`: how often the MacBook query refreshes Top-K while a person is visible.
- `--max-clip-seconds 30`: safety cutoff for very long tracks.
- `--clip-width 320 --clip-height 640`: cropped person clip resolution.
- `--fallback-score 0.55`: score below which a result is considered fallback.

If Top-9 contains too many wrong clips, inspect:

- weak YOLO crop
- blurred best frame
- person partially outside frame
- gallery clip too short
- lighting mismatch
- camera angle mismatch
- visually similar hard negative
- query person too small in MacBook webcam
