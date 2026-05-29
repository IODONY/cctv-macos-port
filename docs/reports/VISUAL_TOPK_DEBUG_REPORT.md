# Top-K Retrieval Debug Report

This report inspects retrieval failures and high-risk candidates without running cameras, RTSP, TouchDesigner, or full tracking.

## Worst Queries

| query | dataset | identity | own@9 | wrong@9 | max_possible_own@9 | normalized_own_recall@9 | readiness | top wrong candidates |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527 | person_04 | 1 | 8 | 2 | 0.5 | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.5781, test_clip_0527_person_02_cam_2_event_1779819881964:ambiguous:0.5509, test_clip_0527_person_02_cam_4_event_1779815845590:no_match:0.5301, test_clip_0527_person_02_cam_5_event_1779819881966:no_match:0.5301, test_clip_0527_person_02_cam_1_event_1779815845584:no_match:0.5285 |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527 | person_04 | 1 | 8 | 2 | 0.5 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7687, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.7582, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.6479, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6311, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6201 |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527 | person_04 | 2 | 7 | 2 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.8092, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.7466, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.7084, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.6927, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6301 |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7466, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.6479, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4961, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.469, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.4581 |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.8092, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.7582, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5711, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.523, test_clip_0527_person_01_cam_3_event_1779815845589:no_match:0.4896 |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7084, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.6311, test_clip_0527_person_01_cam_3_event_1779815845589:no_match:0.5437, test_clip_0527_person_02_cam_1_event_1779817469639:no_match:0.5106, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4948 |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.7687, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6927, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.5281, test_clip_0527_person_01_cam_3_event_1779815845589:no_match:0.5142, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.5029 |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527 | person_01 | 4 | 5 | 4 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6301, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.5711, test_clip_0527_person_03_cam_5_event_1779815845594:no_match:0.5281, test_clip_0527_person_03_cam_1_event_1779815845592:no_match:0.4961, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.4948 |
| test_clip_0527_person_01_cam_3_event_1779815845589 | test_clip_0527 | person_01 | 4 | 5 | 4 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.5612, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.5437, test_clip_0527_person_03_cam_5_event_1779815845594:no_match:0.5142, test_clip_0527_person_03_cam_1_event_1779815845596:no_match:0.4896, test_clip_0527_person_02_cam_1_event_1779817469639:no_match:0.4586 |
| test_clip_0527_person_01_cam_3_event_1779819881968 | test_clip_0527 | person_01 | 4 | 5 | 4 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.5228, test_clip_0527_person_03_cam_1_event_1779815845596:no_match:0.4715, test_clip_0527_person_03_cam_5_event_1779815845594:no_match:0.4665, test_clip_0527_person_04_cam_5_event_1779815845598:no_match:0.4599, test_clip_0527_person_03_cam_1_event_1779815845592:no_match:0.44 |

## Hard Negatives In Top-K

| query | candidate | rank | score | outcome | reasons |
| --- | --- | ---: | ---: | --- | --- |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_04_cam_1_event_1779815845601 | 4 | 0.6301 | ambiguous |  |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_03_cam_1_event_1779815845596 | 5 | 0.5711 | ambiguous |  |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_03_cam_1_event_1779815845592 | 8 | 0.4961 | no_match |  |
| test_clip_0527_person_01_cam_4_event_1779815845585 | test_clip_0527_person_03_cam_4_event_1779815845595 | 9 | 0.4405 | no_match |  |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527_person_04_cam_5_event_1779815845598 | 2 | 0.6201 | ambiguous |  |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527_person_03_cam_5_event_1779815845594 | 5 | 0.5029 | no_match |  |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527_person_02_cam_5_event_1779819881966 | 6 | 0.4767 | no_match |  |
| test_clip_0527_person_02_cam_1_event_1779815845584 | test_clip_0527_person_04_cam_1_event_1779815845601 | 9 | 0.4447 | no_match |  |
| test_clip_0527_person_02_cam_1_event_1779817469639 | test_clip_0527_person_04_cam_1_event_1779815845601 | 8 | 0.5259 | no_match |  |
| test_clip_0527_person_02_cam_2_event_1779815845587 | test_clip_0527_person_04_cam_2_event_1779815845597 | 8 | 0.5781 | ambiguous |  |
| test_clip_0527_person_02_cam_2_event_1779819881964 | test_clip_0527_person_04_cam_2_event_1779815845597 | 8 | 0.5509 | ambiguous |  |
| test_clip_0527_person_02_cam_5_event_1779819881966 | test_clip_0527_person_01_cam_5_event_1779815845586 | 9 | 0.4767 | no_match |  |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527_person_04_cam_1_event_1779815845601 | 2 | 0.7466 | ambiguous |  |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527_person_01_cam_1_event_1779815845583 | 6 | 0.4961 | no_match |  |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527_person_04_cam_1_event_1779815845601 | 2 | 0.8092 | ambiguous |  |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527_person_01_cam_1_event_1779815845583 | 6 | 0.5711 | ambiguous |  |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527_person_01_cam_4_event_1779815845585 | 9 | 0.4405 | no_match |  |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527_person_04_cam_5_event_1779815845598 | 1 | 0.7687 | ambiguous |  |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527_person_01_cam_5_event_1779815845586 | 8 | 0.5029 | no_match |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_03_cam_1_event_1779815845596 | 1 | 0.8092 | ambiguous |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_03_cam_1_event_1779815845592 | 2 | 0.7466 | ambiguous |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_01_cam_1_event_1779815845583 | 7 | 0.6301 | ambiguous |  |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527_person_02_cam_2_event_1779815845587 | 2 | 0.5781 | ambiguous |  |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527_person_02_cam_2_event_1779819881964 | 3 | 0.5509 | ambiguous |  |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527_person_03_cam_5_event_1779815845594 | 1 | 0.7687 | ambiguous |  |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527_person_01_cam_5_event_1779815845586 | 6 | 0.6201 | ambiguous |  |

## Low Quality Query Crops

| query | quality | selected_frame | reason | crop |
| --- | ---: | ---: | --- | --- |
| test_clip_0527_person_02_cam_5_event_1779815845591 | 0.6879 | 38 | best_shot_selected | snapshots/reid_debug/test_clip_0527_person_02_cam_5_event_1779815845591_best.jpg |
| test_clip_0527_person_02_cam_5_event_1779819881966 | 0.6879 | 111 | best_shot_selected | snapshots/reid_debug/test_clip_0527_person_02_cam_5_event_1779819881966_best.jpg |
| test_clip_0527_person_04_cam_5_event_1779815845598 | 0.7424 | 133 | best_shot_selected | snapshots/reid_debug/test_clip_0527_person_04_cam_5_event_1779815845598_best.jpg |
| test_clip_0527_person_03_cam_5_event_1779815845594 | 0.7452 | 126 | best_shot_selected | snapshots/reid_debug/test_clip_0527_person_03_cam_5_event_1779815845594_best.jpg |
| test_clip_0527_person_01_cam_5_event_1779815845586 | 0.7563 | 12 | best_shot_selected | snapshots/reid_debug/test_clip_0527_person_01_cam_5_event_1779815845586_best.jpg |
| test_clip_0527_person_02_cam_1_event_1779819881971 | 0.7704 | 62 | best_shot_selected | snapshots/reid_debug/test_clip_0527_person_02_cam_1_event_1779819881971_best.jpg |
| test_clip_0527_person_01_cam_3_event_1779819881968 | 0.8433 | 32 | best_shot_selected | snapshots/reid_debug/test_clip_0527_person_01_cam_3_event_1779819881968_best.jpg |
| test_clip_0527_person_02_cam_1_event_1779815845584 | 0.8565 | 18 | best_shot_selected | snapshots/reid_debug/test_clip_0527_person_02_cam_1_event_1779815845584_best.jpg |
| test_clip_0527_person_01_cam_4_event_1779815845585 | 0.8629 | 53 | best_shot_selected | snapshots/reid_debug/test_clip_0527_person_01_cam_4_event_1779815845585_best.jpg |
| test_clip_0527_person_04_cam_1_event_1779815845601 | 0.8695 | 2 | best_shot_selected | snapshots/reid_debug/test_clip_0527_person_04_cam_1_event_1779815845601_best.jpg |

## Next Tuning Suggestions

- If low-quality crops dominate, increase `--max-frames` or lower `--sample-every`.
- If same-clothing hard negatives dominate, try `--retrieval-backend hybrid`.
- If query/gallery angle mismatch dominates, increase `--visual-top-n` for tracklet averaging.
