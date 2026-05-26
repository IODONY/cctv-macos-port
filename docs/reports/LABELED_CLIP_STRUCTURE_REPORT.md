# Labeled Clip Structure Report

- Inspected source root: `data/labeld_clips`
- Preferred `data/labeled_clips/` exists: `False`
- Legacy `data/labeld_clips/` exists: `True`
- Origin excluded: `True`
- Total labeled clips: `38`
- Top-K target: `9`

## Detected Dataset Folders

- `direct root identities`
- `test_clip_0527`

## Detected Filename Patterns

- `event_id`: `20` clips
- `take_index`: `18` clips

## Identity Clip Counts

| dataset_id | identity_id | clips | available_positive_count | max_possible_own_count_at_9 | normalized_own_recall_at_9 | additional_clips_needed_for_top_9_own | enough_same_identity_for_top_9 | layout_type |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| root | person_001 | 4 | 3 | 3 | 1.0000 | 6 | False | direct_identity |
| root | person_002 | 7 | 6 | 6 | 1.0000 | 3 | False | direct_identity |
| root | person_003 | 7 | 6 | 6 | 1.0000 | 3 | False | direct_identity |
| test_clip_0527 | person_01 | 5 | 4 | 4 | 1.0000 | 5 | False | nested_dataset_identity |
| test_clip_0527 | person_02 | 8 | 7 | 7 | 1.0000 | 2 | False | nested_dataset_identity |
| test_clip_0527 | person_03 | 4 | 3 | 3 | 1.0000 | 6 | False | nested_dataset_identity |
| test_clip_0527 | person_04 | 3 | 2 | 2 | 1.0000 | 7 | False | nested_dataset_identity |

## Interpretation

- `available_positive_count` is the same-identity gallery count for leave-one-out evaluation.
- `max_possible_own_count_at_9` is capped by both `9` and available same-identity gallery clips.
- A low own-count is not automatically an algorithm failure when the same-identity gallery is too small.
- `additional_clips_needed_for_top_9_own` counts extra same-identity gallery clips needed per query.
