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
- Match threshold: `0.72`
- Ambiguous threshold: `0.25`

## Headline

- `Recall@9` macro/query mean: `0.9375`
- `Recall@9` micro/positive-weighted: `0.9468` (89/94)
- `Normalized OwnRecall@9` micro: `0.9468` (89/94)
- `Precision@9` macro/query mean: `0.4944`
- `OwnCount@9` mean: `4.45`
- `Wrong@9` mean: `4.55`
- `TopK output count` mean: `9.0`
- Insufficient same-identity gallery queries: `20`
- Output readiness counts: `insufficient_same_identity_gallery=20`

## Summary Metrics

- `additional_gallery_clips_needed_for_top_9_own`: `2`
- `max_available_positive_count_for_any_query`: `7`
- `max_own_at_9`: `7`
- `mean_ambiguous_rate_at_9`: `0.4333`
- `mean_false_match_rate_at_9`: `0.1333`
- `mean_hard_negative_rate_at_9`: `0.1167`
- `mean_normalized_own_recall_at_9`: `0.9375`
- `mean_own_at_12`: `4.5`
- `mean_own_at_9`: `4.45`
- `mean_precision_at_12`: `0.375`
- `mean_precision_at_9`: `0.4944`
- `mean_recall_at_12`: `0.95`
- `mean_recall_at_9`: `0.9375`
- `mean_topk_output_count_at_9`: `9.0`
- `mean_wrong_at_12`: `7.5`
- `mean_wrong_at_9`: `4.55`
- `micro_normalized_own_recall_at_9`: `0.9468`
- `micro_precision_at_12`: `0.375`
- `micro_precision_at_9`: `0.4944`
- `micro_recall_at_12`: `0.9574`
- `micro_recall_at_9`: `0.9468`
- `min_own_at_9`: `1`
- `output_readiness_counts`: `{'insufficient_same_identity_gallery': 20}`
- `queries_with_insufficient_gallery`: `0`
- `queries_with_insufficient_same_identity_gallery`: `20`
- `queries_with_majority_own_at_9`: `8`
- `query_count`: `20`
- `total_available_positive_count`: `94`
- `total_max_possible_own_count_at_9`: `94`
- `total_own_at_12`: `90`
- `total_own_at_9`: `89`
- `total_returned_at_12`: `240`
- `total_returned_at_9`: `180`
- `total_wrong_at_12`: `150`
- `total_wrong_at_9`: `91`

## Dataset Breakdown

| dataset | queries | OwnCount@9 total | Wrong@9 total | Recall@9 micro | Normalized OwnRecall@9 micro | Precision@9 micro | readiness |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| test_clip_0527 | 20 | 89 | 91 | 0.9468 | 0.9468 | 0.4944 | insufficient_same_identity_gallery=20 |

## Identity Breakdown

| dataset | identity | queries | available positives | max possible own@9 | additional clips needed | OwnCount@9 total | Wrong@9 total | Recall@9 micro | Normalized OwnRecall@9 micro | own@9 min-max | readiness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| test_clip_0527 | person_01 | 5 | 20 | 20 | 5 | 15 | 30 | 0.75 | 0.75 | 1-4 | insufficient_same_identity_gallery=5 |
| test_clip_0527 | person_02 | 8 | 56 | 56 | 2 | 56 | 16 | 1.0 | 1.0 | 7-7 | insufficient_same_identity_gallery=8 |
| test_clip_0527 | person_03 | 4 | 12 | 12 | 6 | 12 | 24 | 1.0 | 1.0 | 3-3 | insufficient_same_identity_gallery=4 |
| test_clip_0527 | person_04 | 3 | 6 | 6 | 7 | 6 | 21 | 1.0 | 1.0 | 2-2 | insufficient_same_identity_gallery=3 |

## Additional Clips Needed

`additional clips needed` is the minimum extra same-identity gallery clips needed so a query can theoretically return 9 own clips. This is a dataset coverage limit, not a live identity field.

## Camera Pair Breakdown

| query_cam | candidate_cam | top-k candidates | own | wrong | precision | mean_score | outcomes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| cam_1 | cam_1 | 21 | 8 | 13 | 0.381 | 0.6874 | ambiguous=11, matched=8, no_match=2 |
| cam_1 | cam_2 | 9 | 7 | 2 | 0.7778 | 0.9619 | ambiguous=1, matched=8 |
| cam_1 | cam_3 | 5 | 2 | 3 | 0.4 | 0.7328 | ambiguous=3, matched=2 |
| cam_1 | cam_4 | 11 | 6 | 5 | 0.5455 | 0.6766 | ambiguous=6, matched=4, no_match=1 |
| cam_1 | cam_5 | 17 | 9 | 8 | 0.5294 | 0.8847 | ambiguous=5, matched=12 |
| cam_2 | cam_1 | 10 | 7 | 3 | 0.7 | 0.9094 | ambiguous=2, matched=8 |
| cam_2 | cam_2 | 2 | 2 | 0 | 1.0 | 1.0 | matched=2 |
| cam_2 | cam_3 | 4 | 0 | 4 | 0.0 | 0.551 | ambiguous=4 |
| cam_2 | cam_4 | 4 | 2 | 2 | 0.5 | 0.7427 | ambiguous=2, matched=2 |
| cam_2 | cam_5 | 7 | 5 | 2 | 0.7143 | 0.9915 | matched=7 |
| cam_3 | cam_1 | 5 | 2 | 3 | 0.4 | 0.7328 | ambiguous=3, matched=2 |
| cam_3 | cam_2 | 3 | 0 | 3 | 0.0 | 0.563 | ambiguous=3 |
| cam_3 | cam_3 | 2 | 2 | 0 | 1.0 | 0.9334 | matched=2 |
| cam_3 | cam_4 | 4 | 2 | 2 | 0.5 | 0.7664 | ambiguous=2, matched=2 |
| cam_3 | cam_5 | 4 | 2 | 2 | 0.5 | 0.5849 | ambiguous=4 |
| cam_4 | cam_1 | 10 | 6 | 4 | 0.6 | 0.7419 | ambiguous=6, matched=4 |
| cam_4 | cam_2 | 3 | 2 | 1 | 0.6667 | 0.845 | ambiguous=1, matched=2 |
| cam_4 | cam_3 | 5 | 2 | 3 | 0.4 | 0.6766 | ambiguous=2, matched=2, no_match=1 |
| cam_4 | cam_4 | 2 | 0 | 2 | 0.0 | 0.674 | ambiguous=2 |
| cam_4 | cam_5 | 7 | 3 | 4 | 0.4286 | 0.7026 | ambiguous=5, matched=2 |
| cam_5 | cam_1 | 19 | 9 | 10 | 0.4737 | 0.8485 | ambiguous=7, matched=12 |
| cam_5 | cam_2 | 7 | 5 | 2 | 0.7143 | 0.9915 | matched=7 |
| cam_5 | cam_3 | 4 | 1 | 3 | 0.25 | 0.5572 | ambiguous=4 |
| cam_5 | cam_4 | 7 | 3 | 4 | 0.4286 | 0.6962 | ambiguous=5, matched=2 |
| cam_5 | cam_5 | 8 | 2 | 6 | 0.25 | 0.9883 | matched=8 |

## Per Query Top-K

| query | dataset | identity | cam | gallery | available_positive_count | max_possible_own_count_at_9 | output_count | OwnCount@9 | Wrong@9 | Precision@9 | Recall@9 | Normalized OwnRecall@9 | insufficient_same_identity_gallery | readiness | top candidates |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| test_clip_0527_person_01_cam_1_event_1779815845583 | test_clip_0527 | person_01 | cam_1 | 19 | 4 | 4 | 9 | 3 | 6 | 0.3333 | 0.75 | 0.75 | True | insufficient_same_identity_gallery | test_clip_0527_person_01_cam_4_event_1779815845585:matched:0.9904, test_clip_0527_person_01_cam_3_event_1779815845589:matched:0.9327, test_clip_0527_person_01_cam_3_event_1779819881968:matched:0.9097, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.6389, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.591, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.5471, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.5465, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.5271, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.5239 |
| test_clip_0527_person_01_cam_3_event_1779815845589 | test_clip_0527 | person_01 | cam_3 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_01_cam_4_event_1779815845585:matched:0.9922, test_clip_0527_person_01_cam_3_event_1779819881968:matched:0.9334, test_clip_0527_person_01_cam_1_event_1779815845583:matched:0.9327, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.639, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.5798, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.5695, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.5553, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.5424, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.5174 |
| test_clip_0527_person_01_cam_3_event_1779819881968 | test_clip_0527 | person_01 | cam_3 | 19 | 4 | 4 | 9 | 4 | 5 | 0.4444 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_01_cam_4_event_1779815845585:matched:0.9427, test_clip_0527_person_01_cam_3_event_1779815845589:matched:0.9334, test_clip_0527_person_01_cam_1_event_1779815845583:matched:0.9097, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6291, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.6271, test_clip_0527_person_02_cam_4_event_1779815845590:ambiguous:0.5883, test_clip_0527_person_02_cam_2_event_1779815845587:ambiguous:0.5871, test_clip_0527_person_02_cam_2_event_1779819881964:ambiguous:0.5846, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.5611 |
| test_clip_0527_person_01_cam_4_event_1779815845585 | test_clip_0527 | person_01 | cam_4 | 19 | 4 | 4 | 9 | 3 | 6 | 0.3333 | 0.75 | 0.75 | True | insufficient_same_identity_gallery | test_clip_0527_person_01_cam_3_event_1779815845589:matched:0.9922, test_clip_0527_person_01_cam_1_event_1779815845583:matched:0.9904, test_clip_0527_person_01_cam_3_event_1779819881968:matched:0.9427, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.674, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.5989, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.5684, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.5529, test_clip_0527_person_02_cam_5_event_1779819881966:ambiguous:0.5486, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.547 |
| test_clip_0527_person_01_cam_5_event_1779815845586 | test_clip_0527 | person_01 | cam_5 | 19 | 4 | 4 | 9 | 1 | 8 | 0.1111 | 0.25 | 0.25 | True | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_2_event_1779815845597:matched:1.0, test_clip_0527_person_03_cam_5_event_1779815845594:matched:1.0, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.9958, test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.9827, test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.9532, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7063, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.6291, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6265, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.5947 |
| test_clip_0527_person_02_cam_1_event_1779815845584 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_2_event_1779815845587:matched:1.0, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.9959, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.9941, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.9805, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.9694, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8763, test_clip_0527_person_02_cam_1_event_1779819881971:ambiguous:0.7916, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.5553, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5471 |
| test_clip_0527_person_02_cam_1_event_1779817469639 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.9715, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.9708, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.9696, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.9644, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.9617, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.8796, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.8763, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.4959, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.4738 |
| test_clip_0527_person_02_cam_1_event_1779819881971 | test_clip_0527 | person_02 | cam_1 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.9827, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.9789, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.9701, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.9378, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.9152, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.8796, test_clip_0527_person_02_cam_1_event_1779815845584:ambiguous:0.7916, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.639, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.6271 |
| test_clip_0527_person_02_cam_2_event_1779815845587 | test_clip_0527 | person_02 | cam_2 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_4_event_1779815845590:matched:1.0, test_clip_0527_person_02_cam_2_event_1779819881964:matched:1.0, test_clip_0527_person_02_cam_1_event_1779815845584:matched:1.0, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.9884, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.9827, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.9812, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.9715, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.5871, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.5174 |
| test_clip_0527_person_02_cam_2_event_1779819881964 | test_clip_0527 | person_02 | cam_2 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_4_event_1779815845590:matched:1.0, test_clip_0527_person_02_cam_2_event_1779815845587:matched:1.0, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.9941, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.9876, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.9834, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.9789, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.9696, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.5846, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.5149 |
| test_clip_0527_person_02_cam_4_event_1779815845590 | test_clip_0527 | person_02 | cam_4 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_2_event_1779815845587:matched:1.0, test_clip_0527_person_02_cam_2_event_1779819881964:matched:1.0, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.9959, test_clip_0527_person_02_cam_5_event_1779815845591:matched:0.982, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.9708, test_clip_0527_person_02_cam_5_event_1779819881966:matched:0.9416, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.9152, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.5883, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.5424 |
| test_clip_0527_person_02_cam_5_event_1779815845591 | test_clip_0527 | person_02 | cam_5 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_5_event_1779819881966:matched:1.0, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.9834, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.982, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.9812, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.9805, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.9701, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.9617, test_clip_0527_person_01_cam_3_event_1779819881968:ambiguous:0.5102, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.5095 |
| test_clip_0527_person_02_cam_5_event_1779819881966 | test_clip_0527 | person_02 | cam_5 | 19 | 7 | 7 | 9 | 7 | 2 | 0.7778 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_02_cam_5_event_1779815845591:matched:1.0, test_clip_0527_person_02_cam_2_event_1779815845587:matched:0.9884, test_clip_0527_person_02_cam_2_event_1779819881964:matched:0.9876, test_clip_0527_person_02_cam_1_event_1779815845584:matched:0.9694, test_clip_0527_person_02_cam_1_event_1779817469639:matched:0.9644, test_clip_0527_person_02_cam_4_event_1779815845590:matched:0.9416, test_clip_0527_person_02_cam_1_event_1779819881971:matched:0.9378, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.591, test_clip_0527_person_01_cam_3_event_1779815845589:ambiguous:0.5798 |
| test_clip_0527_person_03_cam_1_event_1779815845592 | test_clip_0527 | person_03 | cam_1 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_2_event_1779815845597:matched:1.0, test_clip_0527_person_03_cam_5_event_1779815845594:matched:1.0, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.9827, test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.9722, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.9696, test_clip_0527_person_04_cam_1_event_1779815845601:matched:0.898, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6732, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.6389, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.547 |
| test_clip_0527_person_03_cam_1_event_1779815845596 | test_clip_0527 | person_03 | cam_1 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_5_event_1779815845594:matched:1.0, test_clip_0527_person_04_cam_2_event_1779815845597:matched:0.9988, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.9958, test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.9696, test_clip_0527_person_04_cam_5_event_1779815845598:matched:0.964, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.6776, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.654, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.5529, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5232 |
| test_clip_0527_person_03_cam_4_event_1779815845595 | test_clip_0527 | person_03 | cam_4 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.674, test_clip_0527_person_03_cam_1_event_1779815845592:ambiguous:0.6732, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.654, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.6477, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.6265, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.6035, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.535, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5208, test_clip_0527_person_01_cam_3_event_1779819881968:no_match:0.3176 |
| test_clip_0527_person_03_cam_5_event_1779815845594 | test_clip_0527 | person_03 | cam_5 | 19 | 3 | 3 | 9 | 3 | 6 | 0.3333 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_2_event_1779815845597:matched:1.0, test_clip_0527_person_03_cam_1_event_1779815845596:matched:1.0, test_clip_0527_person_04_cam_5_event_1779815845598:matched:1.0, test_clip_0527_person_03_cam_1_event_1779815845592:matched:1.0, test_clip_0527_person_01_cam_5_event_1779815845586:matched:1.0, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7591, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6477, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.5684, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.5239 |
| test_clip_0527_person_04_cam_1_event_1779815845601 | test_clip_0527 | person_04 | cam_1 | 19 | 2 | 2 | 9 | 2 | 7 | 0.2222 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.898, test_clip_0527_person_04_cam_2_event_1779815845597:ambiguous:0.7616, test_clip_0527_person_04_cam_5_event_1779815845598:ambiguous:0.7609, test_clip_0527_person_03_cam_5_event_1779815845594:ambiguous:0.7591, test_clip_0527_person_01_cam_5_event_1779815845586:ambiguous:0.7063, test_clip_0527_person_03_cam_1_event_1779815845596:ambiguous:0.6776, test_clip_0527_person_01_cam_1_event_1779815845583:no_match:0.232, test_clip_0527_person_03_cam_4_event_1779815845595:no_match:0.1426, test_clip_0527_person_02_cam_1_event_1779817469639:no_match:0.081 |
| test_clip_0527_person_04_cam_2_event_1779815845597 | test_clip_0527 | person_04 | cam_2 | 19 | 2 | 2 | 9 | 2 | 7 | 0.2222 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_5_event_1779815845598:matched:1.0, test_clip_0527_person_03_cam_5_event_1779815845594:matched:1.0, test_clip_0527_person_01_cam_5_event_1779815845586:matched:1.0, test_clip_0527_person_03_cam_1_event_1779815845592:matched:1.0, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.9988, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7616, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.535, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.4369, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.4359 |
| test_clip_0527_person_04_cam_5_event_1779815845598 | test_clip_0527 | person_04 | cam_5 | 19 | 2 | 2 | 9 | 2 | 7 | 0.2222 | 1.0 | 1.0 | True | insufficient_same_identity_gallery | test_clip_0527_person_04_cam_2_event_1779815845597:matched:1.0, test_clip_0527_person_03_cam_5_event_1779815845594:matched:1.0, test_clip_0527_person_03_cam_1_event_1779815845592:matched:0.9722, test_clip_0527_person_03_cam_1_event_1779815845596:matched:0.964, test_clip_0527_person_01_cam_5_event_1779815845586:matched:0.9532, test_clip_0527_person_04_cam_1_event_1779815845601:ambiguous:0.7609, test_clip_0527_person_03_cam_4_event_1779815845595:ambiguous:0.6035, test_clip_0527_person_01_cam_4_event_1779815845585:ambiguous:0.5036, test_clip_0527_person_01_cam_1_event_1779815845583:ambiguous:0.4871 |
