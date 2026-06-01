# 기능별 / 로직 순서별 실전 작동 설명

## 1. 카메라 설정 로딩

실행 시작점은 `scripts/run_live_from_camera_csv.py`입니다.

이 스크립트는 `config/cameras/cameras.local.csv`를 읽어서 각 카메라의 역할과 주소를 정합니다.

- `role=G`: gallery 카메라입니다. 1~9층/앵글 카메라처럼 clip을 수집합니다.
- `role=Q`: query 카메라입니다. 3층 도착 관객을 감지하고 gallery에서 Top-12를 호출합니다.
- `label=tapo_1`~`tapo_9`: TouchDesigner 12슬롯 coverage 기준입니다.
- `source_type=rtsp`: Tapo RTSP 카메라입니다.
- `source_type=webcam`: 내장/USB 카메라입니다.

CSV의 username/password는 실행 시 환경 변수로만 bridge에 전달됩니다. 코드 안에 계정 정보를 넣지 않습니다.

## 2. 카메라 수신

`src/live_topk_bridge.py`가 카메라별 capture worker를 실행합니다.

각 카메라 worker는 최신 frame을 계속 갱신합니다. 모든 frame을 큐에 쌓아 오래된 frame까지 분석하지 않고, 지연이 생기면 최신 frame 중심으로 따라갑니다.

실전 권장값:

- `--frame-width 1280`
- `--frame-height 720`
- `--recording-fps 25`
- `--inference-interval 2`

`--inference-interval 2`는 2프레임마다 한 번 YOLO/Tracker 분석을 수행한다는 뜻입니다.

## 3. YOLO 사람 검출

YOLO는 화면 속 person bbox를 찾습니다.

역할:

- 사람이 들어왔는지 감지
- 사람 bbox 생성
- ReID crop 후보 생성
- tracker에 넘길 detection 제공

YOLO는 사람 검출 담당이고, 최종 "같은 사람인지" 판단은 OSNet ReID embedding이 담당합니다.

## 4. BoT-SORT 추적

BoT-SORT는 YOLO bbox를 시간축으로 이어 `track_id`를 만듭니다.

실전 기본값:

- `--tracker-backend botsort`
- `--tracker-reid` 사용 권장
- tracker config: `config/trackers/botsort_reid.yaml`

Track 의미:

- 새 track 등장: 새 사람 clip 녹화 후보
- track 유지: 같은 recorder에 full-frame 영상 계속 기록
- track 사라짐: 바로 종료하지 않고 post-roll 대기

## 5. 사람별 full-frame 녹화

사람 track이 시작되면 `PersonClipRecorder`가 만들어집니다.

중요한 점:

- 저장되는 mp4는 crop이 아니라 원본 full-frame 영상입니다.
- ReID용 이미지만 사람 bbox crop으로 저장됩니다.
- 한 화면에 두 사람이 있으면 사람별 recorder가 따로 생길 수 있습니다.

기본 종료 조건:

- 사람이 사라지고 `--post-roll-seconds`가 지난 뒤 clip 종료
- 너무 짧은 clip은 gallery에 등록하지 않고 `_discarded`로 이동
- best crop 품질이 낮은 clip도 `_discarded`로 이동

## 6. Tracklet stitching

현장에서는 같은 사람이 계속 보이는데 tracker id가 순간적으로 바뀔 수 있습니다.

Tracklet stitching은 사라진 track과 새 track이 같은 사람으로 보일 때 기존 recorder에 이어붙입니다.

판단 기준:

- 같은 카메라 안에서만 비교
- 시간 gap
- bbox 중심 이동 거리
- OSNet ReID similarity
- 최근 다중 인물/겹침 여부

애매하면 붙이지 않습니다. 다른 사람끼리 합쳐지는 것이 더 큰 문제이기 때문입니다.

## 7. Duplicate track absorb

Stitching은 "사라졌다가 다시 생긴 track"을 처리합니다.

Duplicate absorb는 "기존 recorder가 아직 살아 있는데 같은 사람이 새 track으로 동시에 잡히는 경우"를 처리합니다.

예:

- 한 사람이 화면에 계속 있음
- YOLO/BoT-SORT가 순간적으로 같은 사람을 `track 4`, `track 6` 두 개로 봄
- 새 mp4를 만들기 전에 기존 recorder와 비교
- 같은 사람으로 확실하면 `track 6`을 recorder 4가 흡수

로그 필드:

- `absorbed_track_ids`
- `track_ownership_events`
- `stitched_track_ids`
- `close_reason`

## 8. Clip 종료 후 ReID crop 선택

Clip이 종료되면 recorder는 저장 중 모아둔 crop 후보에서 best/top-N crop을 고릅니다.

현재 방식은 `diverse-quality`입니다.

고려 요소:

- crop 품질
- bbox confidence
- 선명도
- 사람 bbox 크기
- 초반/중반/후반 시간 다양성
- front/side/back-like appearance 다양성
- 비슷한 crop 중복 제거

결과 파일:

- `*_best.jpg`
- `*_best_crop_002.jpg`
- `*_best_crop_003.jpg`
- 최대 `--live-visual-top-n`개

## 9. OSNet ReID embedding

ReID backend는 기본 `osnet_x0_25`입니다.

Crop은 OSNet 입력 크기 `256x128`로 변환되고, feature vector로 바뀐 뒤 cosine similarity 비교에 사용됩니다.

이 시스템은 얼굴 인식이 아니라 전신 appearance 기반입니다.

비교에 쓰이는 정보:

- 옷 색
- 실루엣
- 가방/외형적 appearance
- 앞/뒤/옆 crop prototype

## 10. Gallery 등록

Clip이 유효하면 gallery에 등록됩니다.

Gallery record에는 다음이 포함됩니다.

- full-frame mp4 경로
- best/top-N crop 경로
- camera label
- track id / stitched id / absorbed id
- OSNet embedding
- prototype embeddings
- crop quality
- clip duration
- close reason

Query 카메라가 등장하기 전까지 gallery는 계속 누적됩니다.

## 11. 3층 Query 처리

Query 카메라에서 사람이 보이면 다음 순서가 실행됩니다.

1. query 인물 bbox 선택
2. query crop 생성
3. OSNet embedding 생성
4. gallery 전체 clip과 similarity score 계산
5. Top-12 selection 실행
6. TouchDesigner OSC payload 송출
7. 동시에 `snapshots/live_topk_exports/`에 결과 폴더 저장

## 12. Camera-covered Top-12 선택

기본 모드는 `camera-covered`입니다.

목표:

- 1~9번 camera angle이 최소 하나씩 등장
- 남는 3개는 유사도 높은 중복 장면
- 특정 카메라 clip이 아직 없으면 가능한 후보 중 유사도 최고 clip으로 fallback

슬롯:

- rank 1: `tapo_1`
- rank 2: `tapo_2`
- rank 3: `tapo_3`
- rank 4: 남은 후보 중 유사도 1등 중복 장면
- rank 5: `tapo_4`
- rank 6: `tapo_5`
- rank 7: `tapo_6`
- rank 8: 남은 후보 중 유사도 2등 중복 장면
- rank 9: `tapo_7`
- rank 10: `tapo_8`
- rank 11: `tapo_9`
- rank 12: 남은 후보 중 유사도 3등 중복 장면

결과 metadata:

- `topk_selection_mode`
- `coverage_cam_labels`
- `missing_cam_labels`
- `coverage_slot_map`
- result별 `slot_type`
- result별 `coverage_fallback`
- result별 `intended_cam_label`
- result별 `actual_cam_label`

## 13. TouchDesigner 송출

OSC 주소:

- `/walnut/topk/cam/<query_cam>/results`
- `/walnut/topk/cam/<query_cam>/result/<rank>/path`
- `/walnut/topk/cam/<query_cam>/result/<rank>/score`
- `/walnut/topk/cam/<query_cam>/result/<rank>/cam_label`
- `/walnut/topk/cam/<query_cam>/result/<rank>/slot_type`

TouchDesigner callback은 `movie_clip_1`~`movie_clip_12`에 rank별 path를 넣습니다.

## 14. Export 결과 폴더

`--export-topk-dir snapshots/live_topk_exports`를 켜면 query마다 결과 폴더가 생깁니다.

구조:

```text
snapshots/live_topk_exports/<session>/<query_id>/
  query_best.jpg
  results.json
  rank_01/
    clip.mp4 또는 clip_path.txt
    best.jpg 또는 best_path.txt
    score.json
  ...
  rank_12/
```

TouchDesigner 연결 없이도 이 폴더를 보면 어떤 영상이 호출될지 확인할 수 있습니다.

