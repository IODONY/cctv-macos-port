# Live Similarity Truth Evaluation

This report compares automatic live similarity grouping against a manually sorted truth folder.

## Summary

- Session: `20260530_165958`
- Events: `logs/topk_live/20260530_165958/gallery_events.jsonl`
- Truth root: `snapshots/live_topk/20260530_165958/similarity_groups_merged`
- Embedding source: `best-crops`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Records embedded: `20`
- Embedding failures: `0`
- Duplicate truth policy: `exclude`
- Truth conflicts: `0`

## Best Configuration

- Method: `reciprocal`
- Threshold: `0.65`
- Reciprocal top-N: `8`
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
| 1 | reciprocal | 0.65 | 8 | 3 | [10, 6, 4] | 1.0 | 1.0 | 1.0 | 1.0 | 0 | 0 |
| 2 | reciprocal | 0.65 | 10 | 3 | [10, 6, 4] | 1.0 | 1.0 | 1.0 | 1.0 | 0 | 0 |
| 3 | connected | 0.65 | 1 | 3 | [10, 6, 4] | 1.0 | 1.0 | 1.0 | 1.0 | 0 | 0 |
| 4 | centroid | 0.6 | 1 | 4 | [10, 5, 4, 1] | 0.96063 | 1.0 | 0.924242 | 1.0 | 0 | 5 |
| 5 | reciprocal | 0.25 | 4 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 6 | reciprocal | 0.3 | 4 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 7 | reciprocal | 0.35 | 4 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 8 | reciprocal | 0.4 | 4 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 9 | reciprocal | 0.45 | 4 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 10 | reciprocal | 0.5 | 4 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 11 | reciprocal | 0.55 | 4 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 12 | reciprocal | 0.6 | 4 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 13 | reciprocal | 0.6 | 5 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 14 | reciprocal | 0.65 | 4 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 15 | reciprocal | 0.65 | 5 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 16 | reciprocal | 0.65 | 6 | 4 | [9, 6, 4, 1] | 0.926829 | 1.0 | 0.863636 | 1.0 | 0 | 9 |
| 17 | centroid | 0.65 | 1 | 5 | [10, 4, 3, 2, 1] | 0.909091 | 1.0 | 0.833333 | 1.0 | 0 | 11 |
| 18 | reciprocal | 0.7 | 8 | 7 | [10, 3, 2, 2, 1, 1, 1] | 0.862069 | 1.0 | 0.757576 | 1.0 | 0 | 16 |
| 19 | reciprocal | 0.7 | 10 | 7 | [10, 3, 2, 2, 1, 1, 1] | 0.862069 | 1.0 | 0.757576 | 1.0 | 0 | 16 |
| 20 | centroid | 0.7 | 1 | 7 | [10, 3, 2, 2, 1, 1, 1] | 0.862069 | 1.0 | 0.757576 | 1.0 | 0 | 16 |

## Best Predicted Groups

- `group_001` count=10 truth_counts={'p1': 10} pairwise={'count': 45, 'min': 0.70841, 'mean': 0.802323, 'median': 0.7969, 'max': 0.923237}
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
- `group_002` count=6 truth_counts={'p2': 6} pairwise={'count': 15, 'min': 0.48745, 'mean': 0.619654, 'median': 0.620219, 'max': 0.750555}
  - `live_20260530_165958_tapo_1_t008_e040623`
  - `live_20260530_165958_tapo_1_t010_e046105`
  - `live_20260530_165958_tapo_2_t009_e044722`
  - `live_20260530_165958_tapo_3_t014_e062392`
  - `live_20260530_165958_tapo_2_t016_e071717`
  - `live_20260530_165958_tapo_1_t017_e072279`
- `group_003` count=4 truth_counts={'p3': 4} pairwise={'count': 6, 'min': 0.640743, 'mean': 0.723671, 'median': 0.720858, 'max': 0.81504}
  - `live_20260530_165958_tapo_1_t001_e001941`
  - `live_20260530_165958_tapo_1_t002_e009598`
  - `live_20260530_165958_tapo_1_t003_e027634`
  - `live_20260530_165958_tapo_1_t027_e116200`

## Export

- Best grouping export: `snapshots/live_topk/20260530_165958/similarity_groups_truth_tuned_3person`
