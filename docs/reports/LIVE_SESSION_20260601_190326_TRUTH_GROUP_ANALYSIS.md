# 20260601_190326 Truth Group Analysis

이 리포트는 사용자가 `snapshots/live_topk/20260601_190326/similarity_groups_merged/` 아래에 재정리한 정답 폴더 `p1~p5`를 기준으로, 왜 한 사람이 여러 similarity group으로 나뉘었는지 분석한 결과다.

카메라, RTSP, TouchDesigner는 실행하지 않았고, 저장된 `_best.jpg`와 `gallery_events.jsonl`만 다시 분석했다.

## Source

- Session: `20260601_190326`
- Gallery events: `logs/topk_live/20260601_190326/gallery_events.jsonl`
- User truth folders: `snapshots/live_topk/20260601_190326/similarity_groups_merged/p1` ... `p5`
- Extra non-person/invalid folder: `snapshots/live_topk/20260601_190326/similarity_groups_merged/too_small_reconazing_people_n1`
- Contact sheets: `snapshots/testdata/test_0601_190326_truth_contact/`

## Truth Folder Counts

| truth folder | best crops | note |
| --- | ---: | --- |
| `p1` | 9 | 기존 merged `group_001`과 일치 |
| `p2` | 10 | 여러 그룹으로 쪼개짐 |
| `p3` | 5 | 기존 merged `group_003`과 일치 |
| `p4` | 4 | 여러 그룹으로 쪼개짐 |
| `p5` | 0 | `.DS_Store`만 있음 |
| `too_small_reconazing_people_n1` | 2 | 화면 가장자리/부분 인물 crop, 정식 인물 그룹에서 제외해야 함 |

## Existing Merge Result

기존 세션 종료 병합은 `best crop 1장`만 OSNet으로 다시 임베딩하고, `reciprocal`, threshold `0.65`, top-N `4`로 묶었다.

| truth | existing grouping |
| --- | --- |
| `p1` | 9개 전부 `group_001` |
| `p2` | `group_002` 6개, `group_005` 2개, `group_008` 1개, `group_009` 1개 |
| `p3` | 5개 전부 `group_003` |
| `p4` | `group_004` 2개, `group_007` 1개, `group_010` 1개 |
| `too_small_reconazing_people_n1` | 2개 전부 `group_006` |

즉 실제 문제는 전체가 무작위로 틀린 것이 아니라, `p2`와 `p4`의 일부 clip이 singleton 또는 작은 그룹으로 떨어진 것이다.

## Main Causes

1. 세션 종료 병합이 live gallery와 다른 임베딩 방식을 사용했다.

   live gallery 등록은 `top-N crop embedding 평균`을 사용할 수 있는데, 기존 `regroup_live_session`은 `_best.jpg` 하나만 다시 임베딩했다. 같은 clip 안에서도 crop 각도와 가려짐이 다르기 때문에 best 1장만 쓰면 사람이 쪼개질 가능성이 커진다.

2. 일부 clip은 실제 저장 프레임이 너무 적었다.

   예:

   | clip | truth | frame_count | issue |
   | --- | --- | ---: | --- |
   | `live_20260601_190326_tapo_1_t001_e210160` | `p4` | 1 | p4 singleton의 핵심 원인 |
   | `live_20260601_190326_tapo_1_t002_e240922` | `p2` | 19 | p2 singleton 원인 중 하나 |
   | `live_20260601_190326_tapo_5_t005_e336838` | `p2` | 1 | 영상 길이/대표성 부족 |

   이 문제는 이후 `25fps` 수정에서 `encoded_duration_seconds = frame_count / writer_fps` 기준으로 gallery 등록을 필터하도록 고쳤다. 앞으로는 frame 1장짜리 clip이 ReID gallery에 들어가지 않아야 한다.

3. `reciprocal top-4`는 안전하지만 보수적이다.

   `reciprocal` 방식은 잘못 섞이는 것을 줄이는 대신, 같은 사람이라도 상호 top-4 관계가 약하면 singleton으로 남긴다. 이번 세션에서 p2/p4 singleton은 실제 같은 사람과의 similarity가 threshold 근처에 있었지만 reciprocal 조건 때문에 떨어졌다.

4. 화면 가장자리/부분 crop에 대한 penalty가 약하다.

   `too_small_reconazing_people_n1`의 crop은 x 좌표가 `0`에 붙은 edge-clipped partial crop이다. 현재 crop quality는 confidence, sharpness, area, center, aspect, full-body ratio를 보지만, bbox가 화면 경계에 잘린 정도를 직접 penalty로 주지는 않는다. 그래서 부분 인물 crop이 정상 인물 그룹에 붙을 위험이 남아 있다.

## Quantitative Check

정답 폴더 기준으로 같은 사람 pair가 같은 group에 들어갔는지를 계산했다.

| embedding source | grouping | threshold | groups | pair precision | pair recall | pair F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| best-only | reciprocal top-4 | 0.65 | 10 | 1.000 | 0.653 | 0.790 |
| top-N mean | reciprocal top-4 | 0.65 | 8 | 1.000 | 0.796 | 0.886 |
| top-N mean | centroid | 0.60 | 5 | 0.960 | 0.990 | 0.975 |

해석:

- `top-N mean`은 기존 방식보다 확실히 덜 쪼개진다.
- `centroid 0.60`은 정답 기준 점수는 가장 좋지만, `too_small` partial crop이 p4 쪽으로 섞이는 사례가 있었다.
- 따라서 운영 기본값은 아직 `reciprocal`을 유지하고, 검토용/디버그용으로 `centroid 0.60` 또는 singleton attach 단계를 추가하는 편이 안전하다.

## Applied Code Change

다음 수정은 반영했다.

- `src/live_session_grouping.py`
  - 세션 종료 regroup이 기본적으로 `top_crop_paths`를 모두 재임베딩한 뒤 평균 embedding을 사용한다.
  - `top_crop_paths`가 없으면 기존처럼 `best_frame_path` 하나로 fallback한다.
  - report metadata에 `embedding_aggregation`을 남긴다.

- `scripts/regroup_live_session.py`
  - `--embedding-aggregation topn|best` 옵션을 추가했다.
  - 기본값은 `topn`이다.

검증 명령:

```bash
python scripts/regroup_live_session.py \
  --session 20260601_190326 \
  --embedding-model osnet_x0_25 \
  --embedding-aggregation topn \
  --method reciprocal \
  --threshold 0.65 \
  --reciprocal-topn 4 \
  --output-subdir similarity_groups_merged_topn_test \
  --write-report docs/reports/LIVE_SESSION_20260601_190326_TOPN_REGROUP_REPORT.md
```

결과:

- Records: `30`
- Groups: `8`
- Sizes: `[9, 8, 5, 3, 2, 1, 1, 1]`
- 기존 best-only 결과 `[9, 6, 5, 2, 2, 2, 1, 1, 1, 1]`보다 p2/p4 분할이 줄었다.

정답 폴더를 보존하기 위해 테스트 출력은 기존 `similarity_groups_merged/`가 아니라 `similarity_groups_merged_topn_test/`에 생성했다.

## Recommended Next Logic Changes

1. crop quality에 edge-clipping penalty 추가

   bbox가 화면 좌/우/상/하 경계에 붙어 있으면 crop이 부분 인물일 가능성이 높다. `edge_score` 또는 `visibility_score`를 추가해서 `_best.jpg` 선택 단계에서 edge-clipped crop이 대표 crop으로 선택되지 않게 해야 한다.

2. singleton attach 후처리 추가

   기본 `reciprocal` 그룹을 만든 뒤 singleton만 대상으로 가장 가까운 group centroid에 붙이는 2단계가 필요하다.

   권장 조건:

   - nearest group centroid score >= `0.60`
   - nearest와 second-nearest 차이 >= `0.05`
   - crop이 edge-clipped가 아님
   - `encoded_duration_seconds >= 1.5`
   - `crop_count_used >= 2`이면 더 신뢰

   이번 세션의 p2 singleton과 p4 singleton은 이 방식으로 회수될 가능성이 높다.

3. debug grouping과 runtime Top-K를 분리 유지

   similarity group은 검토/정리용이다. Top-K 검색은 여전히 전체 gallery embedding 대상으로 수행해야 한다. 그룹이 틀려도 Top-K 후보가 제한되면 안 된다.

4. low-frame clip 차단 유지

   `25fps` 기준으로 실제 저장 길이가 짧은 clip은 gallery/ReID 등록에서 제외해야 한다. 이번 세션의 frame 1장짜리 p4/p2 clip은 분할의 강한 원인이었다.

## Conclusion

이번 세션의 분할은 모델이 완전히 실패한 것이 아니라, `best-only regroup`, `low-frame clip`, `edge-clipped partial crop`, `reciprocal grouping의 보수성`이 함께 만든 문제다.

가장 먼저 반영할 가치가 큰 수정은 이미 적용한 `top-N mean regroup`이다. 다음 단계는 `edge-clipping penalty`와 `singleton attach`를 넣어 p2/p4처럼 같은 사람이 singleton으로 떨어지는 사례를 줄이는 것이다.
