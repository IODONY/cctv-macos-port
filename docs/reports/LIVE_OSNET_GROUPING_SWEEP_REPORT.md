# Live OSNet Similarity Grouping Sweep

This report re-embeds saved live `_best.jpg` crops only. It does not run RTSP, webcam, TouchDesigner, or live tracking.

## Source

- Events: `logs/topk_live/20260530_020213/gallery_events.jsonl`
- Records embedded: `18`
- Embedding model: `osnet_x0_25`
- Embedding method: `torchreid_osnet_x0_25`

## Threshold Sweep

| threshold | connected groups | connected sizes | live-centroid groups | live-centroid sizes |
| ---: | ---: | --- | ---: | --- |
| 0.50 | 1 | [18] | 1 | [18] |
| 0.55 | 1 | [18] | 5 | [7, 7, 2, 1, 1] |
| 0.60 | 4 | [12, 4, 1, 1] | 6 | [8, 4, 2, 2, 1, 1] |
| 0.65 | 8 | [7, 4, 2, 1, 1, 1, 1, 1] | 9 | [5, 4, 2, 2, 1, 1, 1, 1, 1] |
| 0.70 | 9 | [5, 4, 2, 2, 1, 1, 1, 1, 1] | 9 | [5, 4, 2, 2, 1, 1, 1, 1, 1] |
| 0.72 | 9 | [5, 4, 2, 2, 1, 1, 1, 1, 1] | 10 | [4, 4, 2, 2, 1, 1, 1, 1, 1, 1] |

## Pairwise Similarity

- Min: `0.3319`
- Mean: `0.5299`
- Median: `0.5115`
- Max: `0.8799`

## Interpretation

- For a single-person smoke session, a lower group count is desirable.
- The connected grouping column shows whether the embedding space links the saved crops together.
- The live-centroid column approximates the current online export grouping logic.
- If different visitors merge in future tests, raise `--similarity-group-threshold`; if the same visitor splits, lower it or add session-end merge.
