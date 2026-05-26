# Top-K Output System Design

## Goal

The runtime system should return a ranked list of 9 to 12 likely clip paths for display when a query arrives from an exhibition trigger camera. The system must return clips, not a final `matched` or `ambiguous` label. Pairwise outcomes can remain internal scoring signals, but the display output is a Top-K ranked list.

In live exhibition mode, `identity_id` is not available. Identity labels are only used in offline labeled evaluation.

## Runtime Flow

1. First and second floor cameras record gallery clips.
2. YOLO-based person detection triggers recording on and off.
3. Each completed clip or tracklet is analyzed for best shots.
4. The selected best shot, crop, or tracklet representation is converted into an appearance ReID embedding or equivalent retrieval profile.
5. The gallery stores one or more retrieval records per clip or tracklet:
   - `clip_id`
   - `clip_path`
   - `dataset_id` or session id
   - `cam_id`
   - `event_id`
   - embedding/profile vector
   - quality metadata
6. A third-floor query event creates a query clip, best shot, and query embedding/profile.
7. The ranker compares the query against gallery records and returns Top-K results.
8. If the high-confidence result count is too small, fallback fills missing slots with lower-confidence but non-blocked candidates.
9. TouchDesigner receives a payload with ranked clip paths and scores.

## Ranking Behavior

The ranker should prioritize enough output clips and high own-identity recall in labeled evaluation. In live mode, it should prioritize:

- High retrieval score.
- Strong crop or tracklet quality.
- Compatible camera/time routing when configured.
- Diversity only when it does not remove strong likely matches.
- Fallback candidates when fewer than 9 strong candidates exist.

`matched`, `ambiguous`, `low_confidence`, and `no_match` can be preserved as internal debug fields. They should not be the final display output contract.

## Fallback Fill

Fallback exists to keep the display populated:

1. Return all high-confidence candidates first.
2. Fill remaining slots from ambiguous or lower-confidence candidates ranked by score.
3. Keep hard contradiction or blocked candidates below fallback candidates unless the gallery is extremely thin.
4. Mark fallback candidates in logs and debug reports.

This fallback is for output continuity. It should not hide low-quality retrieval behavior in evaluation reports.

## Proposed JSON Payload

```json
{
  "event_id": "event_1779815845594",
  "query_id": "query_cam_5_event_1779815845594",
  "k": 9,
  "candidate_pool": 12,
  "results": [
    {
      "rank": 1,
      "clip_id": "test_clip_0527_person_03_cam_1_event_1779815845592",
      "clip_path": "data/labeld_clips/test_clip_0527/person_03/cam_1_event_1779815845592.mp4",
      "score": 0.83,
      "cam_id": "cam_1",
      "dataset_id": "test_clip_0527",
      "fallback": false,
      "identity_debug": "only in labeled evaluation"
    }
  ]
}
```

## Proposed OSC Shape

For TouchDesigner, keep OSC compact and deterministic:

- `/walnut/topk/event_id`
- `/walnut/topk/query_id`
- `/walnut/topk/k`
- `/walnut/topk/result/1/clip_id`
- `/walnut/topk/result/1/path`
- `/walnut/topk/result/1/score`
- `/walnut/topk/result/1/cam_id`
- `/walnut/topk/result/1/fallback`

The payload should not include `identity_id` in live mode. Offline evaluation may log `identity_debug` separately to measure Recall@9 and OwnCount@9.

## Output Readiness

A query is output-ready when:

- It returns 9 clip paths.
- The gallery has enough candidates to fill the requested K.
- Labeled evaluation shows enough own-identity clips in Top-K when enough same-identity gallery clips exist.
- Fallback usage is visible in logs and does not dominate the output.

If the labeled dataset has fewer than 9 same-identity gallery clips, the query should be marked `insufficient_same_identity_gallery`, not a pure ranking failure.
