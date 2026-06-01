# Live Similarity Truth Evaluation

This report compares automatic live similarity grouping against a manually sorted truth folder.

## Summary

- Session: `20260530_225714`
- Events: `logs/topk_live/20260530_225714/gallery_events.jsonl`
- Truth root: `snapshots/live_topk/20260530_225714/similarity_groups_merged`
- Embedding source: `best-crops`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Records embedded: `69`
- Embedding failures: `0`
- Duplicate truth policy: `exclude`
- Truth conflicts: `0`

## Best Configuration

- Method: `reciprocal`
- Threshold: `0.65`
- Reciprocal top-N: `4`
- Predicted group count: `14`
- Predicted sizes: `[16, 11, 7, 7, 7, 6, 5, 2, 2, 2, 1, 1, 1, 1]`
- Pairwise F1: `0.756677`
- Pairwise precision: `0.958647`
- Pairwise recall: `0.625`
- Purity: `0.970588`
- Over-merged different-person pairs: `11`
- Split same-person pairs: `153`

## Truth Labels

| label | clips |
| --- | ---: |
| `p1` | 15 |
| `p2` | 14 |
| `p3` | 7 |
| `p4` | 8 |
| `p5_isNotHuman` | 1 |
| `p6` | 18 |
| `p7` | 5 |

## Top Configurations

| rank | method | threshold | top-N | groups | sizes | pair F1 | precision | recall | purity | overmerge | split |
| ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | reciprocal | 0.65 | 4 | 14 | [16, 11, 7, 7, 7, 6, 5, 2, 2, 2, 1, 1, 1, 1] | 0.756677 | 0.958647 | 0.625 | 0.970588 | 11 | 153 |
| 2 | centroid | 0.65 | 1 | 14 | [18, 18, 7, 5, 4, 3, 3, 2, 2, 2, 2, 1, 1, 1] | 0.727989 | 0.784703 | 0.678922 | 0.926471 | 76 | 131 |
| 3 | reciprocal | 0.45 | 4 | 12 | [16, 15, 11, 7, 6, 5, 2, 2, 2, 1, 1, 1] | 0.705394 | 0.809524 | 0.625 | 0.867647 | 60 | 153 |
| 4 | reciprocal | 0.5 | 4 | 12 | [16, 15, 11, 7, 6, 5, 2, 2, 2, 1, 1, 1] | 0.705394 | 0.809524 | 0.625 | 0.867647 | 60 | 153 |
| 5 | reciprocal | 0.55 | 4 | 12 | [16, 15, 11, 7, 6, 5, 2, 2, 2, 1, 1, 1] | 0.705394 | 0.809524 | 0.625 | 0.867647 | 60 | 153 |
| 6 | reciprocal | 0.6 | 4 | 12 | [16, 15, 11, 7, 6, 5, 2, 2, 2, 1, 1, 1] | 0.705394 | 0.809524 | 0.625 | 0.867647 | 60 | 153 |
| 7 | reciprocal | 0.65 | 5 | 12 | [23, 11, 7, 7, 7, 6, 2, 2, 1, 1, 1, 1] | 0.680905 | 0.698454 | 0.664216 | 0.897059 | 117 | 137 |
| 8 | reciprocal | 0.7 | 4 | 21 | [16, 11, 7, 6, 4, 3, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1] | 0.680315 | 0.951542 | 0.529412 | 0.970588 | 11 | 192 |
| 9 | reciprocal | 0.45 | 6 | 7 | [25, 22, 12, 6, 2, 1, 1] | 0.664 | 0.560811 | 0.813725 | 0.764706 | 260 | 76 |
| 10 | reciprocal | 0.5 | 6 | 7 | [25, 22, 12, 6, 2, 1, 1] | 0.664 | 0.560811 | 0.813725 | 0.764706 | 260 | 76 |
| 11 | reciprocal | 0.55 | 6 | 7 | [25, 22, 12, 6, 2, 1, 1] | 0.664 | 0.560811 | 0.813725 | 0.764706 | 260 | 76 |
| 12 | reciprocal | 0.6 | 6 | 7 | [25, 22, 12, 6, 2, 1, 1] | 0.664 | 0.560811 | 0.813725 | 0.764706 | 260 | 76 |
| 13 | reciprocal | 0.65 | 6 | 10 | [25, 12, 7, 7, 7, 6, 2, 1, 1, 1] | 0.66354 | 0.635955 | 0.693627 | 0.867647 | 162 | 125 |
| 14 | centroid | 0.5 | 1 | 3 | [24, 23, 22] | 0.657367 | 0.510149 | 0.92402 | 0.661765 | 362 | 31 |
| 15 | centroid | 0.55 | 1 | 3 | [24, 23, 22] | 0.657367 | 0.510149 | 0.92402 | 0.661765 | 362 | 31 |
| 16 | centroid | 0.6 | 1 | 7 | [23, 23, 8, 7, 5, 2, 1] | 0.647423 | 0.558719 | 0.769608 | 0.764706 | 248 | 94 |
| 17 | reciprocal | 0.7 | 6 | 18 | [22, 12, 7, 6, 3, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1] | 0.645333 | 0.707602 | 0.593137 | 0.911765 | 100 | 166 |
| 18 | reciprocal | 0.75 | 4 | 27 | [16, 11, 7, 3, 3, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] | 0.645057 | 0.952153 | 0.487745 | 0.985294 | 10 | 209 |
| 19 | reciprocal | 0.45 | 5 | 10 | [23, 15, 11, 7, 6, 2, 2, 1, 1, 1] | 0.64142 | 0.620137 | 0.664216 | 0.794118 | 166 | 137 |
| 20 | reciprocal | 0.5 | 5 | 10 | [23, 15, 11, 7, 6, 2, 2, 1, 1, 1] | 0.64142 | 0.620137 | 0.664216 | 0.794118 | 166 | 137 |

## Best Predicted Groups

- `group_001` count=16 truth_counts={'p6': 16} pairwise={'count': 120, 'min': 0.486102, 'mean': 0.677925, 'median': 0.701085, 'max': 0.953653}
  - `live_20260530_225714_tapo_3_t014_e469843`
  - `live_20260530_225714_tapo_3_t024_e479299`
  - `live_20260530_225714_tapo_3_t025_e484113`
  - `live_20260530_225714_tapo_3_t026_e488575`
  - `live_20260530_225714_tapo_3_t029_e493579`
  - `live_20260530_225714_tapo_3_t026_e495061`
  - `live_20260530_225714_tapo_3_t036_e499840`
  - `live_20260530_225714_tapo_3_t036_e508773`
  - `live_20260530_225714_tapo_3_t038_e509895`
  - `live_20260530_225714_tapo_3_t036_e512321`
  - `live_20260530_225714_tapo_3_t045_e527415`
  - `live_20260530_225714_tapo_3_t047_e530374`
  - `live_20260530_225714_tapo_1_t049_e537913`
  - `live_20260530_225714_tapo_1_t099_e676150`
  - `live_20260530_225714_tapo_1_t099_e695547`
  - `live_20260530_225714_tapo_1_t099_e725682`
- `group_002` count=11 truth_counts={'p1': 10, 'p6': 1} pairwise={'count': 55, 'min': 0.688277, 'mean': 0.803398, 'median': 0.802398, 'max': 0.910899}
  - `live_20260530_225714_tapo_3_t030_e494589`
  - `live_20260530_225714_tapo_3_t035_e498342`
  - `live_20260530_225714_tapo_1_t042_e521376`
  - `live_20260530_225714_tapo_1_t056_e552085`
  - `live_20260530_225714_tapo_3_t066_e565104`
  - `live_20260530_225714_tapo_3_t066_e595183`
  - `live_20260530_225714_tapo_3_t078_e597433`
  - `live_20260530_225714_tapo_3_t087_e635508`
  - `live_20260530_225714_tapo_3_t094_e657769`
  - `live_20260530_225714_tapo_1_t102_e685685`
  - `live_20260530_225714_tapo_3_t119_e707261`
- `group_003` count=7 truth_counts={'p2': 7} pairwise={'count': 21, 'min': 0.402127, 'mean': 0.580761, 'median': 0.574653, 'max': 0.81102}
  - `live_20260530_225714_tapo_3_t002_e439587`
  - `live_20260530_225714_tapo_3_t008_e460776`
  - `live_20260530_225714_tapo_2_t054_e548941`
  - `live_20260530_225714_tapo_1_t071_e567397`
  - `live_20260530_225714_tapo_2_t063_e559755`
  - `live_20260530_225714_tapo_2_t063_e591766`
  - `live_20260530_225714_tapo_1_t076_e586473`
- `group_004` count=7 truth_counts={'p2': 7} pairwise={'count': 21, 'min': 0.632103, 'mean': 0.770192, 'median': 0.747546, 'max': 0.882053}
  - `live_20260530_225714_tapo_1_t052_e546261`
  - `live_20260530_225714_tapo_2_t085_e612091`
  - `live_20260530_225714_tapo_1_t076_e616540`
  - `live_20260530_225714_tapo_2_t085_e642175`
  - `live_20260530_225714_tapo_1_t076_e646695`
  - `live_20260530_225714_tapo_2_t097_e663445`
  - `live_20260530_225714_tapo_1_t096_e661378`
- `group_005` count=7 truth_counts={'p3': 7} pairwise={'count': 21, 'min': 0.572377, 'mean': 0.687704, 'median': 0.645597, 'max': 0.981492}
  - `live_20260530_225714_tapo_3_t091_e651591`
  - `live_20260530_225714_tapo_3_t103_e688430`
  - `live_20260530_225714_tapo_1_t108_e691069`
  - `live_20260530_225714_tapo_1_t110_e693876`
  - `live_20260530_225714_tapo_3_t121_e714384`
  - `live_20260530_225714_tapo_1_t120_e711734`
  - `live_20260530_225714_tapo_1_t122_e725683`
- `group_006` count=6 truth_counts={'p4': 6} pairwise={'count': 15, 'min': 0.574076, 'mean': 0.685197, 'median': 0.692602, 'max': 0.80651}
  - `live_20260530_225714_tapo_1_t100_e679564`
  - `live_20260530_225714_tapo_2_t101_e682115`
  - `live_20260530_225714_tapo_2_t106_e690603`
  - `live_20260530_225714_tapo_1_t099_e689389`
  - `live_20260530_225714_tapo_2_t109_e693638`
  - `live_20260530_225714_tapo_1_t107_e690695`
- `group_007` count=5 truth_counts={'p7': 5} pairwise={'count': 10, 'min': 0.515164, 'mean': 0.682112, 'median': 0.679291, 'max': 0.809074}
  - `live_20260530_225714_tapo_3_t003_e456104`
  - `live_20260530_225714_tapo_3_t003_e486252`
  - `live_20260530_225714_tapo_3_t003_e516335`
  - `live_20260530_225714_tapo_3_t051_e546213`
  - `live_20260530_225714_tapo_1_t069_e567086`
- `group_008` count=2 truth_counts={'p4': 2} pairwise={'count': 1, 'min': 0.842471, 'mean': 0.842471, 'median': 0.842471, 'max': 0.842471}
  - `live_20260530_225714_tapo_1_t018_e473329`
  - `live_20260530_225714_tapo_1_t098_e674483`
- `group_009` count=2 truth_counts={'p1': 1, 'p6': 1} pairwise={'count': 1, 'min': 0.704276, 'mean': 0.704276, 'median': 0.704276, 'max': 0.704276}
  - `live_20260530_225714_tapo_1_t067_e565159`
  - `live_20260530_225714_tapo_1_t065_e564326`
- `group_010` count=2 truth_counts={'p1': 2} pairwise={'count': 1, 'min': 0.749299, 'mean': 0.749299, 'median': 0.749299, 'max': 0.749299}
  - `live_20260530_225714_tapo_2_t083_e609651`
  - `live_20260530_225714_tapo_2_t104_e688959`
- `group_011` count=1 truth_counts={'p5_isNotHuman': 1} pairwise={'count': 0, 'min': None, 'mean': None, 'median': None, 'max': None}
  - `live_20260530_225714_tapo_2_t039_e513019`
- `group_012` count=1 truth_counts={'p1': 1} pairwise={'count': 0, 'min': None, 'mean': None, 'median': None, 'max': None}
  - `live_20260530_225714_tapo_1_t057_e553767`
- `group_013` count=1 truth_counts={'unlabeled': 1} pairwise={'count': 0, 'min': None, 'mean': None, 'median': None, 'max': None}
  - `live_20260530_225714_tapo_1_t074_e578120`
- `group_014` count=1 truth_counts={'p1': 1} pairwise={'count': 0, 'min': None, 'mean': None, 'median': None, 'max': None}
  - `live_20260530_225714_tapo_1_t081_e605327`
