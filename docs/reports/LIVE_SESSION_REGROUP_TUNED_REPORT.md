# Live Session Regroup Report

This report is generated from saved live gallery clips and best ReID crops. It does not run cameras.

## Summary

- Session: `20260530_163231`
- Events: `logs/topk_live/20260530_163231/gallery_events.jsonl`
- Output: `snapshots/live_topk/20260530_163231/similarity_groups_default_tuned`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Method: `reciprocal`
- Threshold: `0.6`
- Reciprocal top-N: `3`
- Records grouped: `11`
- Group count: `4`
- Group sizes: `[5, 4, 1, 1]`
- Failures: `0`

## Groups

| group | clips | pairwise min | pairwise mean | pairwise max | members |
| --- | ---: | ---: | ---: | ---: | --- |
| group_001 | 5 | 0.724591 | 0.767039 | 0.799964 | live_20260530_163231_tapo_3_track_1_event_1780126356481, live_20260530_163231_tapo_3_track_1_event_1780126386562, live_20260530_163231_tapo_1_track_18_event_1780126396392, live_20260530_163231_tapo_2_track_17_event_1780126395913, live_20260530_163231_tapo_3_track_22_event_1780126409174 |
| group_002 | 4 | 0.578522 | 0.693698 | 0.799276 | live_20260530_163231_tapo_3_track_8_event_1780126376551, live_20260530_163231_tapo_3_track_12_event_1780126382412, live_20260530_163231_tapo_3_track_12_event_1780126385342, live_20260530_163231_tapo_3_track_21_event_1780126405901 |
| group_003 | 1 | None | None | None | live_20260530_163231_tapo_1_track_1_event_1780126354502 |
| group_004 | 1 | None | None | None | live_20260530_163231_tapo_1_track_13_event_1780126390303 |
