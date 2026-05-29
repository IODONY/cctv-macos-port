# Live OSNet Similarity Grouping Sweep

This report re-embeds saved live `_best.jpg` crops only. It does not run RTSP, webcam, TouchDesigner, or live tracking.

## Source

- Events: `logs/topk_live/20260530_020213/gallery_events.jsonl`
- Records embedded: `18`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`
- Reciprocal top-N: `5`

## Threshold Sweep

| threshold | connected groups | connected sizes | reciprocal groups | reciprocal sizes | centroid groups | centroid sizes |
| ---: | ---: | --- | ---: | --- | ---: | --- |
| 0.50 | 1 | [18] | 2 | [16, 2] | 1 | [18] |
| 0.55 | 1 | [18] | 2 | [16, 2] | 5 | [7, 7, 2, 1, 1] |
| 0.60 | 4 | [12, 4, 1, 1] | 5 | [10, 4, 2, 1, 1] | 6 | [8, 4, 2, 2, 1, 1] |
| 0.65 | 8 | [7, 4, 2, 1, 1, 1, 1, 1] | 8 | [7, 4, 2, 1, 1, 1, 1, 1] | 9 | [5, 4, 2, 2, 1, 1, 1, 1, 1] |
| 0.70 | 9 | [5, 4, 2, 2, 1, 1, 1, 1, 1] | 9 | [5, 4, 2, 2, 1, 1, 1, 1, 1] | 9 | [5, 4, 2, 2, 1, 1, 1, 1, 1] |
| 0.72 | 9 | [5, 4, 2, 2, 1, 1, 1, 1, 1] | 9 | [5, 4, 2, 2, 1, 1, 1, 1, 1] | 10 | [4, 4, 2, 2, 1, 1, 1, 1, 1, 1] |

## Pairwise Similarity

- Count: `153`
- Min: `0.331876`
- Mean: `0.529863`
- Median: `0.511509`
- Max: `0.879869`

## Interpretation

- For a single-person smoke session, a lower group count is desirable.
- `connected` shows whether saved crops are linked by any threshold path.
- `reciprocal` is the intended final session-end grouping mode.
- `centroid` approximates the online temporary grouping behavior.
