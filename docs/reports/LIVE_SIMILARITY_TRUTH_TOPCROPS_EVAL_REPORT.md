# Live Similarity Truth Evaluation

This report compares automatic live similarity grouping against a manually sorted truth folder.

## Summary

- Session: `20260530_163231`
- Events: `logs/topk_live/20260530_163231/gallery_events.jsonl`
- Truth root: `snapshots/live_topk/20260530_163231/similarity_groups_merged/group_001/jpg`
- Embedding source: `top-crops`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Records embedded: `11`
- Embedding failures: `0`
- Duplicate truth policy: `exclude`
- Truth conflicts: `0`

## Best Configuration

- Method: `centroid`
- Threshold: `0.6`
- Reciprocal top-N: `1`
- Predicted group count: `3`
- Predicted sizes: `[5, 4, 2]`
- Pairwise F1: `0.969697`
- Pairwise precision: `0.941176`
- Pairwise recall: `1.0`
- Purity: `0.909091`
- Over-merged different-person pairs: `1`
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
| 1 | centroid | 0.6 | 1 | 3 | [5, 4, 2] | 0.969697 | 0.941176 | 1.0 | 0.909091 | 1 | 0 |
| 2 | centroid | 0.65 | 1 | 3 | [5, 4, 2] | 0.969697 | 0.941176 | 1.0 | 0.909091 | 1 | 0 |
| 3 | centroid | 0.7 | 1 | 5 | [5, 3, 1, 1, 1] | 0.896552 | 1.0 | 0.8125 | 1.0 | 0 | 3 |
| 4 | centroid | 0.75 | 1 | 5 | [5, 3, 1, 1, 1] | 0.896552 | 1.0 | 0.8125 | 1.0 | 0 | 3 |
| 5 | centroid | 0.8 | 1 | 5 | [5, 3, 1, 1, 1] | 0.896552 | 1.0 | 0.8125 | 1.0 | 0 | 3 |
| 6 | reciprocal | 0.8 | 3 | 5 | [6, 2, 1, 1, 1] | 0.6875 | 0.6875 | 0.6875 | 0.909091 | 5 | 5 |
| 7 | reciprocal | 0.8 | 4 | 5 | [6, 2, 1, 1, 1] | 0.6875 | 0.6875 | 0.6875 | 0.909091 | 5 | 5 |
| 8 | reciprocal | 0.8 | 5 | 5 | [6, 2, 1, 1, 1] | 0.6875 | 0.6875 | 0.6875 | 0.909091 | 5 | 5 |
| 9 | connected | 0.8 | 1 | 5 | [6, 2, 1, 1, 1] | 0.6875 | 0.6875 | 0.6875 | 0.909091 | 5 | 5 |
| 10 | reciprocal | 0.7 | 2 | 5 | [4, 4, 1, 1, 1] | 0.642857 | 0.75 | 0.5625 | 0.909091 | 3 | 7 |
| 11 | reciprocal | 0.75 | 2 | 5 | [4, 4, 1, 1, 1] | 0.642857 | 0.75 | 0.5625 | 0.909091 | 3 | 7 |
| 12 | reciprocal | 0.45 | 2 | 4 | [4, 4, 2, 1] | 0.62069 | 0.692308 | 0.5625 | 0.818182 | 4 | 7 |
| 13 | reciprocal | 0.5 | 2 | 4 | [4, 4, 2, 1] | 0.62069 | 0.692308 | 0.5625 | 0.818182 | 4 | 7 |
| 14 | reciprocal | 0.55 | 2 | 4 | [4, 4, 2, 1] | 0.62069 | 0.692308 | 0.5625 | 0.818182 | 4 | 7 |
| 15 | reciprocal | 0.6 | 2 | 4 | [4, 4, 2, 1] | 0.62069 | 0.692308 | 0.5625 | 0.818182 | 4 | 7 |
| 16 | reciprocal | 0.65 | 2 | 4 | [4, 4, 2, 1] | 0.62069 | 0.692308 | 0.5625 | 0.818182 | 4 | 7 |
| 17 | reciprocal | 0.7 | 3 | 3 | [9, 1, 1] | 0.615385 | 0.444444 | 1.0 | 0.636364 | 20 | 0 |
| 18 | reciprocal | 0.7 | 4 | 3 | [9, 1, 1] | 0.615385 | 0.444444 | 1.0 | 0.636364 | 20 | 0 |
| 19 | reciprocal | 0.7 | 5 | 3 | [9, 1, 1] | 0.615385 | 0.444444 | 1.0 | 0.636364 | 20 | 0 |
| 20 | connected | 0.7 | 1 | 3 | [9, 1, 1] | 0.615385 | 0.444444 | 1.0 | 0.636364 | 20 | 0 |

## Best Predicted Groups

- `group_001` count=5 truth_counts={'p1': 5} pairwise={'count': 10, 'min': 0.745136, 'mean': 0.806184, 'median': 0.80959, 'max': 0.862123}
  - `live_20260530_163231_tapo_3_track_1_event_1780126356481`
  - `live_20260530_163231_tapo_3_track_1_event_1780126386562`
  - `live_20260530_163231_tapo_1_track_18_event_1780126396392`
  - `live_20260530_163231_tapo_2_track_17_event_1780126395913`
  - `live_20260530_163231_tapo_3_track_22_event_1780126409174`
- `group_002` count=4 truth_counts={'p2': 4} pairwise={'count': 6, 'min': 0.666679, 'mean': 0.745232, 'median': 0.750346, 'max': 0.849375}
  - `live_20260530_163231_tapo_3_track_8_event_1780126376551`
  - `live_20260530_163231_tapo_3_track_12_event_1780126382412`
  - `live_20260530_163231_tapo_3_track_12_event_1780126385342`
  - `live_20260530_163231_tapo_3_track_21_event_1780126405901`
- `group_003` count=2 truth_counts={'p3': 1, 'p4': 1} pairwise={'count': 1, 'min': 0.658313, 'mean': 0.658313, 'median': 0.658313, 'max': 0.658313}
  - `live_20260530_163231_tapo_1_track_1_event_1780126354502`
  - `live_20260530_163231_tapo_1_track_13_event_1780126390303`

## Export

- Best grouping export: `snapshots/live_topk/20260530_163231/similarity_groups_truth_tuned_topcrops`
