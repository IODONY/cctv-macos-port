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
- Retrieval backend: `hybrid`
- Embedding model: `mobilenet_v3_large`
- Visual top-N crops: `1`
- Visual color weight: `0.2`
- Hybrid visual weight: `0.35`
- Visual rescue count: `2`
- Visual rescue margin: `0.2`
- Visual rescue threshold: `0.6`
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
- `mean_ambiguous_rate_at_9`: `0.4889`
- `mean_false_match_rate_at_9`: `0.0556`
- `mean_hard_negative_rate_at_9`: `0.1222`
- `mean_normalized_own_recall_at_9`: `0.9625`
- `mean_own_at_12`: `4.55`
- `mean_own_at_9`: `4.55`
- `mean_precision_at_12`: `0.3792`
- `mean_precision_at_9`: `0.5055`
- `mean_recall_at_12`: `0.9625`
- `mean_recall_at_9`: `0.9625`
- `mean_topk_output_count_at_9`: `9.0`
- `mean_wrong_at_12`: `7.45`
- `mean_wrong_at_9`: `4.45`
- `micro_normalized_own_recall_at_9`: `0.9681`
- `micro_precision_at_12`: `0.3792`
- `micro_precision_at_9`: `0.5056`
- `micro_recall_at_12`: `0.9681`
- `micro_recall_at_9`: `0.9681`
- `min_own_at_9`: `2`
- `output_readiness_counts`: `{'insufficient_same_identity_gallery': 20}`
- `queries_with_insufficient_gallery`: `0`
- `queries_with_insufficient_same_identity_gallery`: `20`
- `queries_with_majority_own_at_9`: `8`
- `query_count`: `20`
- `total_available_positive_count`: `94`
- `total_max_possible_own_count_at_9`: `94`
- `total_own_at_12`: `91`
- `total_own_at_9`: `91`
- `total_returned_at_12`: `240`
- `total_returned_at_9`: `180`
- `total_wrong_at_12`: `149`
- `total_wrong_at_9`: `89`

## Visual Crop Summary

- `cache_hit_count`: `20`
- `clip_count`: `20`
- `crop_failure_count`: `0`
- `crop_success_count`: `20`
- `embedding_methods`: `{'torchvision_mobilenet_v3_large': 20}`
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
| test_clip_0527 | person_01 | 5 | 20 | 20 | 5 | 17 | 28 | 0.85 | 0.85 | 2-4 | insufficient_same_identity_gallery=5 |
| test_clip_0527 | person_02 | 8 | 56 | 56 | 2 | 56 | 16 | 1.0 | 1.0 | 7-7 | insufficient_same_identity_gallery=8 |
| test_clip_0527 | person_03 | 4 | 12 | 12 | 6 | 12 | 24 | 1.0 | 1.0 | 3-3 | insufficient_same_identity_gallery=4 |
| test_clip_0527 | person_04 | 3 | 6 | 6 | 7 | 6 | 21 | 1.0 | 1.0 | 2-2 | insufficient_same_identity_gallery=3 |

## Additional Clips Needed

`additional clips needed` is the minimum extra same-identity gallery clips needed so a query can theoretically return 9 own clips. This is a dataset coverage limit, not a live identity field.

## Camera Pair Breakdown

| query_cam | candidate_cam | top-k candidates | own | wrong | precision | mean_score | outcomes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| cam_1 | cam_1 | 21 | 8 | 13 | 0.381 | 0.6554 | ambiguous=11, matched=4, no_match=6 |
| cam_1 | cam_2 | 11 | 7 | 4 | 0.6364 | 0.7463 | ambiguous=2, matched=7, no_match=2 |
| cam_1 | cam_3 | 3 | 2 | 1 | 0.6667 | 0.7409 | ambiguous=3 |
| cam_1 | cam_4 | 12 | 6 | 6 | 0.5 | 0.6184 | ambiguous=6, matched=1, no_match=5 |
| cam_1 | cam_5 | 16 | 9 | 7 | 0.5625 | 0.7646 | ambiguous=11, matched=5 |
| cam_2 | cam_1 | 12 | 7 | 5 | 0.5833 | 0.7194 | ambiguous=2, matched=7, no_match=3 |
| cam_2 | cam_2 | 2 | 2 | 0 | 1.0 | 0.9455 | matched=2 |
| cam_2 | cam_3 | 2 | 0 | 2 | 0.0 | 0.5597 | ambiguous=2 |
| cam_2 | cam_4 | 4 | 2 | 2 | 0.5 | 0.6667 | matched=2, no_match=2 |
| cam_2 | cam_5 | 7 | 5 | 2 | 0.7143 | 0.8497 | ambiguous=2, matched=5 |
| cam_3 | cam_1 | 6 | 2 | 4 | 0.3333 | 0.6489 | ambiguous=5, no_match=1 |
| cam_3 | cam_2 | 3 | 0 | 3 | 0.0 | 0.5383 | ambiguous=2, no_match=1 |
| cam_3 | cam_3 | 2 | 2 | 0 | 1.0 | 0.7771 | ambiguous=2 |
| cam_3 | cam_4 | 2 | 2 | 0 | 1.0 | 0.8313 | ambiguous=1, matched=1 |
| cam_3 | cam_5 | 5 | 2 | 3 | 0.4 | 0.5409 | ambiguous=2, no_match=3 |
| cam_4 | cam_1 | 10 | 6 | 4 | 0.6 | 0.6568 | ambiguous=7, matched=1, no_match=2 |
| cam_4 | cam_2 | 4 | 2 | 2 | 0.5 | 0.6761 | matched=2, no_match=2 |
| cam_4 | cam_3 | 3 | 2 | 1 | 0.6667 | 0.7196 | ambiguous=1, matched=1, no_match=1 |
| cam_4 | cam_4 | 3 | 0 | 3 | 0.0 | 0.5636 | ambiguous=2, no_match=1 |
| cam_4 | cam_5 | 7 | 4 | 3 | 0.5714 | 0.6161 | ambiguous=4, matched=1, no_match=2 |
| cam_5 | cam_1 | 19 | 9 | 10 | 0.4737 | 0.7187 | ambiguous=12, matched=5, no_match=2 |
| cam_5 | cam_2 | 7 | 5 | 2 | 0.7143 | 0.8497 | ambiguous=2, matched=5 |
| cam_5 | cam_3 | 3 | 1 | 2 | 0.3333 | 0.5581 | ambiguous=2, no_match=1 |
| cam_5 | cam_4 | 8 | 4 | 4 | 0.5 | 0.5837 | ambiguous=3, matched=1, no_match=4 |
| cam_5 | cam_5 | 8 | 2 | 6 | 0.25 | 0.8375 | ambiguous=4, matched=4 |

## Per Query Top-K

| query | dataset | identity | cam | gallery | available_positive_count | max_possible_own_count_at_9 | output_count | OwnCount@9 | Wrong@9 | Precision@9 | Recall@9 | Normalized OwnRecall@9 | insufficient_same_identity_gallery | readiness | crop_quality | top candidates |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527 | person_01 | cam_1 | 19 | 4 | 4 | 9 | 3 | 6 | 0.3333 | 0.75 | 0.75 | True | insufficient_same_identity_gallery | 0.8783 | test_clip_0527_person_01_cam_4_event_1779815845585:matched:0.8507, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.8081, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.7934, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.5861, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.5859, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.566, test_clip_0527_person_02_cam_1_event_1779819881971:no_match:0.5397, test_clip_0527_person_02_cam_2_event_1779819881964:no_match:0.5126, test_clip_0527_person_02_cam_1_event_1779817469639:no_match:0.5097 |
| test_clip_0527_person_01_cam_3_event_1779815845589 | test_clip_0527 | person_01 | cam_3 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9364 | test_clip_0527_person_01_cam_4_event_1779815845585:matched:0.8451, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.8081, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.7771, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.5758, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.5714, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.5638, test_clip_0527_person_02_cam_5_event_1779815845591:no_match:0.5221, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.4972, test_clip_0527_person_02_cam_2_event_1779815845587:no_match:0.4955 |
| test_clip_0527_person_01_cam_3_event_1779819881968 | test_clip_0527 | person_01 | cam_3 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8433 | test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.8174, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.7934, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.7771, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.6212, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.5808, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.5643, test_clip_0527_person_02_cam_2_event_1779819881964:ambiguous:0.5551, test_clip_0527_person_02_cam_5_event_1779819881966:no_match:0.533, test_clip_0527_person_02_cam_1_event_1779815845584:no_match:0.5308 |
| test_clip_0527_person_01_cam_4_event_1779815845585 | test_clip_0527 | person_01 | cam_4 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8629 | test_clip_0527_person_01_cam_1_event_1779815845583:matched:0.8507, test_clip_0527_person_01_cam_3_event_1779815845589:matched:0.8451, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.8174, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.6094, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.5993, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.5701, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.5637, test_clip_0527_person_02_cam_2_event_1779815845587:no_match:0.5179, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.4015 |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527 | person_01 | cam_5 | 19 | 4 | 4 | 9 | 2 | 7 | 0.2222 | 0.5 | 0.5 | True | insufficient_same_identity_gallery | 0.7563 | test_clip_0527_person_04_cam_2_event_1779815845597:matched:0.8322, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.7907, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7851, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.7649, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.7535, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.5808, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.5698, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.5604, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.4015 |
| test_clip_0527_person_02_cam_1_event_1779815845584 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8565 | test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.9046, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.9035, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8826, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8646, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.8126, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.81, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.7695, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.3492, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.2122 |
| test_clip_0527_person_02_cam_1_event_1779817469639 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8828 | test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8203, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8203, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.81, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.7956, test_clip_0527_person_02_cam_5_event_1779815845591:ambiguous:0.7953, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.7891, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.7533, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.5097, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.4876 |
| test_clip_0527_person_02_cam_1_event_1779819881971 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.7704 | test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8632, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8594, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8556, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8308, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.7695, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.7533, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.7505, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.6212, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.6094 |
| test_clip_0527_person_02_cam_2_event_1779815845587 | test_clip_0527 | person_02 | cam_2 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9248 | test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.9455, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.9046, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8779, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8748, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8632, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8364, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8203, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.5643, test_clip_0527_person_04_cam_1_event_1779815845601:no_match:0.2126 |
| test_clip_0527_person_02_cam_2_event_1779819881964 | test_clip_0527 | person_02 | cam_2 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9175 | test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.9455, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.9035, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8873, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.8772, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8594, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8449, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8203, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.5551, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.5126 |
| test_clip_0527_person_02_cam_4_event_1779815845590 | test_clip_0527 | person_02 | cam_4 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8738 | test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8449, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8364, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.8214, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.8126, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.8006, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.7891, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.7505, test_clip_0527_person_01_cam_3_event_1779819881968:no_match:0.4963, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.4922 |
| test_clip_0527_person_02_cam_5_event_1779815845591 | test_clip_0527 | person_02 | cam_5 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.6879 | test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.9418, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8873, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8826, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8779, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8556, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.8214, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.7953, test_clip_0527_person_01_cam_3_event_1779815845589:no_match:0.5221, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.5102 |
| test_clip_0527_person_02_cam_5_event_1779819881966 | test_clip_0527 | person_02 | cam_5 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.6879 | test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.9418, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.8772, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.8748, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8646, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8308, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.8006, test_clip_0527_person_02_cam_1_event_1779817469639:ambiguous:0.7956, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.5714, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.566 |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527 | person_03 | cam_1 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.9255 | test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.8833, test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.8432, test_clip_0527_person_04_cam_2_event_1779815845597:matched:0.8397, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.8104, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.8041, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7535, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.691, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5859, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.5317 |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527 | person_03 | cam_1 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8762 | test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.8833, test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.8298, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.8076, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7903, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7649, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7064, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6567, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.5256, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4908 |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527 | person_03 | cam_4 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8997 | test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.691, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.6567, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.6052, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.5993, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.5909, test_clip_0527_person_01_cam_5_event_1779815845586:no_match:0.5297, test_clip_0527_person_04_cam_2_event_1779815845597:no_match:0.505, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4888, test_clip_0527_person_02_cam_1_event_1779815845584:no_match:0.3492 |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527 | person_03 | cam_5 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.7452 | test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.8324, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.8041, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.7903, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7851, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.7825, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6412, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6052, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.48, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4512 |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527 | person_04 | cam_1 | 19 | 2 | 2 | 9 | 2 | 7 | 0.2222 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8695 | test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.8432, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.7064, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.6797, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.6656, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.6412, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.5698, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.3663, test_clip_0527_person_02_cam_2_event_1779815845587:no_match:0.2126, test_clip_0527_person_02_cam_1_event_1779815845584:no_match:0.2122 |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527 | person_04 | cam_2 | 19 | 2 | 2 | 9 | 2 | 7 | 0.2222 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.8829 | test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.8397, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.8322, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.816, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.8076, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7825, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6656, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.505, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.4806, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4237 |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527 | person_04 | cam_5 | 19 | 2 | 2 | 9 | 2 | 7 | 0.2222 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | 0.7424 | test_clip_0527_person_03_cam_5_event_1779815845594:matched:0.8324, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.8298, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.816, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.8104, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7907, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6797, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.5909, test_clip_0527_person_01_cam_4_event_1779815845585:no_match:0.4599, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.4101 |
