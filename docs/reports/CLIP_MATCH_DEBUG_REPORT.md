# Clip Match Debug Report

## Summary

The labeled-clip evaluation harness was tested on `data/labeld_clips/` using 18 local MP4 clips and 148 generated pairs. No camera, RTSP, TouchDesigner, or full tracking run was started.

## Iterations

| Iteration | Key behavior | Correct | Incorrect | Uncertain | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| Baseline Type C-style score | bag / torso / brightness score only | 13 | 1 | 134 | Too many low-confidence and ambiguous negatives. |
| Appearance-weighted score + provisional profiles | top, bottom, bag, sleeve, pants, torso, brightness | 40 | 0 | 108 | False incorrect removed, but match threshold was conservative. |
| Match threshold `0.75` | Same weighted score with lower match threshold | 46 | 0 | 102 | Best current setting on this dataset. |

## Current Defaults

- Match threshold: `0.75`
- Ambiguous threshold: `0.60`
- Default weights:
  - `top=1.4`
  - `bottom=1.0`
  - `bag=0.8`
  - `is_long_sleeve=0.7`
  - `is_long_pants=0.5`
  - `torso_ratio=1.0`
  - `brightness_ratio=0.8`

## Current Result

- Total pairs: `148`
- Correct: `46`
- Incorrect: `0`
- Uncertain: `102`
- Outcomes:
  - `matched`: `9`
  - `ambiguous`: `9`
  - `no_match`: `37`
  - `low_confidence`: `93`

## Remaining Debug Notes

- `low_confidence` is still high because several clips do not produce full 75-frame stable profiles.
- Provisional profiles are allowed for scoring, but any low-score provisional comparison remains `low_confidence` rather than becoming `no_match`.
- This keeps the artwork invariant intact: uncertain tracking remains visible as `ambiguous` or `low_confidence` instead of being collapsed into a hard identity decision.
