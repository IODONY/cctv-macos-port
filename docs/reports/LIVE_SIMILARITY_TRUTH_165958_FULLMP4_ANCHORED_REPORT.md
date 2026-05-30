# Live Similarity Truth Evaluation

This report compares automatic live similarity grouping against a manually sorted truth folder.

## Summary

- Session: `20260530_165958`
- Events: `logs/topk_live/20260530_165958/gallery_events.jsonl`
- Truth root: `snapshots/live_topk/20260530_165958/similarity_groups_merged`
- Embedding source: `full-mp4-anchored`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Records embedded: `20`
- Embedding failures: `0`
- Duplicate truth policy: `exclude`
- Truth conflicts: `0`

## Best Configuration

- Method: `reciprocal`
- Threshold: `0.7`
- Reciprocal top-N: `10`
- Predicted group count: `3`
- Predicted sizes: `[10, 6, 4]`
- Pairwise F1: `1.0`
- Pairwise precision: `1.0`
- Pairwise recall: `1.0`
- Purity: `1.0`
- Over-merged different-person pairs: `0`
- Split same-person pairs: `0`

## Truth Labels

| label | clips |
| --- | ---: |
| `p1` | 10 |
| `p2` | 6 |
| `p3` | 4 |

## Top Configurations

| rank | method | threshold | top-N | groups | sizes | pair F1 | precision | recall | purity | overmerge | split |
| ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | reciprocal | 0.7 | 10 | 3 | [10, 6, 4] | 1.0 | 1.0 | 1.0 | 1.0 | 0 | 0 |
| 2 | connected | 0.7 | 1 | 3 | [10, 6, 4] | 1.0 | 1.0 | 1.0 | 1.0 | 0 | 0 |
| 3 | centroid | 0.65 | 1 | 4 | [10, 5, 4, 1] | 0.96063 | 1.0 | 0.924242 | 1.0 | 0 | 5 |
| 4 | centroid | 0.7 | 1 | 4 | [10, 5, 4, 1] | 0.96063 | 1.0 | 0.924242 | 1.0 | 0 | 5 |
| 5 | reciprocal | 0.7 | 4 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 6 | reciprocal | 0.7 | 5 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 7 | reciprocal | 0.7 | 6 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 8 | reciprocal | 0.7 | 8 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 9 | centroid | 0.75 | 1 | 6 | [9, 4, 4, 1, 1, 1] | 0.842105 | 1.0 | 0.727273 | 1.0 | 0 | 18 |
| 10 | reciprocal | 0.75 | 4 | 8 | [9, 4, 2, 1, 1, 1, 1, 1] | 0.788991 | 1.0 | 0.651515 | 1.0 | 0 | 23 |
| 11 | reciprocal | 0.75 | 5 | 8 | [9, 4, 2, 1, 1, 1, 1, 1] | 0.788991 | 1.0 | 0.651515 | 1.0 | 0 | 23 |
| 12 | reciprocal | 0.75 | 6 | 8 | [9, 4, 2, 1, 1, 1, 1, 1] | 0.788991 | 1.0 | 0.651515 | 1.0 | 0 | 23 |
| 13 | reciprocal | 0.75 | 8 | 8 | [9, 4, 2, 1, 1, 1, 1, 1] | 0.788991 | 1.0 | 0.651515 | 1.0 | 0 | 23 |
| 14 | reciprocal | 0.75 | 10 | 8 | [9, 4, 2, 1, 1, 1, 1, 1] | 0.788991 | 1.0 | 0.651515 | 1.0 | 0 | 23 |
| 15 | connected | 0.75 | 1 | 8 | [9, 4, 2, 1, 1, 1, 1, 1] | 0.788991 | 1.0 | 0.651515 | 1.0 | 0 | 23 |
| 16 | reciprocal | 0.25 | 4 | 3 | [10, 9, 1] | 0.77551 | 0.703704 | 0.863636 | 0.8 | 24 | 9 |
| 17 | reciprocal | 0.25 | 5 | 3 | [10, 9, 1] | 0.77551 | 0.703704 | 0.863636 | 0.8 | 24 | 9 |
| 18 | reciprocal | 0.25 | 6 | 3 | [10, 9, 1] | 0.77551 | 0.703704 | 0.863636 | 0.8 | 24 | 9 |
| 19 | reciprocal | 0.25 | 8 | 3 | [10, 9, 1] | 0.77551 | 0.703704 | 0.863636 | 0.8 | 24 | 9 |
| 20 | reciprocal | 0.3 | 4 | 3 | [10, 9, 1] | 0.77551 | 0.703704 | 0.863636 | 0.8 | 24 | 9 |

## Best Predicted Groups

- `group_001` count=10 truth_counts={'p1': 10} pairwise={'count': 45, 'min': 0.637884, 'mean': 0.815494, 'median': 0.819813, 'max': 0.966207}
  - `live_20260530_165958_tapo_3_t001_e003564`
  - `live_20260530_165958_tapo_2_t005_e032054`
  - `live_20260530_165958_tapo_1_t004_e028611`
  - `live_20260530_165958_tapo_2_t011_e047943`
  - `live_20260530_165958_tapo_3_t013_e053054`
  - `live_20260530_165958_tapo_3_t019_e081607`
  - `live_20260530_165958_tapo_2_t021_e096289`
  - `live_20260530_165958_tapo_1_t020_e088431`
  - `live_20260530_165958_tapo_2_t023_e106881`
  - `live_20260530_165958_tapo_3_t025_e113109`
- `group_002` count=6 truth_counts={'p2': 6} pairwise={'count': 15, 'min': 0.565017, 'mean': 0.682626, 'median': 0.697949, 'max': 0.768936}
  - `live_20260530_165958_tapo_1_t008_e040623`
  - `live_20260530_165958_tapo_1_t010_e046105`
  - `live_20260530_165958_tapo_2_t009_e044722`
  - `live_20260530_165958_tapo_3_t014_e062392`
  - `live_20260530_165958_tapo_2_t016_e071717`
  - `live_20260530_165958_tapo_1_t017_e072279`
- `group_003` count=4 truth_counts={'p3': 4} pairwise={'count': 6, 'min': 0.740238, 'mean': 0.792008, 'median': 0.785627, 'max': 0.847076}
  - `live_20260530_165958_tapo_1_t001_e001941`
  - `live_20260530_165958_tapo_1_t002_e009598`
  - `live_20260530_165958_tapo_1_t003_e027634`
  - `live_20260530_165958_tapo_1_t027_e116200`

## Export

- Best grouping export: `snapshots/live_topk/20260530_165958/similarity_groups_truth_tuned_3person_fullmp4_anchored`
