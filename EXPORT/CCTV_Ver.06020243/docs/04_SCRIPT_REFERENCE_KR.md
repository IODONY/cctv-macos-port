# 스크립트별 기능

## run/run_live_from_camera_csv.py

현장 운영자가 실행하기 쉬운 wrapper입니다.

CSV를 읽고 `src/live_topk_bridge.py`에 필요한 인자를 만들어 넘깁니다.

권장 실행:

```bash
python run/run_live_from_camera_csv.py --camera-csv config/cameras/cameras.local.csv
```

## scripts/run_live_from_camera_csv.py

동일한 wrapper입니다. 개발/검증용 경로에서 실행할 때 사용합니다.

## src/live_topk_bridge.py

실전 runtime 핵심입니다.

담당 기능:

- RTSP/webcam 수신
- YOLO person detection
- BoT-SORT/ByteTrack/custom tracking
- 사람별 full-frame mp4 녹화
- tracklet stitching
- duplicate track absorb
- ReID crop 선택
- OSNet embedding 생성
- gallery 등록
- query 처리
- camera-covered Top-12 ranking
- TouchDesigner OSC 송출
- Top-K 결과 폴더 export

## src/visual_reid.py

ReID crop과 embedding 담당입니다.

- best/top-N crop selection
- diverse-quality crop 선택
- OSNet x0.25 embedder
- MobileNet/EfficientNet fallback embedder
- prototype similarity

## src/walnut_core.py

YOLO 분석과 tracker backend 처리의 공통 로직입니다.

## src/live_session_grouping.py

세션 종료 후 similarity grouping을 다시 만드는 디버깅 도구입니다.
실전 Top-K 후보를 제한하지는 않습니다.

## touchdesigner/touchdesigner_topk_callbacks.py

TouchDesigner OSC In DAT callback입니다.

Top-K payload를 받아 `movie_clip_1`~`movie_clip_12`에 rank별 mp4 path를 넣습니다.

## scripts/test_live_topk_units.py

카메라 없이 핵심 helper를 검증하는 unit test입니다.

## scripts/agent_validate.sh

환경과 dependency, smoke test를 확인합니다.

## scripts/test_camera_macos.py

macOS 카메라 권한/장치 확인용입니다.

## scripts/test_osc_loopback.py

OSC 송수신 테스트용입니다.

## scripts/regroup_live_session.py

이미 끝난 live session의 gallery clip을 다시 ReID grouping합니다.

## scripts/sweep_live_similarity_groups.py

similarity threshold별 grouping 결과를 비교합니다.

