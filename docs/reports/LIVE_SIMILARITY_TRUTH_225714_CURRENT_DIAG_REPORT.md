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
- Reciprocal top-N: `8`
- Predicted group count: `6`
- Predicted sizes: `[44, 14, 7, 2, 1, 1]`
- Pairwise F1: `0.539877`
- Pairwise precision: `0.373938`
- Pairwise recall: `0.970588`
- Purity: `0.617647`
- Over-merged different-person pairs: `663`
- Split same-person pairs: `12`

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
| 1 | reciprocal | 0.65 | 8 | 6 | [44, 14, 7, 2, 1, 1] | 0.539877 | 0.373938 | 0.970588 | 0.617647 | 663 | 12 |

## Best Predicted Groups

- `group_001` count=44 truth_counts={'p1': 15, 'p4': 6, 'p6': 18, 'p7': 5} pairwise={'count': 946, 'min': 0.338168, 'mean': 0.592367, 'median': 0.579448, 'max': 0.953653}
  - `live_20260530_225714_tapo_3_t014_e469843`
  - `live_20260530_225714_tapo_3_t024_e479299`
  - `live_20260530_225714_tapo_3_t003_e456104`
  - `live_20260530_225714_tapo_3_t025_e484113`
  - `live_20260530_225714_tapo_3_t026_e488575`
  - `live_20260530_225714_tapo_3_t029_e493579`
  - `live_20260530_225714_tapo_3_t026_e495061`
  - `live_20260530_225714_tapo_3_t030_e494589`
  - `live_20260530_225714_tapo_3_t036_e499840`
  - `live_20260530_225714_tapo_3_t036_e508773`
  - `live_20260530_225714_tapo_3_t038_e509895`
  - `live_20260530_225714_tapo_3_t003_e486252`
  - `live_20260530_225714_tapo_3_t035_e498342`
  - `live_20260530_225714_tapo_3_t036_e512321`
  - `live_20260530_225714_tapo_3_t045_e527415`
  - `live_20260530_225714_tapo_3_t047_e530374`
  - `live_20260530_225714_tapo_3_t003_e516335`
  - `live_20260530_225714_tapo_1_t042_e521376`
  - `live_20260530_225714_tapo_1_t049_e537913`
  - `live_20260530_225714_tapo_3_t051_e546213`
  - `live_20260530_225714_tapo_1_t056_e552085`
  - `live_20260530_225714_tapo_1_t057_e553767`
  - `live_20260530_225714_tapo_1_t067_e565159`
  - `live_20260530_225714_tapo_1_t065_e564326`
  - `live_20260530_225714_tapo_1_t069_e567086`
  - `live_20260530_225714_tapo_3_t066_e565104`
  - `live_20260530_225714_tapo_3_t066_e595183`
  - `live_20260530_225714_tapo_3_t078_e597433`
  - `live_20260530_225714_tapo_2_t083_e609651`
  - `live_20260530_225714_tapo_1_t081_e605327`
  - `live_20260530_225714_tapo_3_t087_e635508`
  - `live_20260530_225714_tapo_3_t094_e657769`
  - `live_20260530_225714_tapo_1_t099_e676150`
  - `live_20260530_225714_tapo_1_t100_e679564`
  - `live_20260530_225714_tapo_2_t101_e682115`
  - `live_20260530_225714_tapo_2_t106_e690603`
  - `live_20260530_225714_tapo_1_t099_e689389`
  - `live_20260530_225714_tapo_2_t104_e688959`
  - `live_20260530_225714_tapo_2_t109_e693638`
  - `live_20260530_225714_tapo_1_t102_e685685`
  - `live_20260530_225714_tapo_1_t107_e690695`
  - `live_20260530_225714_tapo_1_t099_e695547`
  - `live_20260530_225714_tapo_1_t099_e725682`
  - `live_20260530_225714_tapo_3_t119_e707261`
- `group_002` count=14 truth_counts={'p2': 14} pairwise={'count': 91, 'min': 0.402127, 'mean': 0.613183, 'median': 0.581454, 'max': 0.882053}
  - `live_20260530_225714_tapo_3_t002_e439587`
  - `live_20260530_225714_tapo_3_t008_e460776`
  - `live_20260530_225714_tapo_2_t054_e548941`
  - `live_20260530_225714_tapo_1_t052_e546261`
  - `live_20260530_225714_tapo_1_t071_e567397`
  - `live_20260530_225714_tapo_2_t063_e559755`
  - `live_20260530_225714_tapo_2_t063_e591766`
  - `live_20260530_225714_tapo_1_t076_e586473`
  - `live_20260530_225714_tapo_2_t085_e612091`
  - `live_20260530_225714_tapo_1_t076_e616540`
  - `live_20260530_225714_tapo_2_t085_e642175`
  - `live_20260530_225714_tapo_1_t076_e646695`
  - `live_20260530_225714_tapo_2_t097_e663445`
  - `live_20260530_225714_tapo_1_t096_e661378`
- `group_003` count=7 truth_counts={'p3': 7} pairwise={'count': 21, 'min': 0.572377, 'mean': 0.687704, 'median': 0.645597, 'max': 0.981492}
  - `live_20260530_225714_tapo_3_t091_e651591`
  - `live_20260530_225714_tapo_3_t103_e688430`
  - `live_20260530_225714_tapo_1_t108_e691069`
  - `live_20260530_225714_tapo_1_t110_e693876`
  - `live_20260530_225714_tapo_3_t121_e714384`
  - `live_20260530_225714_tapo_1_t120_e711734`
  - `live_20260530_225714_tapo_1_t122_e725683`
- `group_004` count=2 truth_counts={'p4': 2} pairwise={'count': 1, 'min': 0.842471, 'mean': 0.842471, 'median': 0.842471, 'max': 0.842471}
  - `live_20260530_225714_tapo_1_t018_e473329`
  - `live_20260530_225714_tapo_1_t098_e674483`
- `group_005` count=1 truth_counts={'p5_isNotHuman': 1} pairwise={'count': 0, 'min': None, 'mean': None, 'median': None, 'max': None}
  - `live_20260530_225714_tapo_2_t039_e513019`
- `group_006` count=1 truth_counts={'unlabeled': 1} pairwise={'count': 0, 'min': None, 'mean': None, 'median': None, 'max': None}
  - `live_20260530_225714_tapo_1_t074_e578120`
