# Top-K Retrieval Evaluation Report

- Clips manifest: `data/labels/clips.csv`
- Query count: `18`
- Gallery count: `18`
- K: `9`
- Candidate pool: `12`
- Match threshold: `0.72`
- Ambiguous threshold: `0.25`

## Summary Metrics

- `max_own_at_9`: `6`
- `mean_ambiguous_rate_at_9`: `0.7037`
- `mean_false_match_rate_at_9`: `0.0`
- `mean_hard_negative_rate_at_9`: `0.1543`
- `mean_own_at_12`: `4.8889`
- `mean_own_at_9`: `4.4444`
- `mean_precision_at_12`: `0.4074`
- `mean_precision_at_9`: `0.4938`
- `mean_recall_at_12`: `0.8889`
- `mean_recall_at_9`: `0.8056`
- `mean_wrong_at_12`: `7.1111`
- `mean_wrong_at_9`: `4.5556`
- `min_own_at_9`: `0`
- `queries_with_majority_own_at_9`: `10`
- `query_count`: `18`

## Per Query Top-K

| query | identity | positives_available | own@9 | wrong@9 | recall@9 | precision@9 | ambiguous_rate@9 | false_match_rate@9 | top candidates |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| person_001_cam_1_01 | person_001 | 3 | 2 | 7 | 0.6667 | 0.2222 | 0.7778 | 0.0 | person_001_cam_2_02:matched:0.9772, person_001_cam_2_01:matched:0.9539, person_003_cam_1_02:ambiguous:0.6339, person_002_cam_2_02:ambiguous:0.6008, person_002_cam_2_01:ambiguous:0.6008, person_003_cam_4_01:ambiguous:0.5586, person_003_cam_2_01:ambiguous:0.5339, person_002_cam_1_01:ambiguous:0.5256, person_003_cam_1_03:ambiguous:0.5146 |
| person_001_cam_1_02 | person_001 | 3 | 0 | 9 | 0.0 | 0.0 | 1.0 | 0.0 | person_002_cam_2_04:ambiguous:0.81, person_002_cam_2_02:ambiguous:0.7979, person_002_cam_2_01:ambiguous:0.7979, person_002_cam_4_01:ambiguous:0.7668, person_002_cam_1_01:ambiguous:0.7379, person_002_cam_2_03:ambiguous:0.691, person_002_cam_3_01:ambiguous:0.6677, person_003_cam_2_01:ambiguous:0.5632, person_003_cam_1_01:ambiguous:0.5581 |
| person_001_cam_2_01 | person_001 | 3 | 3 | 6 | 1.0 | 0.3333 | 0.8889 | 0.0 | person_001_cam_1_01:matched:0.9539, person_001_cam_2_02:ambiguous:0.7902, person_002_cam_2_02:ambiguous:0.5983, person_002_cam_2_01:ambiguous:0.5983, person_002_cam_2_04:ambiguous:0.4996, person_003_cam_1_02:ambiguous:0.4984, person_001_cam_1_02:ambiguous:0.4937, person_003_cam_1_01:ambiguous:0.4868, person_003_cam_1_03:ambiguous:0.4595 |
| person_001_cam_2_02 | person_001 | 3 | 2 | 7 | 0.6667 | 0.2222 | 0.8889 | 0.0 | person_001_cam_1_01:matched:0.9772, person_001_cam_2_01:ambiguous:0.7902, person_003_cam_1_03:ambiguous:0.6517, person_002_cam_2_04:ambiguous:0.6216, person_003_cam_1_01:ambiguous:0.5613, person_003_cam_1_04:ambiguous:0.5563, person_002_cam_1_01:ambiguous:0.5498, person_003_cam_4_01:ambiguous:0.5369, person_002_cam_2_02:ambiguous:0.5143 |
| person_002_cam_1_01 | person_002 | 6 | 6 | 3 | 1.0 | 0.6667 | 0.4444 | 0.0 | person_002_cam_2_02:matched:1.0, person_002_cam_2_01:matched:1.0, person_002_cam_2_04:matched:0.9688, person_002_cam_4_01:matched:0.9072, person_002_cam_2_03:matched:0.902, person_001_cam_1_02:ambiguous:0.7379, person_002_cam_3_01:ambiguous:0.7239, person_003_cam_1_03:ambiguous:0.6786, person_003_cam_1_01:ambiguous:0.6713 |
| person_002_cam_2_01 | person_002 | 6 | 6 | 3 | 1.0 | 0.6667 | 0.5556 | 0.0 | person_002_cam_2_02:matched:1.0, person_002_cam_1_01:matched:1.0, person_002_cam_4_01:matched:0.9684, person_002_cam_2_03:matched:0.9471, person_002_cam_2_04:ambiguous:0.8157, person_001_cam_1_02:ambiguous:0.7979, person_002_cam_3_01:ambiguous:0.7345, person_003_cam_1_02:ambiguous:0.6562, person_003_cam_2_01:ambiguous:0.6311 |
| person_002_cam_2_02 | person_002 | 6 | 6 | 3 | 1.0 | 0.6667 | 0.5556 | 0.0 | person_002_cam_2_01:matched:1.0, person_002_cam_1_01:matched:1.0, person_002_cam_4_01:matched:0.9684, person_002_cam_2_03:matched:0.9471, person_002_cam_2_04:ambiguous:0.8157, person_001_cam_1_02:ambiguous:0.7979, person_002_cam_3_01:ambiguous:0.7345, person_003_cam_1_02:ambiguous:0.6562, person_003_cam_2_01:ambiguous:0.6311 |
| person_002_cam_2_03 | person_002 | 6 | 6 | 3 | 1.0 | 0.6667 | 0.3333 | 0.0 | person_002_cam_2_02:matched:0.9471, person_002_cam_2_01:matched:0.9471, person_002_cam_3_01:matched:0.9035, person_002_cam_1_01:matched:0.902, person_002_cam_4_01:ambiguous:0.7643, person_002_cam_2_04:ambiguous:0.6983, person_001_cam_1_02:ambiguous:0.691, person_003_cam_1_02:no_match:0.3396, person_003_cam_2_01:no_match:0.2528 |
| person_002_cam_2_04 | person_002 | 6 | 6 | 3 | 1.0 | 0.6667 | 0.7778 | 0.0 | person_002_cam_1_01:matched:0.9688, person_002_cam_4_01:matched:0.9156, person_002_cam_2_02:ambiguous:0.8157, person_002_cam_2_01:ambiguous:0.8157, person_001_cam_1_02:ambiguous:0.81, person_002_cam_3_01:ambiguous:0.7417, person_003_cam_1_01:ambiguous:0.7046, person_002_cam_2_03:ambiguous:0.6983, person_001_cam_2_02:ambiguous:0.6216 |
| person_002_cam_3_01 | person_002 | 6 | 6 | 3 | 1.0 | 0.6667 | 0.5556 | 0.0 | person_002_cam_4_01:matched:0.9184, person_002_cam_2_03:matched:0.9035, person_002_cam_2_04:ambiguous:0.7417, person_002_cam_2_02:ambiguous:0.7345, person_002_cam_2_01:ambiguous:0.7345, person_002_cam_1_01:ambiguous:0.7239, person_001_cam_1_02:ambiguous:0.6677, person_003_cam_1_03:no_match:0.2703, person_003_cam_1_04:no_match:0.2262 |
| person_002_cam_4_01 | person_002 | 6 | 6 | 3 | 1.0 | 0.6667 | 0.4444 | 0.0 | person_002_cam_2_02:matched:0.9684, person_002_cam_2_01:matched:0.9684, person_002_cam_3_01:matched:0.9184, person_002_cam_2_04:matched:0.9156, person_002_cam_1_01:matched:0.9072, person_001_cam_1_02:ambiguous:0.7668, person_002_cam_2_03:ambiguous:0.7643, person_003_cam_1_03:ambiguous:0.6043, person_003_cam_1_04:ambiguous:0.5813 |
| person_003_cam_1_01 | person_003 | 6 | 4 | 5 | 0.6667 | 0.4444 | 0.6667 | 0.0 | person_003_cam_1_04:matched:1.0, person_003_cam_1_03:matched:1.0, person_003_cam_2_01:matched:0.9048, person_003_cam_1_02:ambiguous:0.762, person_002_cam_2_04:ambiguous:0.7046, person_002_cam_1_01:ambiguous:0.6713, person_001_cam_2_02:ambiguous:0.5613, person_001_cam_1_02:ambiguous:0.5581, person_002_cam_2_02:ambiguous:0.5423 |
| person_003_cam_1_02 | person_003 | 6 | 4 | 5 | 0.6667 | 0.4444 | 0.8889 | 0.0 | person_003_cam_2_01:matched:0.9787, person_003_cam_1_03:ambiguous:0.7696, person_003_cam_1_01:ambiguous:0.762, person_003_cam_1_04:ambiguous:0.7338, person_002_cam_2_02:ambiguous:0.6562, person_002_cam_2_01:ambiguous:0.6562, person_001_cam_1_01:ambiguous:0.6339, person_002_cam_1_01:ambiguous:0.6213, person_002_cam_4_01:ambiguous:0.5572 |
| person_003_cam_1_03 | person_003 | 6 | 5 | 4 | 0.8333 | 0.5556 | 0.6667 | 0.0 | person_003_cam_1_04:matched:1.0, person_003_cam_1_01:matched:1.0, person_003_cam_2_01:matched:0.923, person_003_cam_1_02:ambiguous:0.7696, person_002_cam_1_01:ambiguous:0.6786, person_001_cam_2_02:ambiguous:0.6517, person_002_cam_2_04:ambiguous:0.6115, person_002_cam_4_01:ambiguous:0.6043, person_003_cam_4_01:ambiguous:0.5848 |
| person_003_cam_1_04 | person_003 | 6 | 5 | 4 | 0.8333 | 0.5556 | 0.6667 | 0.0 | person_003_cam_1_03:matched:1.0, person_003_cam_1_01:matched:1.0, person_003_cam_2_01:matched:0.8908, person_003_cam_1_02:ambiguous:0.7338, person_002_cam_1_01:ambiguous:0.6343, person_002_cam_2_04:ambiguous:0.6123, person_002_cam_4_01:ambiguous:0.5813, person_001_cam_2_02:ambiguous:0.5563, person_003_cam_4_01:ambiguous:0.5198 |
| person_003_cam_2_01 | person_003 | 6 | 5 | 4 | 0.8333 | 0.5556 | 0.5556 | 0.0 | person_003_cam_1_02:matched:0.9787, person_003_cam_1_03:matched:0.923, person_003_cam_1_01:matched:0.9048, person_003_cam_1_04:matched:0.8908, person_002_cam_1_01:ambiguous:0.6483, person_002_cam_2_02:ambiguous:0.6311, person_002_cam_2_01:ambiguous:0.6311, person_003_cam_3_01:ambiguous:0.5908, person_001_cam_1_02:ambiguous:0.5632 |
| person_003_cam_3_01 | person_003 | 6 | 4 | 5 | 0.6667 | 0.4444 | 1.0 | 0.0 | person_003_cam_2_01:ambiguous:0.5908, person_003_cam_1_02:ambiguous:0.5428, person_002_cam_1_01:ambiguous:0.5373, person_002_cam_4_01:ambiguous:0.531, person_002_cam_2_02:ambiguous:0.5253, person_002_cam_2_01:ambiguous:0.5253, person_001_cam_1_02:ambiguous:0.518, person_003_cam_1_03:ambiguous:0.496, person_003_cam_1_04:ambiguous:0.4935 |
| person_003_cam_4_01 | person_003 | 6 | 4 | 5 | 0.6667 | 0.4444 | 1.0 | 0.0 | person_003_cam_1_03:ambiguous:0.5848, person_002_cam_2_02:ambiguous:0.567, person_002_cam_2_01:ambiguous:0.567, person_001_cam_1_01:ambiguous:0.5586, person_003_cam_2_01:ambiguous:0.5556, person_002_cam_1_01:ambiguous:0.5525, person_003_cam_1_02:ambiguous:0.5483, person_001_cam_2_02:ambiguous:0.5369, person_003_cam_1_01:ambiguous:0.5296 |
