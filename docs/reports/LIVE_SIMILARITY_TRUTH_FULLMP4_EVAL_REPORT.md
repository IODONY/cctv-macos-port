# Live Similarity Truth Evaluation

This report compares automatic live similarity grouping against a manually sorted truth folder.

## Summary

- Session: `20260530_163231`
- Events: `logs/topk_live/20260530_163231/gallery_events.jsonl`
- Truth root: `snapshots/live_topk/20260530_163231/similarity_groups_merged/group_001/jpg`
- Embedding source: `full-mp4`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Records embedded: `11`
- Embedding failures: `0`
- Duplicate truth policy: `exclude`
- Truth conflicts: `0`

## Best Configuration

- Method: `centroid`
- Threshold: `0.65`
- Reciprocal top-N: `1`
- Predicted group count: `3`
- Predicted sizes: `[9, 1, 1]`
- Pairwise F1: `0.615385`
- Pairwise precision: `0.444444`
- Pairwise recall: `1.0`
- Purity: `0.636364`
- Over-merged different-person pairs: `20`
- Split same-person pairs: `0`

## Truth Labels

| label | clips |
| --- | ---: |
| `p1` | 5 |
| `p2` | 4 |
| `p3` | 1 |
| `p4` | 1 |

## Top Configurations

| rank | method | threshold | top-N | groups | sizes | pair F1 | precision | recall | purity | overmerge | split |
| ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | centroid | 0.65 | 1 | 3 | [9, 1, 1] | 0.615385 | 0.444444 | 1.0 | 0.636364 | 20 | 0 |
| 2 | centroid | 0.7 | 1 | 3 | [9, 1, 1] | 0.615385 | 0.444444 | 1.0 | 0.636364 | 20 | 0 |
| 3 | centroid | 0.75 | 1 | 3 | [9, 1, 1] | 0.615385 | 0.444444 | 1.0 | 0.636364 | 20 | 0 |
| 4 | connected | 0.65 | 1 | 3 | [9, 1, 1] | 0.615385 | 0.444444 | 1.0 | 0.636364 | 20 | 0 |
| 5 | connected | 0.7 | 1 | 3 | [9, 1, 1] | 0.615385 | 0.444444 | 1.0 | 0.636364 | 20 | 0 |
| 6 | connected | 0.75 | 1 | 3 | [9, 1, 1] | 0.615385 | 0.444444 | 1.0 | 0.636364 | 20 | 0 |
| 7 | centroid | 0.55 | 1 | 2 | [9, 2] | 0.603774 | 0.432432 | 1.0 | 0.545455 | 21 | 0 |
| 8 | centroid | 0.6 | 1 | 2 | [9, 2] | 0.603774 | 0.432432 | 1.0 | 0.545455 | 21 | 0 |
| 9 | reciprocal | 0.65 | 5 | 4 | [8, 1, 1, 1] | 0.590909 | 0.464286 | 0.8125 | 0.727273 | 15 | 3 |
| 10 | reciprocal | 0.7 | 5 | 4 | [8, 1, 1, 1] | 0.590909 | 0.464286 | 0.8125 | 0.727273 | 15 | 3 |
| 11 | reciprocal | 0.75 | 5 | 4 | [8, 1, 1, 1] | 0.590909 | 0.464286 | 0.8125 | 0.727273 | 15 | 3 |
| 12 | reciprocal | 0.8 | 5 | 4 | [8, 1, 1, 1] | 0.590909 | 0.464286 | 0.8125 | 0.727273 | 15 | 3 |
| 13 | centroid | 0.8 | 1 | 4 | [8, 1, 1, 1] | 0.590909 | 0.464286 | 0.8125 | 0.727273 | 15 | 3 |
| 14 | connected | 0.8 | 1 | 4 | [8, 1, 1, 1] | 0.590909 | 0.464286 | 0.8125 | 0.727273 | 15 | 3 |
| 15 | reciprocal | 0.45 | 5 | 3 | [8, 2, 1] | 0.577778 | 0.448276 | 0.8125 | 0.636364 | 16 | 3 |
| 16 | reciprocal | 0.5 | 5 | 3 | [8, 2, 1] | 0.577778 | 0.448276 | 0.8125 | 0.636364 | 16 | 3 |
| 17 | reciprocal | 0.55 | 5 | 3 | [8, 2, 1] | 0.577778 | 0.448276 | 0.8125 | 0.636364 | 16 | 3 |
| 18 | reciprocal | 0.6 | 5 | 3 | [8, 2, 1] | 0.577778 | 0.448276 | 0.8125 | 0.636364 | 16 | 3 |
| 19 | centroid | 0.45 | 1 | 1 | [11] | 0.450704 | 0.290909 | 1.0 | 0.454545 | 39 | 0 |
| 20 | centroid | 0.5 | 1 | 1 | [11] | 0.450704 | 0.290909 | 1.0 | 0.454545 | 39 | 0 |

## Best Predicted Groups

- `group_001` count=9 truth_counts={'p1': 5, 'p2': 4} pairwise={'count': 36, 'min': 0.648503, 'mean': 0.796601, 'median': 0.793723, 'max': 0.999429}
  - `live_20260530_163231_tapo_3_track_8_event_1780126376551`
  - `live_20260530_163231_tapo_3_track_12_event_1780126382412`
  - `live_20260530_163231_tapo_3_track_1_event_1780126356481`
  - `live_20260530_163231_tapo_3_track_1_event_1780126386562`
  - `live_20260530_163231_tapo_3_track_12_event_1780126385342`
  - `live_20260530_163231_tapo_1_track_18_event_1780126396392`
  - `live_20260530_163231_tapo_2_track_17_event_1780126395913`
  - `live_20260530_163231_tapo_3_track_22_event_1780126409174`
  - `live_20260530_163231_tapo_3_track_21_event_1780126405901`
- `group_002` count=1 truth_counts={'p3': 1} pairwise={'count': 0, 'min': None, 'mean': None, 'median': None, 'max': None}
  - `live_20260530_163231_tapo_1_track_1_event_1780126354502`
- `group_003` count=1 truth_counts={'p4': 1} pairwise={'count': 0, 'min': None, 'mean': None, 'median': None, 'max': None}
  - `live_20260530_163231_tapo_1_track_13_event_1780126390303`

## Export

- Best grouping export: `snapshots/live_topk/20260530_163231/similarity_groups_truth_tuned_fullmp4`
