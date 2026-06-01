# 파일 구조

```text
CCTV_Ver.06020243/
  README_KR.md
  requirements.txt
  config/
    cameras/
      cameras.production.template.csv
      cameras.example.csv
    trackers/
      botsort.yaml
      botsort_reid.yaml
      bytetrack.yaml
  docs/
  run/
    run_live_from_camera_csv.py
    setup_windows_venv.ps1
    setup_macos_venv.sh
  scripts/
  src/
  touchdesigner/
  models/
    yolov8n.pt
    yolov8n-pose.pt
  logs/
  snapshots/
  data/
```

## 실행 중 생성되는 폴더

```text
logs/topk_live/<session>/
  gallery_events.jsonl
  query_events.jsonl
  stitch_events.jsonl
  merged_similarity_groups.json

snapshots/live_topk/<session>/
  tapo_1/
  tapo_2/
  ...
  query_3f/
  similarity_groups/
  similarity_groups_merged/
  _discarded/

snapshots/live_topk_exports/<session>/<query_id>/
  query_best.jpg
  results.json
  rank_01/
  ...
  rank_12/
```

## 중요한 파일 의미

- `*.mp4`: 원본 full-frame clip
- `*_best.jpg`: ReID 대표 crop
- `*_best_crop_002.jpg`: 추가 prototype crop
- `results.json`: query별 Top-12 결과
- `gallery_events.jsonl`: gallery에 등록된 clip 로그
- `query_events.jsonl`: query 발생과 Top-K 결과 로그
- `stitch_events.jsonl`: track stitching/absorb 판단 로그

## 공유하지 말아야 할 파일

- `.venv/`
- `config/cameras/cameras.local.csv`
- `logs/`
- `snapshots/`
- 실제 촬영 mp4/jpg
- 카메라 계정/비밀번호가 들어간 문서

