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

Current LAN gallery test mapping:

| runtime role | physical camera | IP address | label |
| --- | ---: | --- | --- |
| gallery | 1 | `192.168.5.59` | `tapo_1` |
| gallery | 2 | `192.168.5.57` | `tapo_2` |
| gallery | 3 | `192.168.5.64` | `tapo_3` |
| query | MacBook internal camera | `webcam:0` | `macbook_query` |

Set RTSP URLs in the local shell only. The URL pattern is:

```text
rtsp://<camera-user>:<camera-password>@<camera-ip>/stream1
```

Example local setup:

```bash
export TAPO_CAM_1_RTSP_URL='rtsp://<user>:<password>@192.168.5.59/stream1'
export TAPO_CAM_2_RTSP_URL='rtsp://<user>:<password>@192.168.5.57/stream1'
export TAPO_CAM_3_RTSP_URL='rtsp://<user>:<password>@192.168.5.64/stream1'
```

If a base RTSP URL does not open for a specific Tapo model, try the same environment variable with `/stream1` or `/stream2` appended.

If every Tapo URL returns `401 Unauthorized`, the network path is reachable but RTSP authentication failed. Check the per-camera RTSP account, password, and whether RTSP/third-party streaming is enabled in the Tapo camera settings. A path change from the base URL to `/stream1` or `/stream2` will not fix an invalid account or disabled RTSP service.

On macOS, the MacBook query camera must be allowed for the Python/Codex runtime in System Settings > Privacy & Security > Camera. The bridge opens webcam sources once on the main thread before starting workers so macOS can present the permission prompt. If `webcam_opened=False` or `not authorized to capture video` appears, grant camera access and rerun the same command.

## Smoke Tests

First test one camera for one minute:

```bash
source .venv/bin/activate
python src/live_topk_bridge.py \
  --rtsp-envs TAPO_CAM_1_RTSP_URL \
  --cam-types G \
  --cam-labels tapo_1 \
  --max-runtime-seconds 60 \
  --disable-osc
```

Then test all three gallery cameras:

```bash
source .venv/bin/activate
python src/live_topk_bridge.py \
  --rtsp-envs TAPO_CAM_1_RTSP_URL,TAPO_CAM_2_RTSP_URL,TAPO_CAM_3_RTSP_URL \
  --cam-types G,G,G \
  --cam-labels tapo_1,tapo_2,tapo_3 \
  --embedding-model osnet_x0_25 \
  --record-video-mode full-frame \
  --storage-layout similarity \
  --show-preview \
  --preview-reid-crops \
  --max-runtime-seconds 120 \
  --disable-osc
```

With `--storage-layout similarity`, the original camera folders are still kept for traceability, but a review view is also created at:

```text
snapshots/live_topk/<session>/similarity_groups/group_001/
snapshots/live_topk/<session>/similarity_groups/group_002/
snapshots/live_topk/<session>/similarity_groups_merged/group_001/
```

`similarity_groups/` is the online temporary view created as clips finish. `similarity_groups_merged/` is regenerated at session shutdown using all saved clips and reciprocal kNN grouping, so it is the preferred review folder when checking whether the same person was split too much.

To re-check grouping quality from an existing live session without opening the cameras again:

```bash
source .venv/bin/activate
python scripts/regroup_live_session.py \
  --session <session_id> \
  --embedding-model osnet_x0_25 \
  --method reciprocal \
  --threshold 0.55 \
  --reciprocal-topn 5 \
  --export-mode symlink \
  --write-report docs/reports/LIVE_SESSION_REGROUP_REPORT.md

python scripts/sweep_live_similarity_groups.py \
  --session <session_id> \
  --embedding-model osnet_x0_25 \
  --thresholds 0.50,0.55,0.60,0.65,0.70,0.72 \
  --output-report docs/reports/LIVE_OSNET_GROUPING_SWEEP_REPORT.md
```

Finally run three Tapo gallery cameras plus the MacBook query camera. This test does not require TouchDesigner; every query event exports the selected clips into the workspace.

```bash
source .venv/bin/activate
python src/live_topk_bridge.py \
  --rtsp-envs TAPO_CAM_1_RTSP_URL,TAPO_CAM_2_RTSP_URL,TAPO_CAM_3_RTSP_URL \
  --rtsp webcam:0 \
  --cam-types G,G,G,Q \
  --cam-labels tapo_1,tapo_2,tapo_3,macbook_query \
  --topk 7 \
  --export-topk-dir snapshots/topk_exports \
  --export-mode symlink \
  --disable-osc
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

- `snapshots/live_topk/<session>/cam_N/*.mp4`: per-person track clips. With the default `--record-video-mode full-frame`, these are full original frames, not cropped person videos.
- `snapshots/live_topk/<session>/cam_N/*_best.jpg`: cropped best ReID frame per track.
- `snapshots/live_topk/<session>/similarity_groups/group_NNN/`: optional appearance-similarity review folders when `--storage-layout similarity` is used.
- `snapshots/live_topk/<session>/similarity_groups_merged/group_NNN/`: final session-end regrouped review folders.
- `snapshots/topk_exports/<session>/<query_id>/results.json`: ranked clips selected for one MacBook query event.
- `snapshots/topk_exports/<session>/<query_id>/query_best.jpg`: query crop used for ranking.
- `snapshots/topk_exports/<session>/<query_id>/rank_01/clip.mp4`: symlink or copy of the selected clip, depending on `--export-mode`.
- `snapshots/topk_exports/<session>/<query_id>/rank_01/best.jpg`: symlink or copy of the selected gallery best frame.
- `snapshots/topk_exports/<session>/<query_id>/rank_01/score.json`: score and metadata for that rank.
- `logs/topk_live/<session>/gallery_events.jsonl`: gallery record metadata.
- `logs/topk_live/<session>/query_results.jsonl`: query Top-K results.
- `logs/model_cache/torch`: local pretrained model cache.

These files should not be committed.

`--export-mode symlink` is preferred on the MacBook because it avoids duplicating video data. Use `--export-mode copy` only if another app cannot follow symlinks. Use `--export-mode path` to write path text files only.

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

The default embedding path uses Torchreid `osnet_x0_25` with MSMT17 ReID weights cached under `logs/model_cache/torchreid`. This is a person-ReID appearance model, not face recognition. If `torchreid` or the OSNet weights cannot load, the bridge raises an explicit error instead of silently falling back to MobileNetV3.

MobileNetV3 and HSV histogram backends remain available for comparison with `--embedding-model mobilenet_v3_large`, `mobilenet_v3_small`, `efficientnet_b0`, or `hsv_histogram`.

The ranking score is cosine similarity between normalized query and gallery embeddings. Results below `--fallback-score` are still returned to keep the display populated, but they are marked as fallback in logs and OSC payloads.

## Practical Tuning

Important CLI parameters:

- `--track-missing-grace 8`: how many analyzed frames a track can be absent before its clip closes.
- `--query-interval-seconds 1.0`: how often the MacBook query refreshes Top-K while a person is visible.
- `--max-clip-seconds 30`: safety cutoff for very long tracks.
- `--clip-width 320 --clip-height 640`: cropped person clip resolution.
- `--fallback-score 0.55`: score below which a result is considered fallback.
- `--cam-labels ...`: physical camera labels that stay attached to logs, exports, and OSC side channels.
- `--embedding-model osnet_x0_25`: default lightweight person-ReID backend.
- `--record-video-mode full-frame`: save full-frame video per detected person track while keeping ReID crops separate.
- `--record-video-mode person-crop`: legacy mode that records cropped person videos.
- `--show-preview`: open annotated YOLO/ReID analysis windows.
- `--preview-reid-crops`: also show the selected ReID crop whenever a track is embedded.
- `--storage-layout similarity`: mirror gallery clips into appearance-similarity folders for debugging.
- `--similarity-group-threshold 0.72`: grouping threshold for that temporary review layout.
- `--merge-threshold 0.55`: final session-end grouping threshold.
- `--merge-reciprocal-topn 5`: mutual neighbor count for final session-end grouping.
- `--no-session-end-merge`: keep only the online temporary similarity folders.
- `--export-topk-dir snapshots/topk_exports`: query-by-query export bundles for TouchDesigner-free testing.
- `--disable-osc`: skip all OSC traffic during camera-only validation.

If Top-9 contains too many wrong clips, inspect:

- weak YOLO crop
- blurred best frame
- person partially outside frame
- gallery clip too short
- lighting mismatch
- camera angle mismatch
- visually similar hard negative
- query person too small in MacBook webcam
