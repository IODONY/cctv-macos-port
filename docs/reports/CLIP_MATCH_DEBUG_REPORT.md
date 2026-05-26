# Clip Match Debug Report

## Summary

The labeled-clip evaluation harness was tested on `data/labeld_clips/` using 18 local MP4 clips and 148 generated pairs. No camera, RTSP, TouchDesigner, or full tracking run was started.

## Iterations

| Iteration | Key behavior | Correct | Incorrect | Uncertain | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| Baseline Type C-style score | bag / torso / brightness score only | 13 | 1 | 134 | Too many low-confidence and ambiguous negatives. |
| Appearance-weighted score + provisional profiles | top, bottom, bag, sleeve, pants, torso, brightness | 40 | 0 | 108 | False incorrect removed, but match threshold was conservative. |
| Match threshold `0.75` | Same weighted score with lower match threshold | 46 | 0 | 102 | Best current setting on this dataset. |
| Clip evidence profile + camera-aware weights | Aggregates frame-level evidence and separates same/cross-camera weights | 51 | 0 | 97 | Removes low-confidence outcomes while preserving ambiguous cases. |

## Current Defaults

- Match threshold: `0.72`
- Ambiguous threshold: `0.25`
- Minimum comparable weight: `2.8`
- Same-camera weights: `top=1.5,bottom=0.9,bag=0.8,is_long_sleeve=0.6,is_long_pants=0.4,torso_ratio=1.0,brightness_ratio=0.7`
- Cross-camera weights: `top=1.9,bottom=0.35,bag=0.7,is_long_sleeve=0.45,is_long_pants=0.25,torso_ratio=1.25,brightness_ratio=0.2`

## Current Result

- Total pairs: `148`
- Correct: `51`
- Incorrect: `0`
- Uncertain: `97`
- Outcomes:
  - `matched`: `22`
  - `ambiguous`: `97`
  - `no_match`: `29`
  - `low_confidence`: `0`

## Remaining Debug Notes

- Clip-level evidence profiles reduce dependence on one finalized or provisional frame.
- Cross-camera brightness is intentionally downweighted because exposure shifts are visible across the current clips.
- Strong contradiction rules only create `no_match` when stable appearance fields conflict together, such as `top+bag` or `sleeve+pants`.
- This keeps the artwork invariant intact: uncertain tracking remains visible as `ambiguous` instead of being collapsed into a hard identity decision.
