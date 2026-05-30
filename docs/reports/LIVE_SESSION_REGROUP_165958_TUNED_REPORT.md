# Live Session Regroup Report

This report is generated from saved live gallery clips and best ReID crops. It does not run cameras.

## Summary

- Session: `20260530_165958`
- Events: `logs/topk_live/20260530_165958/gallery_events.jsonl`
- Output: `snapshots/live_topk/20260530_165958/similarity_groups_default_tuned_3person`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Method: `reciprocal`
- Threshold: `0.65`
- Reciprocal top-N: `8`
- Records grouped: `20`
- Group count: `3`
- Group sizes: `[10, 6, 4]`
- Failures: `0`

## Groups

| group | clips | pairwise min | pairwise mean | pairwise max | members |
| --- | ---: | ---: | ---: | ---: | --- |
| group_001 | 10 | 0.70841 | 0.802323 | 0.923237 | live_20260530_165958_tapo_3_t001_e003564, live_20260530_165958_tapo_2_t005_e032054, live_20260530_165958_tapo_1_t004_e028611, live_20260530_165958_tapo_2_t011_e047943, live_20260530_165958_tapo_3_t013_e053054, live_20260530_165958_tapo_3_t019_e081607, live_20260530_165958_tapo_2_t021_e096289, live_20260530_165958_tapo_1_t020_e088431... |
| group_002 | 6 | 0.48745 | 0.619654 | 0.750555 | live_20260530_165958_tapo_1_t008_e040623, live_20260530_165958_tapo_1_t010_e046105, live_20260530_165958_tapo_2_t009_e044722, live_20260530_165958_tapo_3_t014_e062392, live_20260530_165958_tapo_2_t016_e071717, live_20260530_165958_tapo_1_t017_e072279 |
| group_003 | 4 | 0.640743 | 0.723671 | 0.81504 | live_20260530_165958_tapo_1_t001_e001941, live_20260530_165958_tapo_1_t002_e009598, live_20260530_165958_tapo_1_t003_e027634, live_20260530_165958_tapo_1_t027_e116200 |
