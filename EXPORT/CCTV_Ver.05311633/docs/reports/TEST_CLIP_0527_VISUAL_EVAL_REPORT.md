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
- Visual top-N crops: `3`
- Visual color weight: `0.2`
- Match threshold: `0.72`
- Ambiguous threshold: `0.25`

## Headline

- `Recall@9` macro/query mean: `0.95`
- `Recall@9` micro/positive-weighted: `0.9787` (92/94)
- `Normalized OwnRecall@9` micro: `0.9787` (92/94)
- `Precision@9` macro/query mean: `0.5111`
- `OwnCount@9` mean: `4.6`
- `Wrong@9` mean: `4.4`
- `TopK output count` mean: `9.0`
- Insufficient same-identity gallery queries: `20`
- Output readiness counts: `insufficient_same_identity_gallery=20`

## Summary Metrics

- `additional_gallery_clips_needed_for_top_9_own`: `2`
- `max_available_positive_count_for_any_query`: `7`
- `max_own_at_9`: `7`
- `mean_ambiguous_rate_at_9`: `0.4556`
- `mean_false_match_rate_at_9`: `0.0`
- `mean_hard_negative_rate_at_9`: `0.1444`
- `mean_normalized_own_recall_at_9`: `0.95`
- `mean_own_at_12`: `4.65`
- `mean_own_at_9`: `4.6`
- `mean_precision_at_12`: `0.3875`
- `mean_precision_at_9`: `0.5111`
- `mean_recall_at_12`: `0.975`
- `mean_recall_at_9`: `0.95`
- `mean_topk_output_count_at_9`: `9.0`
- `mean_wrong_at_12`: `7.35`
- `mean_wrong_at_9`: `4.4`
- `micro_normalized_own_recall_at_9`: `0.9787`
- `micro_precision_at_12`: `0.3875`
- `micro_precision_at_9`: `0.5111`
- `micro_recall_at_12`: `0.9894`
- `micro_recall_at_9`: `0.9787`
- `min_own_at_9`: `1`
- `output_readiness_counts`: `{'insufficient_same_identity_gallery': 20}`
- `queries_with_insufficient_gallery`: `0`
- `queries_with_insufficient_same_identity_gallery`: `20`
- `queries_with_majority_own_at_9`: `8`
- `query_count`: `20`
- `total_available_positive_count`: `94`
- `total_max_possible_own_count_at_9`: `94`
- `total_own_at_12`: `93`
- `total_own_at_9`: `92`
- `total_returned_at_12`: `240`
- `total_returned_at_9`: `180`
- `total_wrong_at_12`: `147`
- `total_wrong_at_9`: `88`

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
| test_clip_0527 | 20 | 92 | 88 | 0.9787 | 0.9787 | 0.5111 | insufficient_same_identity_gallery=20 |

## Identity Breakdown

| dataset | identity | queries | available positives | max possible own@9 | additional clips needed | OwnCount@9 total | Wrong@9 total | Recall@9 micro | Normalized OwnRecall@9 micro | own@9 min-max | readiness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| test_clip_0527 | person_01 | 5 | 20 | 20 | 5 | 20 | 25 | 1.0 | 1.0 | 4-4 | insufficient_same_identity_gallery=5 |
| test_clip_0527 | person_02 | 8 | 56 | 56 | 2 | 56 | 16 | 1.0 | 1.0 | 7-7 | insufficient_same_identity_gallery=8 |
| test_clip_0527 | person_03 | 4 | 12 | 12 | 6 | 12 | 24 | 1.0 | 1.0 | 3-3 | insufficient_same_identity_gallery=4 |
| test_clip_0527 | person_04 | 3 | 6 | 6 | 7 | 4 | 23 | 0.6667 | 0.6667 | 1-2 | insufficient_same_identity_gallery=3 |

## Additional Clips Needed

`additional clips needed` is the minimum extra same-identity gallery clips needed so a query can theoretically return 9 own clips. This is a dataset coverage limit, not a live identity field.

## Camera Pair Breakdown

| query_cam | candidate_cam | top-k candidates | own | wrong | precision | mean_score | outcomes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| cam_1 | cam_1 | 20 | 8 | 12 | 0.4 | 0.6694 | ambiguous=14, matched=2, no_match=4 |
| cam_1 | cam_2 | 10 | 7 | 3 | 0.7 | 0.6942 | ambiguous=4, matched=3, no_match=3 |
| cam_1 | cam_3 | 4 | 2 | 2 | 0.5 | 0.6196 | ambiguous=3, no_match=1 |
| cam_1 | cam_4 | 11 | 6 | 5 | 0.5455 | 0.6592 | ambiguous=7, matched=1, no_match=3 |
| cam_1 | cam_5 | 18 | 10 | 8 | 0.5556 | 0.6623 | ambiguous=8, matched=4, no_match=6 |
| cam_2 | cam_1 | 11 | 7 | 4 | 0.6364 | 0.6724 | ambiguous=4, matched=3, no_match=4 |
| cam_2 | cam_2 | 6 | 2 | 4 | 0.3333 | 0.6915 | ambiguous=4, matched=2 |
| cam_2 | cam_4 | 4 | 2 | 2 | 0.5 | 0.6938 | matched=2, no_match=2 |
| cam_2 | cam_5 | 6 | 4 | 2 | 0.6667 | 0.7616 | matched=4, no_match=2 |
| cam_3 | cam_1 | 8 | 2 | 6 | 0.25 | 0.5464 | ambiguous=3, no_match=5 |
| cam_3 | cam_3 | 2 | 2 | 0 | 1.0 | 0.7514 | ambiguous=2 |
| cam_3 | cam_4 | 3 | 2 | 1 | 0.6667 | 0.674 | ambiguous=2, no_match=1 |
| cam_3 | cam_5 | 5 | 2 | 3 | 0.4 | 0.5014 | ambiguous=1, no_match=4 |
| cam_4 | cam_1 | 12 | 6 | 6 | 0.5 | 0.6395 | ambiguous=7, matched=1, no_match=4 |
| cam_4 | cam_2 | 4 | 2 | 2 | 0.5 | 0.6938 | matched=2, no_match=2 |
| cam_4 | cam_3 | 3 | 2 | 1 | 0.6667 | 0.674 | ambiguous=2, no_match=1 |
| cam_4 | cam_4 | 2 | 0 | 2 | 0.0 | 0.4405 | no_match=2 |
| cam_4 | cam_5 | 6 | 4 | 2 | 0.6667 | 0.6615 | ambiguous=4, matched=1, no_match=1 |
| cam_5 | cam_1 | 19 | 10 | 9 | 0.5263 | 0.6561 | ambiguous=8, matched=4, no_match=7 |
| cam_5 | cam_2 | 6 | 4 | 2 | 0.6667 | 0.7616 | matched=4, no_match=2 |
| cam_5 | cam_3 | 4 | 2 | 2 | 0.5 | 0.5101 | ambiguous=1, no_match=3 |
| cam_5 | cam_4 | 6 | 4 | 2 | 0.6667 | 0.6615 | ambiguous=4, matched=1, no_match=1 |
| cam_5 | cam_5 | 10 | 2 | 8 | 0.2 | 0.6532 | ambiguous=4, matched=2, no_match=4 |

## Per Query Top-K

| query | dataset | identity | cam | gallery | available_positive_count | max_possible_own_count_at_9 | output_count | OwnCount@9 | Wrong@9 | Precision@9 | Recall@9 | Normalized OwnRecall@9 | insufficient_same_identity_gallery | readiness | crop_quality | top candidates |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527 | person_01 | cam_1 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8783 | test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.7788, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.7279, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.6997, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6301, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.5711, test_clip_0527_person_03_cam_5_event_1779815845594:no_match:0.5281, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.5234, test_clip_0527_person_03_cam_1_event_1779815845592:no_match:0.4961, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.4948 |
| test_clip_0527_person_01_cam_3_event_1779815845589 | test_clip_0527 | person_01 | cam_3 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9364 | test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.7514, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6997, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.6966, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.5612, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.5437, test_clip_0527_person_03_cam_5_event_1779815845594:no_match:0.5142, test_clip_0527_person_03_cam_1_event_1779815845596:no_match:0.4896, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.461, test_clip_0527_person_02_cam_1_event_1779817469639:no_match:0.4586 |
| test_clip_0527_person_01_cam_3_event_1779819881968 | test_clip_0527 | person_01 | cam_3 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8433 | test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.7818, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.7514, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.7279, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6053, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.5228, test_clip_0527_person_03_cam_1_event_1779815845596:no_match:0.4715, test_clip_0527_person_03_cam_5_event_1779815845594:no_match:0.4665, test_clip_0527_person_04_cam_5_event_1779815845598:no_match:0.4599, test_clip_0527_person_03_cam_1_event_1779815845592:no_match:0.44 |
| test_clip_0527_person_01_cam_4_event_1779815845585 | test_clip_0527 | person_01 | cam_4 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8629 | test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.7818, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.7788, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.6966, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6258, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.5885, test_clip_0527_person_03_cam_1_event_1779815845596:no_match:0.523, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.4972, test_clip_0527_person_04_cam_5_event_1779815845598:no_match:0.4781, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.4405 |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527 | person_01 | cam_5 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.7563 | test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.6258, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.6201, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.6053, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.5234, test_clip_0527_person_03_cam_5_event_1779815845594:no_match:0.5029, test_clip_0527_person_02_cam_5_event_1779819881966:no_match:0.4767, test_clip_0527_person_03_cam_1_event_1779815845596:no_match:0.4742, test_clip_0527_person_01_cam_3_event_1779815845589:no_match:0.461, test_clip_0527_person_03_cam_1_event_1779815845592:no_match:0.4581 |
| test_clip_0527_person_02_cam_1_event_1779815845584 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8565 | test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8914, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8638, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.859, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8585, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.856, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8329, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.6882, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.5285, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.4447 |
| test_clip_0527_person_02_cam_1_event_1779817469639 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8828 | test_clip_0527_person_02_cam_5_event_1779815845591:ambiguous:0.7291, test_clip_0527_person_02_cam_2_event_1779819881964:ambiguous:0.7161, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.7029, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.7016, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.6882, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.6241, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.6058, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.5259, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.5106 |
| test_clip_0527_person_02_cam_1_event_1779819881971 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.7704 | test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8648, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8496, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8329, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8312, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.8123, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.7783, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.6241, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.5099, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.4463 |
| test_clip_0527_person_02_cam_2_event_1779815845587 | test_clip_0527 | person_02 | cam_2 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9248 | test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.9456, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8891, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.867, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8667, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.856, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.8123, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.7016, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.5781, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.4704 |
| test_clip_0527_person_02_cam_2_event_1779819881964 | test_clip_0527 | person_02 | cam_2 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9175 | test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.9456, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8842, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8811, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8753, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.859, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8312, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.7161, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.5509, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.4536 |
| test_clip_0527_person_02_cam_4_event_1779815845590 | test_clip_0527 | person_02 | cam_4 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8738 | test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8811, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8667, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8585, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8209, test_clip_0527_person_02_cam_5_event_1779815845591:ambiguous:0.7921, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.7783, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.6058, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.5301, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.4228 |
| test_clip_0527_person_02_cam_5_event_1779815845591 | test_clip_0527 | person_02 | cam_5 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.6879 | test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8977, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8842, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.867, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8638, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8496, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.7921, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.7291, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.5239, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.4732 |
| test_clip_0527_person_02_cam_5_event_1779819881966 | test_clip_0527 | person_02 | cam_5 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.6879 | test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8977, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8914, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8891, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8753, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8648, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8209, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.7029, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.5301, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.4767 |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527 | person_03 | cam_1 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9255 | test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.8107, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7466, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.6853, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6601, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.6479, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4961, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.469, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.4581, test_clip_0527_person_02_cam_5_event_1779815845591:no_match:0.4559 |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527 | person_03 | cam_1 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8762 | test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.8107, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.8092, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.7582, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.7441, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.6774, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5711, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.523, test_clip_0527_person_01_cam_3_event_1779815845589:no_match:0.4896, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.4742 |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527 | person_03 | cam_4 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8997 | test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.7441, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7084, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.6601, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.6311, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.6208, test_clip_0527_person_01_cam_3_event_1779815845589:no_match:0.5437, test_clip_0527_person_02_cam_1_event_1779817469639:no_match:0.5106, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4948, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.4405 |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527 | person_03 | cam_5 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.7452 | test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.7687, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6927, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.6853, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.6774, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6208, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.5281, test_clip_0527_person_01_cam_3_event_1779815845589:no_match:0.5142, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.5029, test_clip_0527_person_02_cam_1_event_1779817469639:no_match:0.4919 |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527 | person_04 | cam_1 | 19 | 2 | 2 | 9 | 2 | 7 | 0.2222 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8695 | test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.8092, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.7466, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.7084, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.6927, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.6715, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.6583, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6301, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.5885, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.5612 |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527 | person_04 | cam_2 | 19 | 2 | 2 | 9 | 1 | 8 | 0.1111 | 0.5 | 0.5 | True | insufficient_same_identity_gallery | 0.8829 | test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6583, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.5781, test_clip_0527_person_02_cam_2_event_1779819881964:ambiguous:0.5509, test_clip_0527_person_02_cam_4_event_1779815845590:no_match:0.5301, test_clip_0527_person_02_cam_5_event_1779819881966:no_match:0.5301, test_clip_0527_person_02_cam_1_event_1779815845584:no_match:0.5285, test_clip_0527_person_02_cam_5_event_1779815845591:no_match:0.5239, test_clip_0527_person_02_cam_1_event_1779819881971:no_match:0.5099, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.4972 |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527 | person_04 | cam_5 | 19 | 2 | 2 | 9 | 1 | 8 | 0.1111 | 0.5 | 0.5 | True | insufficient_same_identity_gallery | 0.7424 | test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7687, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.7582, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6715, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.6479, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6311, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6201, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4829, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.4781, test_clip_0527_person_01_cam_3_event_1779819881968:no_match:0.4599 |
