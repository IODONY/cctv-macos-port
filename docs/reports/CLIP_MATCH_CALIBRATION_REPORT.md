# Clip Match Calibration Report

This report uses the current labeled clips as a development set. It is for tuning the evaluator, not proof of generalization.

## Selected Runtime Settings

- Match threshold: `0.72`
- Ambiguous threshold: `0.25`
- Minimum available weight: `2.8`
- Same-camera weights: `{'top': 1.5, 'bottom': 0.9, 'bag': 0.8, 'is_long_sleeve': 0.6, 'is_long_pants': 0.4, 'torso_ratio': 1.0, 'brightness_ratio': 0.7}`
- Cross-camera weights: `{'top': 1.9, 'bottom': 0.35, 'bag': 0.7, 'is_long_sleeve': 0.45, 'is_long_pants': 0.25, 'torso_ratio': 1.25, 'brightness_ratio': 0.2}`

## Best Zero-Incorrect Candidates

| weight_set | match | ambiguous | correct | incorrect | uncertain | low_confidence | matched | no_match |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| camera_aware_default | 0.72 | 0.25 | 51 | 0 | 97 | 0 | 22 | 29 |
| camera_aware_default | 0.72 | 0.2 | 48 | 0 | 100 | 0 | 22 | 26 |
| top_torso_cross_camera | 0.72 | 0.2 | 48 | 0 | 100 | 0 | 22 | 26 |
| camera_aware_default | 0.74 | 0.25 | 47 | 0 | 101 | 0 | 18 | 29 |
| top_torso_cross_camera | 0.74 | 0.2 | 46 | 0 | 102 | 0 | 20 | 26 |
| camera_aware_default | 0.74 | 0.2 | 44 | 0 | 104 | 0 | 18 | 26 |
| camera_aware_default | 0.76 | 0.25 | 44 | 0 | 104 | 0 | 15 | 29 |
| camera_aware_default | 0.78 | 0.25 | 43 | 0 | 105 | 0 | 14 | 29 |

## Tuning Direction

- Keep `incorrect=0` as the first constraint.
- Prefer candidates that reduce `low_confidence` without turning hard negatives into `matched`.
- Cross-camera brightness remains a weak feature because camera exposure shifts are visible in the current clips.
