# YOLO-ReID Top-K Retrieval Evaluation Report

This evaluates labeled clips by ranking gallery clips for each query and checking whether the final Top-9 output is usable for display.

- Clips manifest: `data/labels/clips.csv`
- Dataset filter: `test_clip_0527`
- Evaluation mode: `leave_one_out`
- Query cameras: `all`
- Gallery cameras: `all eligible`
- Query count: `20`
- Gallery count: `20`
- K: `9`
- Candidate pool: `12`
- Retrieval backend: `visual`
- Embedding model: `osnet_x0_25`
- Visual top-N crops: `6`
- Crop selection strategy: `diverse-quality`
- Prototype score mode: `max`
- Visual color weight: `0.2`
- Match threshold: `0.72`
- Ambiguous threshold: `0.25`

## Headline

- `Recall@9` macro/query mean: `0.9625`
- `Recall@9` micro/positive-weighted: `0.9681` (91/94)
- `Normalized OwnRecall@9` micro: `0.9681` (91/94)
- `Precision@9` macro/query mean: `0.5055`
- `OwnCount@9` mean: `4.55`
- `Wrong@9` mean: `4.45`
- `TopK output count` mean: `9.0`
- Insufficient same-identity gallery queries: `20`
- Output readiness counts: `insufficient_same_identity_gallery=20`

## Summary Metrics

- `additional_gallery_clips_needed_for_top_9_own`: `2`
- `max_available_positive_count_for_any_query`: `7`
- `max_own_at_9`: `7`
- `mean_ambiguous_rate_at_9`: `0.4389`
- `mean_false_match_rate_at_9`: `0.1333`
- `mean_hard_negative_rate_at_9`: `0.1722`
- `mean_normalized_own_recall_at_9`: `0.9625`
- `mean_own_at_12`: `4.65`
- `mean_own_at_9`: `4.55`
- `mean_precision_at_12`: `0.3875`
- `mean_precision_at_9`: `0.5055`
- `mean_recall_at_12`: `0.9875`
- `mean_recall_at_9`: `0.9625`
- `mean_topk_output_count_at_9`: `9.0`
- `mean_wrong_at_12`: `7.35`
- `mean_wrong_at_9`: `4.45`
- `micro_normalized_own_recall_at_9`: `0.9681`
- `micro_precision_at_12`: `0.3875`
- `micro_precision_at_9`: `0.5056`
- `micro_recall_at_12`: `0.9894`
- `micro_recall_at_9`: `0.9681`
- `min_own_at_9`: `1`
- `output_readiness_counts`: `{'insufficient_same_identity_gallery': 20}`
- `queries_with_insufficient_gallery`: `0`
- `queries_with_insufficient_same_identity_gallery`: `20`
- `queries_with_majority_own_at_9`: `8`
- `query_count`: `20`
- `total_available_positive_count`: `94`
- `total_max_possible_own_count_at_9`: `94`
- `total_own_at_12`: `93`
- `total_own_at_9`: `91`
- `total_returned_at_12`: `240`
- `total_returned_at_9`: `180`
- `total_wrong_at_12`: `147`
- `total_wrong_at_9`: `89`

## Visual Crop Summary

- `cache_hit_count`: `0`
- `clip_count`: `20`
- `crop_failure_count`: `0`
- `crop_success_count`: `20`
- `embedding_methods`: `{'torchreid_osnet_x0_25': 20}`
- `failure_reasons`: `{}`
- `max_best_crop_quality`: `0.9364`
- `mean_best_crop_quality`: `0.841`
- `mean_crop_count`: `135.6`
- `min_best_crop_quality`: `0.6879`

## Dataset Breakdown

| dataset | queries | OwnCount@9 total | Wrong@9 total | Recall@9 micro | Normalized OwnRecall@9 micro | Precision@9 micro | readiness |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| test_clip_0527 | 20 | 91 | 89 | 0.9681 | 0.9681 | 0.5056 | insufficient_same_identity_gallery=20 |

## Identity Breakdown

| dataset | identity | queries | available positives | max possible own@9 | additional clips needed | OwnCount@9 total | Wrong@9 total | Recall@9 micro | Normalized OwnRecall@9 micro | own@9 min-max | readiness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| test_clip_0527 | person_01 | 5 | 20 | 20 | 5 | 17 | 28 | 0.85 | 0.85 | 1-4 | insufficient_same_identity_gallery=5 |
| test_clip_0527 | person_02 | 8 | 56 | 56 | 2 | 56 | 16 | 1.0 | 1.0 | 7-7 | insufficient_same_identity_gallery=8 |
| test_clip_0527 | person_03 | 4 | 12 | 12 | 6 | 12 | 24 | 1.0 | 1.0 | 3-3 | insufficient_same_identity_gallery=4 |
| test_clip_0527 | person_04 | 3 | 6 | 6 | 7 | 6 | 21 | 1.0 | 1.0 | 2-2 | insufficient_same_identity_gallery=3 |

## Additional Clips Needed

`additional clips needed` is the minimum extra same-identity gallery clips needed so a query can theoretically return 9 own clips. This is a dataset coverage limit, not a live identity field.

## Camera Pair Breakdown

| query_cam | candidate_cam | top-k candidates | own | wrong | precision | mean_score | outcomes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| cam_1 | cam_1 | 22 | 8 | 14 | 0.3636 | 0.8233 | ambiguous=6, matched=16 |
| cam_1 | cam_2 | 10 | 7 | 3 | 0.7 | 0.7762 | ambiguous=2, matched=7, no_match=1 |
| cam_1 | cam_3 | 5 | 2 | 3 | 0.4 | 0.6387 | ambiguous=4, no_match=1 |
| cam_1 | cam_4 | 10 | 6 | 4 | 0.6 | 0.7715 | ambiguous=3, matched=6, no_match=1 |
| cam_1 | cam_5 | 16 | 10 | 6 | 0.625 | 0.8015 | ambiguous=8, matched=8 |
| cam_2 | cam_1 | 8 | 7 | 1 | 0.875 | 0.8249 | ambiguous=1, matched=7 |
| cam_2 | cam_2 | 6 | 2 | 4 | 0.3333 | 0.7355 | ambiguous=4, matched=2 |
| cam_2 | cam_4 | 4 | 2 | 2 | 0.5 | 0.7378 | ambiguous=2, matched=2 |
| cam_2 | cam_5 | 9 | 5 | 4 | 0.5556 | 0.7955 | ambiguous=2, matched=7 |
| cam_3 | cam_1 | 8 | 2 | 6 | 0.25 | 0.6015 | ambiguous=5, no_match=3 |
| cam_3 | cam_2 | 2 | 0 | 2 | 0.0 | 0.563 | ambiguous=1, no_match=1 |
| cam_3 | cam_3 | 2 | 2 | 0 | 1.0 | 0.7262 | ambiguous=2 |
| cam_3 | cam_4 | 4 | 2 | 2 | 0.5 | 0.6696 | ambiguous=4 |
| cam_3 | cam_5 | 2 | 2 | 0 | 1.0 | 0.7015 | ambiguous=2 |
| cam_4 | cam_1 | 9 | 6 | 3 | 0.6667 | 0.7981 | ambiguous=3, matched=6 |
| cam_4 | cam_2 | 5 | 2 | 3 | 0.4 | 0.7147 | ambiguous=3, matched=2 |
| cam_4 | cam_3 | 4 | 2 | 2 | 0.5 | 0.6696 | ambiguous=4 |
| cam_4 | cam_4 | 2 | 0 | 2 | 0.0 | 0.6092 | ambiguous=2 |
| cam_4 | cam_5 | 7 | 4 | 3 | 0.5714 | 0.7768 | ambiguous=4, matched=3 |
| cam_5 | cam_1 | 16 | 9 | 7 | 0.5625 | 0.808 | ambiguous=8, matched=8 |
| cam_5 | cam_2 | 8 | 5 | 3 | 0.625 | 0.8294 | ambiguous=1, matched=7 |
| cam_5 | cam_3 | 2 | 1 | 1 | 0.5 | 0.6557 | ambiguous=1, no_match=1 |
| cam_5 | cam_4 | 6 | 3 | 3 | 0.5 | 0.7693 | ambiguous=2, matched=3, no_match=1 |
| cam_5 | cam_5 | 13 | 2 | 11 | 0.1538 | 0.7785 | ambiguous=5, matched=8 |

## Per Query Top-K

| query | dataset | identity | cam | gallery | available_positive_count | max_possible_own_count_at_9 | output_count | OwnCount@9 | Wrong@9 | Precision@9 | Recall@9 | Normalized OwnRecall@9 | insufficient_same_identity_gallery | readiness | crop_quality | top candidates |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527 | person_01 | cam_1 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8783 | test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.8088, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.803, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.6972, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6745, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6254, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.6192, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6103, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.6036, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.5947 |
| test_clip_0527_person_01_cam_3_event_1779815845589 | test_clip_0527 | person_01 | cam_3 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9364 | test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.7262, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.7051, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6972, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6167, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.5941, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.5424, test_clip_0527_person_03_cam_1_event_1779815845592:no_match:0.5399, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.5363, test_clip_0527_person_03_cam_1_event_1779815845596:no_match:0.5148 |
| test_clip_0527_person_01_cam_3_event_1779819881968 | test_clip_0527 | person_01 | cam_3 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8433 | test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.803, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.7985, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7862, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.7262, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.6004, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.5835, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.5808, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.5673, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.553 |
| test_clip_0527_person_01_cam_4_event_1779815845585 | test_clip_0527 | person_01 | cam_4 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8629 | test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.8088, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.7985, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7762, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.7051, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.622, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6166, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6092, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.5984, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.5802 |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527 | person_01 | cam_5 | 19 | 4 | 4 | 9 | 1 | 8 | 0.1111 | 0.25 | 0.25 | True | insufficient_same_identity_gallery | 0.7563 | test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.9068, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8883, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8766, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8387, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8371, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.826, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.7907, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.7862, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.7781 |
| test_clip_0527_person_02_cam_1_event_1779815845584 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8565 | test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.961, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.9559, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8851, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8838, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8776, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8647, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8599, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8527, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8421 |
| test_clip_0527_person_02_cam_1_event_1779817469639 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8828 | test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8776, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8621, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8473, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8388, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8315, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8296, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8277, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7907, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.5405 |
| test_clip_0527_person_02_cam_1_event_1779819881971 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.7704 | test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8825, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8809, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8789, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8765, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8647, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8461, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8315, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.826, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.555 |
| test_clip_0527_person_02_cam_2_event_1779815845587 | test_clip_0527 | person_02 | cam_2 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9248 | test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.9324, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8794, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8789, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.8766, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8542, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8532, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8527, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8388, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.6689 |
| test_clip_0527_person_02_cam_2_event_1779819881964 | test_clip_0527 | person_02 | cam_2 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9175 | test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.9324, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8894, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8825, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8761, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8599, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8478, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.8387, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8277, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.6051 |
| test_clip_0527_person_02_cam_4_event_1779815845590 | test_clip_0527 | person_02 | cam_4 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8738 | test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8894, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8838, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8794, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8765, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8621, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8463, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.8371, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8224, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.5841 |
| test_clip_0527_person_02_cam_5_event_1779815845591 | test_clip_0527 | person_02 | cam_5 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.6879 | test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8988, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.8883, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8542, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8478, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8473, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8461, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8421, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8224, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.5855 |
| test_clip_0527_person_02_cam_5_event_1779819881966 | test_clip_0527 | person_02 | cam_5 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.6879 | test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.9068, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8988, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8851, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8809, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8761, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8532, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8463, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8296, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.5797 |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527 | person_03 | cam_1 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9255 | test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.908, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.8772, test_clip_0527_person_03_cam_4_event_1779815845595:matched:0.8319, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.8162, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.8009, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6192, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.5544, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.553, test_clip_0527_person_01_cam_3_event_1779815845589:no_match:0.5399 |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527 | person_03 | cam_1 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8762 | test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.9755, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.9559, test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.8772, test_clip_0527_person_03_cam_4_event_1779815845595:matched:0.8442, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.8021, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7833, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6036, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.6004, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.5319 |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527 | person_03 | cam_4 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8997 | test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.8442, test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.8335, test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.8319, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.8197, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7558, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6254, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.6092, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.5941, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.5808 |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527 | person_03 | cam_5 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.7452 | test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.8653, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.8009, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.7833, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.7558, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7323, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6501, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5947, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.5347, test_clip_0527_person_01_cam_3_event_1779819881968:no_match:0.5251 |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527 | person_04 | cam_1 | 19 | 2 | 2 | 9 | 2 | 7 | 0.2222 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8695 | test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.9755, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.961, test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.908, test_clip_0527_person_04_cam_2_event_1779815845597:matched:0.9042, test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.8728, test_clip_0527_person_03_cam_4_event_1779815845595:matched:0.8335, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7323, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.6227, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.6166 |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527 | person_04 | cam_2 | 19 | 2 | 2 | 9 | 2 | 7 | 0.2222 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8829 | test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.9042, test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.8882, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.6689, test_clip_0527_person_02_cam_2_event_1779819881964:ambiguous:0.6051, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.5984, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.5841, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.57, test_clip_0527_person_02_cam_5_event_1779815845591:ambiguous:0.5551, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.5544 |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527 | person_04 | cam_5 | 19 | 2 | 2 | 9 | 2 | 7 | 0.2222 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.7424 | test_clip_0527_person_04_cam_2_event_1779815845597:matched:0.8882, test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.8728, test_clip_0527_person_03_cam_5_event_1779815845594:matched:0.8653, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.8197, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.8162, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.8021, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6018, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.6001, test_clip_0527_person_02_cam_5_event_1779815845591:ambiguous:0.5855 |
