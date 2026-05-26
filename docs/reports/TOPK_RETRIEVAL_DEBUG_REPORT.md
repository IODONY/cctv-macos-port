# Top-K Retrieval Debug Report

This report inspects retrieval failures and high-risk candidates without running cameras, RTSP, TouchDesigner, or full tracking.

## Worst Queries

| query | identity | own@9 | wrong@9 | hard_negative_rate@9 | margin_to_wrong_high_risk | top wrong candidates |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| person_001_cam_1_02 | person_001 | 0 | 9 | 0.2222 | -0.1798 | person_002_cam_2_04:ambiguous:0.81, person_002_cam_2_02:ambiguous:0.7979, person_002_cam_2_01:ambiguous:0.7979, person_002_cam_4_01:ambiguous:0.7668, person_002_cam_1_01:ambiguous:0.7379 |
| person_001_cam_1_01 | person_001 | 2 | 7 | 0.3333 | -0.1193 | person_003_cam_1_02:ambiguous:0.6339, person_002_cam_2_02:ambiguous:0.6008, person_002_cam_2_01:ambiguous:0.6008, person_003_cam_4_01:ambiguous:0.5586, person_003_cam_2_01:ambiguous:0.5339 |
| person_001_cam_2_02 | person_001 | 2 | 7 | 0.2222 | -0.1073 | person_003_cam_1_03:ambiguous:0.6517, person_002_cam_2_04:ambiguous:0.6216, person_003_cam_1_01:ambiguous:0.5613, person_003_cam_1_04:ambiguous:0.5563, person_002_cam_1_01:ambiguous:0.5498 |
| person_001_cam_2_01 | person_001 | 3 | 6 | 0.3333 | -0.1388 | person_002_cam_2_02:ambiguous:0.5983, person_002_cam_2_01:ambiguous:0.5983, person_002_cam_2_04:ambiguous:0.4996, person_003_cam_1_02:ambiguous:0.4984, person_003_cam_1_01:ambiguous:0.4868 |
| person_003_cam_1_01 | person_003 | 4 | 5 | 0.2222 | -0.129 | person_002_cam_2_04:ambiguous:0.7046, person_002_cam_1_01:ambiguous:0.6713, person_001_cam_2_02:ambiguous:0.5613, person_001_cam_1_02:ambiguous:0.5581, person_002_cam_2_02:ambiguous:0.5423 |
| person_003_cam_1_02 | person_003 | 4 | 5 | 0.2222 | -0.0767 | person_002_cam_2_02:ambiguous:0.6562, person_002_cam_2_01:ambiguous:0.6562, person_001_cam_1_01:ambiguous:0.6339, person_002_cam_1_01:ambiguous:0.6213, person_002_cam_4_01:ambiguous:0.5572 |
| person_003_cam_3_01 | person_003 | 4 | 5 | 0.0 | 0.3477 | person_002_cam_1_01:ambiguous:0.5373, person_002_cam_4_01:ambiguous:0.531, person_002_cam_2_02:ambiguous:0.5253, person_002_cam_2_01:ambiguous:0.5253, person_001_cam_1_02:ambiguous:0.518 |
| person_003_cam_4_01 | person_003 | 4 | 5 | 0.0 | 0.0017 | person_002_cam_2_02:ambiguous:0.567, person_002_cam_2_01:ambiguous:0.567, person_001_cam_1_01:ambiguous:0.5586, person_002_cam_1_01:ambiguous:0.5525, person_001_cam_2_02:ambiguous:0.5369 |

## Hard Negatives In Top-K

| query | candidate | rank | score | outcome | reasons |
| --- | --- | ---: | ---: | --- | --- |
| person_001_cam_1_01 | person_003_cam_1_02 | 3 | 0.6339 | ambiguous |  |
| person_001_cam_1_01 | person_002_cam_1_01 | 8 | 0.5256 | ambiguous |  |
| person_001_cam_1_01 | person_003_cam_1_03 | 9 | 0.5146 | ambiguous |  |
| person_001_cam_1_02 | person_002_cam_1_01 | 5 | 0.7379 | ambiguous |  |
| person_001_cam_1_02 | person_003_cam_1_01 | 9 | 0.5581 | ambiguous |  |
| person_001_cam_2_01 | person_002_cam_2_02 | 3 | 0.5983 | ambiguous |  |
| person_001_cam_2_01 | person_002_cam_2_01 | 4 | 0.5983 | ambiguous |  |
| person_001_cam_2_01 | person_002_cam_2_04 | 5 | 0.4996 | ambiguous |  |
| person_001_cam_2_02 | person_002_cam_2_04 | 4 | 0.6216 | ambiguous |  |
| person_001_cam_2_02 | person_002_cam_2_02 | 9 | 0.5143 | ambiguous |  |
| person_002_cam_1_01 | person_001_cam_1_02 | 6 | 0.7379 | ambiguous |  |
| person_002_cam_1_01 | person_003_cam_1_03 | 8 | 0.6786 | ambiguous |  |
| person_002_cam_1_01 | person_003_cam_1_01 | 9 | 0.6713 | ambiguous |  |
| person_002_cam_2_01 | person_003_cam_2_01 | 9 | 0.6311 | ambiguous |  |
| person_002_cam_2_02 | person_003_cam_2_01 | 9 | 0.6311 | ambiguous |  |
| person_002_cam_2_03 | person_003_cam_2_01 | 9 | 0.2528 | no_match | top_and_bag_mismatch |
| person_002_cam_2_04 | person_001_cam_2_02 | 9 | 0.6216 | ambiguous |  |
| person_003_cam_1_01 | person_002_cam_1_01 | 6 | 0.6713 | ambiguous |  |
| person_003_cam_1_01 | person_001_cam_1_02 | 8 | 0.5581 | ambiguous |  |
| person_003_cam_1_02 | person_001_cam_1_01 | 7 | 0.6339 | ambiguous |  |
| person_003_cam_1_02 | person_002_cam_1_01 | 8 | 0.6213 | ambiguous |  |
| person_003_cam_1_03 | person_002_cam_1_01 | 5 | 0.6786 | ambiguous |  |
| person_003_cam_1_04 | person_002_cam_1_01 | 5 | 0.6343 | ambiguous |  |
| person_003_cam_2_01 | person_002_cam_2_02 | 6 | 0.6311 | ambiguous |  |
| person_003_cam_2_01 | person_002_cam_2_01 | 7 | 0.6311 | ambiguous |  |
