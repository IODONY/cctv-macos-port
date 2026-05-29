# Live Session Regroup Report

This report is generated from saved live gallery clips and best ReID crops. It does not run cameras.

## Summary

- Session: `20260530_020213`
- Events: `logs/topk_live/20260530_020213/gallery_events.jsonl`
- Output: `snapshots/live_topk/20260530_020213/similarity_groups_merged`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Method: `reciprocal`
- Threshold: `0.55`
- Reciprocal top-N: `5`
- Records grouped: `18`
- Group count: `2`
- Group sizes: `[16, 2]`
- Failures: `0`

## Groups

| group | clips | pairwise min | pairwise mean | pairwise max | members |
| --- | ---: | ---: | ---: | ---: | --- |
| group_001 | 16 | 0.373764 | 0.546959 | 0.879869 | live_20260530_020213_cam_3_track_3_event_1780074148516, live_20260530_020213_cam_3_track_1_event_1780074137944, live_20260530_020213_cam_2_track_1_event_1780074150177, live_20260530_020213_cam_2_track_2_event_1780074151809, live_20260530_020213_cam_2_track_3_event_1780074152256, live_20260530_020213_cam_1_track_1_event_1780074155175, live_20260530_020213_cam_2_track_4_event_1780074156675, live_20260530_020213_cam_3_track_4_event_1780074157811... |
| group_002 | 2 | 0.633448 | 0.633448 | 0.633448 | live_20260530_020213_cam_3_track_2_event_1780074138156, live_20260530_020213_cam_2_track_6_event_1780074173403 |
