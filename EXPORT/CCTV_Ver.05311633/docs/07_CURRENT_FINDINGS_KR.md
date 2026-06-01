# 07. 현재까지의 주요 발견

## 1. Top-K는 group보다 file-level 평가가 더 중요함

`similarity_groups_merged/`는 디버깅용 폴더입니다. 실제 출력 시스템은 query embedding과 전체 gallery clip embedding을 비교해 Top-K clip을 내보내야 합니다.

그래서 `scripts/export_live_file_topk_rankings.py`를 추가했습니다. 이 스크립트는 merged group을 ranking에 쓰지 않고, 파일 하나를 객체 하나로 보고 Top-K 리스트를 생성합니다.

## 2. `with_reid: true`는 tracker용이고 Top-K OSNet과 다름

- Tracker 내부 ReID: `config/trackers/botsort_reid.yaml`
- Top-K 검색 ReID: `--embedding-model osnet_x0_25`

둘은 서로 다른 단계입니다.

## 3. clip 분절은 아직 완전히 해결되지 않음

post-roll, min-clip, BoT-SORT, `with_reid: true`가 분절을 완화할 수 있지만 완전한 해결책은 아닙니다.

추가 개선 후보:

- 더 긴 post-roll
- tracklet stitching
- 카메라별 continuous raw recording 보관
- 같은 환경에서 `with_reid false/true` A/B 테스트
- full-mp4 anchored embedding

## 4. grouping은 threshold/top-N에 민감함

최근 테스트에서 `reciprocal top-N`이 너무 크면 서로 다른 사람이 한 group으로 over-merge될 수 있었습니다.

## 5. 9대 운영에서는 분석 FPS를 낮춰야 함

9대 720p 기준으로 모든 frame을 분석하지 않고 `--inference-interval 2` 또는 더 큰 간격을 사용합니다. RTSP 수신은 최신 frame만 유지하고 inference worker가 round-robin으로 처리합니다.

