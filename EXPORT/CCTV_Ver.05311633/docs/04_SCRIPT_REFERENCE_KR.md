# 04. 스크립트별 기능

## 실행 스크립트

### `run/run_live_from_camera_csv.py`

전달용 메인 실행 스크립트입니다. `config/cameras/cameras.local.csv`를 읽어 RTSP/Webcam source를 만들고 `src/live_topk_bridge.py`를 실행합니다.

주요 옵션:

```bash
--camera-csv config/cameras/cameras.local.csv
--tracker-backend botsort
--max-runtime-seconds 120
--disable-osc
--show-preview
--preview-reid-crops
```

추가 bridge 옵션은 `--` 뒤에 넣습니다.

```bash
python run/run_live_from_camera_csv.py --max-runtime-seconds 120 -- \
  --tracker-config-path config/trackers/botsort_reid.yaml
```

### `src/live_topk_bridge.py`

live pipeline 본체입니다.

- RTSP/Webcam frame 수신
- YOLO 분석
- tracker state 관리
- track별 mp4 녹화
- best crop 선택
- OSNet embedding 생성
- gallery/query event log 작성
- Top-K export
- similarity grouping

### `src/walnut_core.py`

YOLO pose/detect 모델 호출과 tracker backend 선택을 담당합니다. `botsort`, `bytetrack`, `custom`을 선택할 수 있습니다.

## ReID/Grouping 모듈

### `src/visual_reid.py`

embedding backend를 제공합니다.

- 기본: `osnet_x0_25`
- 비교용: `mobilenet_v3_large`, `mobilenet_v3_small`, `efficientnet_b0`
- fallback: `hsv_histogram`

### `src/visual_grouping.py`

embedding cosine similarity 기반 grouping helper입니다.

### `src/live_session_grouping.py`

세션 종료 후 gallery event log를 다시 읽어 `similarity_groups_merged/`를 만듭니다.

## 분석/평가 스크립트

### `scripts/regroup_live_session.py`

이미 끝난 live session을 다시 grouping합니다.

```bash
python scripts/regroup_live_session.py \
  --session 20260530_233510 \
  --embedding-model osnet_x0_25 \
  --method reciprocal \
  --threshold 0.65 \
  --reciprocal-topn 8
```

### `scripts/sweep_live_similarity_groups.py`

threshold/top-N 조합을 sweep해서 grouping 성능을 비교합니다.

### `scripts/evaluate_live_similarity_truth.py`

사용자가 `p1`, `p2`, `p3`처럼 수동 정답 폴더를 정리했을 때 자동 grouping과 정답을 비교합니다.

### `scripts/export_live_file_topk_rankings.py`

merged group을 쓰지 않고, 파일 하나를 객체 하나로 보고 Top-K ranking CSV/JSON/Markdown을 만듭니다.

```bash
python scripts/export_live_file_topk_rankings.py \
  --session 20260530_225714 \
  --k 7 \
  --embedding-model osnet_x0_25
```

### `scripts/evaluate_topk_retrieval.py`

labeled clip dataset 기반 offline Top-K 평가를 수행합니다.

### `scripts/generate_clip_manifest.py`

`data/labeled_clips/` 구조를 읽어 `data/labels/clips.csv` manifest를 만듭니다.

## 검증 스크립트

### `scripts/agent_validate.sh`

프로젝트 기본 의존성, 모델 파일, 로그/스냅샷 쓰기 가능 여부를 확인합니다.

### `scripts/test_live_topk_units.py`

live Top-K recorder/grouping 단위 테스트입니다.

### `scripts/test_camera_macos.py`

macOS webcam/camera 접근 테스트입니다.

### `scripts/test_video_writer_codecs.py`

OpenCV mp4 writer codec 테스트입니다.

