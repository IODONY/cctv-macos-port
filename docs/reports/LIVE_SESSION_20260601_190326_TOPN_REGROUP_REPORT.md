# Live Session Regroup Report

This report is generated from saved live gallery clips and saved ReID crops. It does not run cameras.

## Summary

- Session: `20260601_190326`
- Events: `logs/topk_live/20260601_190326/gallery_events.jsonl`
- Output: `snapshots/live_topk/20260601_190326/similarity_groups_merged_topn_test`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Embedding aggregation: `topn`
- Method: `reciprocal`
- Threshold: `0.65`
- Reciprocal top-N: `4`
- Records grouped: `30`
- Group count: `8`
- Group sizes: `[9, 8, 5, 3, 2, 1, 1, 1]`
- Failures: `0`

## Groups

| group | clips | pairwise min | pairwise mean | pairwise max | members |
| --- | ---: | ---: | ---: | ---: | --- |
| group_001 | 9 | 0.398443 | 0.619626 | 0.858816 | live_20260601_190326_tapo_1_t004_e273786, live_20260601_190326_tapo_5_t001_e334691, live_20260601_190326_tapo_5_t001_e397057, live_20260601_190326_tapo_4_t009_e397216, live_20260601_190326_tapo_1_t002_e398333, live_20260601_190326_tapo_4_t010_e429015, live_20260601_190326_tapo_4_t019_e460921, live_20260601_190326_tapo_5_t005_e460330... |
| group_002 | 8 | 0.541735 | 0.742777 | 0.952489 | live_20260601_190326_tapo_5_t001_e274264, live_20260601_190326_tapo_5_t005_e336838, live_20260601_190326_tapo_5_t005_e397058, live_20260601_190326_tapo_4_t010_e397217, live_20260601_190326_tapo_1_t004_e396867, live_20260601_190326_tapo_4_t009_e460522, live_20260601_190326_tapo_5_t016_e460586, live_20260601_190326_tapo_1_t020_e461024 |
| group_003 | 5 | 0.765006 | 0.819257 | 0.895211 | live_20260601_190326_tapo_5_t002_e274265, live_20260601_190326_tapo_1_t003_e272327, live_20260601_190326_tapo_3_t002_e304550, live_20260601_190326_tapo_1_t003_e396867, live_20260601_190326_tapo_3_t025_e464760 |
| group_004 | 3 | 0.662655 | 0.716647 | 0.812809 | live_20260601_190326_tapo_3_t001_e274065, live_20260601_190326_tapo_5_t006_e366688, live_20260601_190326_tapo_5_t007_e396737 |
| group_005 | 2 | 0.689583 | 0.689583 | 0.689583 | live_20260601_190326_tapo_1_t014_e400162, live_20260601_190326_tapo_1_t014_e460408 |
| group_006 | 1 | None | None | None | live_20260601_190326_tapo_1_t001_e210160 |
| group_007 | 1 | None | None | None | live_20260601_190326_tapo_3_t002_e274067 |
| group_008 | 1 | None | None | None | live_20260601_190326_tapo_1_t002_e240922 |
