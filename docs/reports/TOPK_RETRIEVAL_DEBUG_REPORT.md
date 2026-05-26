# Top-K Retrieval Debug Report

This report inspects retrieval failures and high-risk candidates without running cameras, RTSP, TouchDesigner, or full tracking.

## Worst Queries

| query | dataset | identity | own@9 | wrong@9 | max_possible_own@9 | normalized_own_recall@9 | readiness | top wrong candidates |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527 | person_01 | 1 | 8 | 4 | 0.25 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_2_event_1779815845597:matched:1.0, test_clip_0527_person_03_cam_5_event_1779815845594:matched:1.0, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.9958, test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.9827, test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.9532 |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527 | person_04 | 2 | 7 | 2 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.898, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7591, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7063, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.6776, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.232 |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527 | person_04 | 2 | 7 | 2 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_5_event_1779815845594:matched:1.0, test_clip_0527_person_01_cam_5_event_1779815845586:matched:1.0, test_clip_0527_person_03_cam_1_event_1779815845592:matched:1.0, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.9988, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.535 |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527 | person_04 | 2 | 7 | 2 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_5_event_1779815845594:matched:1.0, test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.9722, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.964, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.9532, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6035 |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527 | person_01 | 3 | 6 | 4 | 0.75 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.6389, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.591, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.5471, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.5465, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.5271 |
| test_clip_0527_person_01_cam_4_event_1779815845585 | test_clip_0527 | person_01 | 3 | 6 | 4 | 0.75 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.674, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.5989, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.5684, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.5529, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.5486 |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_2_event_1779815845597:matched:1.0, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.9827, test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.9722, test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.898, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6389 |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_2_event_1779815845597:matched:0.9988, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.9958, test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.964, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6776, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.5529 |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.674, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6265, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.6035, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.535, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5208 |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_2_event_1779815845597:matched:1.0, test_clip_0527_person_04_cam_5_event_1779815845598:matched:1.0, test_clip_0527_person_01_cam_5_event_1779815845586:matched:1.0, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7591, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.5684 |

## Hard Negatives In Top-K

| query | candidate | rank | score | outcome | reasons |
| --- | --- | ---: | ---: | --- | --- |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_03_cam_1_event_1779815845592 | 4 | 0.6389 | ambiguous |  |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_02_cam_1_event_1779815845584 | 6 | 0.5471 | ambiguous |  |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_02_cam_1_event_1779819881971 | 7 | 0.5465 | ambiguous |  |
| test_clip_0527_person_01_cam_4_event_1779815845585 | test_clip_0527_person_03_cam_4_event_1779815845595 | 4 | 0.674 | ambiguous |  |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527_person_03_cam_5_event_1779815845594 | 2 | 1.0 | matched |  |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527_person_04_cam_5_event_1779815845598 | 5 | 0.9532 | matched |  |
| test_clip_0527_person_02_cam_1_event_1779815845584 | test_clip_0527_person_01_cam_1_event_1779815845583 | 9 | 0.5471 | ambiguous |  |
| test_clip_0527_person_02_cam_1_event_1779817469639 | test_clip_0527_person_01_cam_1_event_1779815845583 | 8 | 0.4959 | ambiguous |  |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527_person_04_cam_1_event_1779815845601 | 6 | 0.898 | matched |  |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527_person_01_cam_1_event_1779815845583 | 8 | 0.6389 | ambiguous |  |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527_person_04_cam_1_event_1779815845601 | 6 | 0.6776 | ambiguous |  |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527_person_01_cam_1_event_1779815845583 | 9 | 0.5232 | ambiguous |  |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527_person_01_cam_4_event_1779815845585 | 1 | 0.674 | ambiguous |  |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527_person_04_cam_5_event_1779815845598 | 3 | 1.0 | matched |  |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527_person_01_cam_5_event_1779815845586 | 5 | 1.0 | matched |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_03_cam_1_event_1779815845592 | 1 | 0.898 | matched |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_03_cam_1_event_1779815845596 | 6 | 0.6776 | ambiguous |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_01_cam_1_event_1779815845583 | 7 | 0.232 | no_match | top_and_bag_mismatch |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_02_cam_1_event_1779817469639 | 9 | 0.081 | no_match | top_and_bag_mismatch |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527_person_03_cam_5_event_1779815845594 | 2 | 1.0 | matched |  |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527_person_01_cam_5_event_1779815845586 | 5 | 0.9532 | matched |  |
