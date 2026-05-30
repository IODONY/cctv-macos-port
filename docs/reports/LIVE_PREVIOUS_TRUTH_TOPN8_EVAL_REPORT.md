# Live Similarity Truth Evaluation

This report compares automatic live similarity grouping against a manually sorted truth folder.

## Summary

- Session: `20260530_163231`
- Events: `logs/topk_live/20260530_163231/gallery_events.jsonl`
- Truth root: `snapshots/live_topk/20260530_163231/similarity_groups_merged/group_001/jpg`
- Embedding source: `best-crops`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Records embedded: `11`
- Embedding failures: `0`
- Duplicate truth policy: `exclude`
- Truth conflicts: `0`

## Best Configuration

- Method: `reciprocal`
- Threshold: `0.65`
- Reciprocal top-N: `8`
- Predicted group count: `4`
- Predicted sizes: `[5, 4, 1, 1]`
- Pairwise F1: `1.0`
- Pairwise precision: `1.0`
- Pairwise recall: `1.0`
- Purity: `1.0`
- Over-merged different-person pairs: `0`
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
| 1 | reciprocal | 0.65 | 8 | 4 | [5, 4, 1, 1] | 1.0 | 1.0 | 1.0 | 1.0 | 0 | 0 |

## Best Predicted Groups

- `group_001` count=5 truth_counts={'p1': 5} pairwise={'count': 10, 'min': 0.724591, 'mean': 0.767039, 'median': 0.77163, 'max': 0.799964}
  - `live_20260530_163231_tapo_3_track_1_event_1780126356481`
  - `live_20260530_163231_tapo_3_track_1_event_1780126386562`
  - `live_20260530_163231_tapo_1_track_18_event_1780126396392`
  - `live_20260530_163231_tapo_2_track_17_event_1780126395913`
  - `live_20260530_163231_tapo_3_track_22_event_1780126409174`
- `group_002` count=4 truth_counts={'p2': 4} pairwise={'count': 6, 'min': 0.578522, 'mean': 0.693698, 'median': 0.691896, 'max': 0.799276}
  - `live_20260530_163231_tapo_3_track_8_event_1780126376551`
  - `live_20260530_163231_tapo_3_track_12_event_1780126382412`
  - `live_20260530_163231_tapo_3_track_12_event_1780126385342`
  - `live_20260530_163231_tapo_3_track_21_event_1780126405901`
- `group_003` count=1 truth_counts={'p3': 1} pairwise={'count': 0, 'min': None, 'mean': None, 'median': None, 'max': None}
  - `live_20260530_163231_tapo_1_track_1_event_1780126354502`
- `group_004` count=1 truth_counts={'p4': 1} pairwise={'count': 0, 'min': None, 'mean': None, 'median': None, 'max': None}
  - `live_20260530_163231_tapo_1_track_13_event_1780126390303`
