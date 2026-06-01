# Top-K Retrieval Debug Report

This report inspects retrieval failures and high-risk candidates without running cameras, RTSP, TouchDesigner, or full tracking.

## Worst Queries

| query | dataset | identity | own@9 | wrong@9 | max_possible_own@9 | normalized_own_recall@9 | readiness | top wrong candidates |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527 | person_01 | 1 | 8 | 4 | 0.25 | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.9068, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8883, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8766, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8387, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8371 |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527 | person_04 | 2 | 7 | 2 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.9755, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.961, test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.908, test_clip_0527_person_03_cam_4_event_1779815845595:matched:0.8335, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7323 |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527 | person_04 | 2 | 7 | 2 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.6689, test_clip_0527_person_02_cam_2_event_1779819881964:ambiguous:0.6051, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.5984, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.5841, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.57 |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527 | person_04 | 2 | 7 | 2 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_5_event_1779815845594:matched:0.8653, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.8197, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.8162, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.8021, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6018 |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.908, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.8162, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6192, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.5544, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.553 |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.9755, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.9559, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.8021, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6036, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.6004 |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.8335, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.8197, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6254, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.6092, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.5941 |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.8653, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7323, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6501, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5947, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.5347 |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527 | person_01 | 4 | 5 | 4 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6254, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.6192, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6103, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.6036, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.5947 |
| test_clip_0527_person_01_cam_3_event_1779815845589 | test_clip_0527 | person_01 | 4 | 5 | 4 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.5941, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.5424, test_clip_0527_person_03_cam_1_event_1779815845592:no_match:0.5399, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.5363, test_clip_0527_person_03_cam_1_event_1779815845596:no_match:0.5148 |

## Hard Negatives In Top-K

| query | candidate | rank | score | outcome | reasons |
| --- | --- | ---: | ---: | --- | --- |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_03_cam_1_event_1779815845592 | 6 | 0.6192 | ambiguous |  |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_04_cam_1_event_1779815845601 | 7 | 0.6103 | ambiguous |  |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_03_cam_1_event_1779815845596 | 8 | 0.6036 | ambiguous |  |
| test_clip_0527_person_01_cam_4_event_1779815845585 | test_clip_0527_person_03_cam_4_event_1779815845595 | 7 | 0.6092 | ambiguous |  |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527_person_02_cam_5_event_1779819881966 | 1 | 0.9068 | matched |  |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527_person_02_cam_5_event_1779815845591 | 2 | 0.8883 | matched |  |
| test_clip_0527_person_02_cam_1_event_1779815845584 | test_clip_0527_person_04_cam_1_event_1779815845601 | 1 | 0.961 | matched |  |
| test_clip_0527_person_02_cam_1_event_1779815845584 | test_clip_0527_person_03_cam_1_event_1779815845596 | 2 | 0.9559 | matched |  |
| test_clip_0527_person_02_cam_1_event_1779819881971 | test_clip_0527_person_04_cam_1_event_1779815845601 | 9 | 0.555 | ambiguous |  |
| test_clip_0527_person_02_cam_2_event_1779815845587 | test_clip_0527_person_04_cam_2_event_1779815845597 | 9 | 0.6689 | ambiguous |  |
| test_clip_0527_person_02_cam_2_event_1779819881964 | test_clip_0527_person_04_cam_2_event_1779815845597 | 9 | 0.6051 | ambiguous |  |
| test_clip_0527_person_02_cam_5_event_1779815845591 | test_clip_0527_person_01_cam_5_event_1779815845586 | 2 | 0.8883 | matched |  |
| test_clip_0527_person_02_cam_5_event_1779815845591 | test_clip_0527_person_04_cam_5_event_1779815845598 | 9 | 0.5855 | ambiguous |  |
| test_clip_0527_person_02_cam_5_event_1779819881966 | test_clip_0527_person_01_cam_5_event_1779815845586 | 1 | 0.9068 | matched |  |
| test_clip_0527_person_02_cam_5_event_1779819881966 | test_clip_0527_person_04_cam_5_event_1779815845598 | 9 | 0.5797 | ambiguous |  |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527_person_04_cam_1_event_1779815845601 | 1 | 0.908 | matched |  |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527_person_01_cam_1_event_1779815845583 | 6 | 0.6192 | ambiguous |  |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527_person_04_cam_1_event_1779815845601 | 1 | 0.9755 | matched |  |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527_person_02_cam_1_event_1779815845584 | 2 | 0.9559 | matched |  |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527_person_01_cam_1_event_1779815845583 | 7 | 0.6036 | ambiguous |  |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527_person_01_cam_4_event_1779815845585 | 7 | 0.6092 | ambiguous |  |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527_person_04_cam_5_event_1779815845598 | 1 | 0.8653 | matched |  |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527_person_01_cam_5_event_1779815845586 | 6 | 0.6501 | ambiguous |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_03_cam_1_event_1779815845596 | 1 | 0.9755 | matched |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_02_cam_1_event_1779815845584 | 2 | 0.961 | matched |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_03_cam_1_event_1779815845592 | 3 | 0.908 | matched |  |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527_person_02_cam_2_event_1779815845587 | 3 | 0.6689 | ambiguous |  |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527_person_02_cam_2_event_1779819881964 | 4 | 0.6051 | ambiguous |  |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527_person_03_cam_5_event_1779815845594 | 3 | 0.8653 | matched |  |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527_person_01_cam_5_event_1779815845586 | 7 | 0.6018 | ambiguous |  |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527_person_02_cam_5_event_1779815845591 | 9 | 0.5855 | ambiguous |  |

## Low Quality Query Crops

| query | quality | selected_frame | reason | crop |
| --- | ---: | ---: | --- | --- |
| test_clip_0527_person_02_cam_5_event_1779815845591 | 0.6879 | 38 | best_shot_selected |  |
| test_clip_0527_person_02_cam_5_event_1779819881966 | 0.6879 | 111 | best_shot_selected |  |
| test_clip_0527_person_04_cam_5_event_1779815845598 | 0.7424 | 133 | best_shot_selected |  |
| test_clip_0527_person_03_cam_5_event_1779815845594 | 0.7452 | 126 | best_shot_selected |  |
| test_clip_0527_person_01_cam_5_event_1779815845586 | 0.7563 | 12 | best_shot_selected |  |
| test_clip_0527_person_02_cam_1_event_1779819881971 | 0.7704 | 62 | best_shot_selected |  |
| test_clip_0527_person_01_cam_3_event_1779819881968 | 0.8433 | 32 | best_shot_selected |  |
| test_clip_0527_person_02_cam_1_event_1779815845584 | 0.8565 | 18 | best_shot_selected |  |
| test_clip_0527_person_01_cam_4_event_1779815845585 | 0.8629 | 53 | best_shot_selected |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | 0.8695 | 2 | best_shot_selected |  |

## Next Tuning Suggestions

- If low-quality crops dominate, increase `--max-frames` or lower `--sample-every`.
- If same-clothing hard negatives dominate, try `--retrieval-backend hybrid`.
- If query/gallery angle mismatch dominates, increase `--visual-top-n` for tracklet averaging.
