# 06. 파일 구조

## 최상위 구조

```text
CCTV_Ver.05311633/
  README_KR.md
  requirements.txt
  run/
  src/
  scripts/
  config/
  docs/
  models/
  touchdesigner/
  logs/
  snapshots/
  data/
```

## `run/`

전달받은 사람이 주로 실행하는 파일입니다.

- `run_live_from_camera_csv.py`: CSV 기반 live 실행
- `setup_macos_venv.sh`: macOS 가상환경 설치
- `setup_windows_venv.ps1`: Windows 가상환경 설치

## `src/`

live pipeline의 핵심 코드입니다.

- `live_topk_bridge.py`: live Top-K bridge 본체
- `walnut_core.py`: YOLO/Tracker 분석 코어
- `visual_reid.py`: OSNet/MobileNet/EfficientNet embedding
- `visual_grouping.py`: embedding grouping
- `live_session_grouping.py`: 세션 종료 후 regroup

## `scripts/`

테스트, 평가, 재분석용 CLI입니다.

- `regroup_live_session.py`
- `sweep_live_similarity_groups.py`
- `evaluate_live_similarity_truth.py`
- `export_live_file_topk_rankings.py`
- `evaluate_topk_retrieval.py`
- `generate_clip_manifest.py`
- `agent_validate.sh`

## `config/`

카메라와 tracker 설정입니다.

```text
config/
  cameras/
    cameras.local.template.csv
    cameras.example.csv
  trackers/
    botsort.yaml
    botsort_reid.yaml
    bytetrack.yaml
```

실제 카메라 계정은 `cameras.local.csv`에만 넣고 외부 공유하지 않습니다.

## `models/`

YOLO 모델 파일입니다.

- `yolov8n.pt`
- `yolov8n-pose.pt`

OSNet weight는 첫 실행 시 `logs/model_cache/torchreid/` 아래로 다운로드됩니다.

## `logs/`

실행 로그와 JSONL event가 저장됩니다.

```text
logs/topk_live/<session>/gallery_events.jsonl
logs/topk_live/<session>/query_events.jsonl
logs/topk_live/<session>/merged_similarity_groups.json
```

## `snapshots/`

mp4, best crop, grouping, Top-K export가 저장됩니다.

```text
snapshots/live_topk/<session>/<cam_label>/*.mp4
snapshots/live_topk/<session>/<cam_label>/*_best.jpg
snapshots/live_topk/<session>/similarity_groups_merged/
snapshots/live_topk_exports/<session>/<query_id>/
```

## `docs/reports/`

최근 테스트 리포트 샘플입니다. 새 환경에서는 직접 다시 생성하세요.

