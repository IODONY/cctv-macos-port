# Top-K Retrieval Debug Report

This report inspects retrieval failures and high-risk candidates without running cameras, RTSP, TouchDesigner, or full tracking.

## Worst Queries

| query | dataset | identity | own@9 | wrong@9 | max_possible_own@9 | normalized_own_recall@9 | readiness | top wrong candidates |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527 | person_01 | 2 | 7 | 4 | 0.5 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_2_event_1779815845597:matched:0.8322, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.7907, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7851, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.7649, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.7535 |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527 | person_04 | 2 | 7 | 2 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.8432, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.7064, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.6412, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.5698, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.3663 |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527 | person_04 | 2 | 7 | 2 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.8397, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.8322, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.8076, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7825, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.505 |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527 | person_04 | 2 | 7 | 2 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_5_event_1779815845594:matched:0.8324, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.8298, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.8104, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7907, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.5909 |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527 | person_01 | 3 | 6 | 4 | 0.75 | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.5861, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.5859, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.566, test_clip_0527_person_02_cam_1_event_1779819881971:no_match:0.5397, test_clip_0527_person_02_cam_2_event_1779819881964:no_match:0.5126 |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.8432, test_clip_0527_person_04_cam_2_event_1779815845597:matched:0.8397, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.8104, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7535, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5859 |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.8298, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.8076, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7649, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7064, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.5256 |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.5993, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.5909, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.5297, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.505, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4888 |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527 | person_03 | 3 | 6 | 3 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.8324, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7851, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.7825, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6412, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.48 |
| test_clip_0527_person_01_cam_3_event_1779815845589 | test_clip_0527 | person_01 | 4 | 5 | 4 | 1.0 | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.5758, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.5714, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.5638, test_clip_0527_person_02_cam_5_event_1779815845591:no_match:0.5221, test_clip_0527_person_02_cam_2_event_1779815845587:no_match:0.4955 |

## Hard Negatives In Top-K

| query | candidate | rank | score | outcome | reasons |
| --- | --- | ---: | ---: | --- | --- |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_02_cam_1_event_1779815845584 | 4 | 0.5861 | ambiguous |  |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_03_cam_1_event_1779815845592 | 5 | 0.5859 | ambiguous |  |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_02_cam_1_event_1779819881971 | 7 | 0.5397 | no_match |  |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527_person_02_cam_1_event_1779817469639 | 9 | 0.5097 | no_match |  |
| test_clip_0527_person_01_cam_4_event_1779815845585 | test_clip_0527_person_03_cam_4_event_1779815845595 | 5 | 0.5993 | ambiguous |  |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527_person_04_cam_5_event_1779815845598 | 2 | 0.7907 | ambiguous |  |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527_person_03_cam_5_event_1779815845594 | 3 | 0.7851 | ambiguous |  |
| test_clip_0527_person_02_cam_1_event_1779815845584 | test_clip_0527_person_04_cam_1_event_1779815845601 | 9 | 0.2122 | no_match | top_and_bag_mismatch,sleeve_and_pants_mismatch |
| test_clip_0527_person_02_cam_1_event_1779817469639 | test_clip_0527_person_01_cam_1_event_1779815845583 | 8 | 0.5097 | no_match |  |
| test_clip_0527_person_02_cam_4_event_1779815845590 | test_clip_0527_person_01_cam_4_event_1779815845585 | 9 | 0.4922 | no_match |  |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527_person_04_cam_1_event_1779815845601 | 2 | 0.8432 | matched |  |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527_person_01_cam_1_event_1779815845583 | 8 | 0.5859 | ambiguous |  |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527_person_04_cam_1_event_1779815845601 | 6 | 0.7064 | ambiguous |  |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527_person_01_cam_1_event_1779815845583 | 9 | 0.4908 | no_match |  |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527_person_01_cam_4_event_1779815845585 | 4 | 0.5993 | ambiguous |  |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527_person_04_cam_5_event_1779815845598 | 1 | 0.8324 | matched |  |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527_person_01_cam_5_event_1779815845586 | 4 | 0.7851 | ambiguous |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_03_cam_1_event_1779815845592 | 1 | 0.8432 | matched |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_03_cam_1_event_1779815845596 | 2 | 0.7064 | ambiguous |  |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527_person_02_cam_1_event_1779815845584 | 9 | 0.2122 | no_match | top_and_bag_mismatch,sleeve_and_pants_mismatch |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527_person_03_cam_5_event_1779815845594 | 1 | 0.8324 | matched |  |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527_person_01_cam_5_event_1779815845586 | 5 | 0.7907 | ambiguous |  |

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
