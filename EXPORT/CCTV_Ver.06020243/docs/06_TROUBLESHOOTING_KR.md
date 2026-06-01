# 현장 문제 해결

## RTSP가 열리지 않을 때

1. IP가 맞는지 확인합니다.
2. 같은 네트워크에 있는지 확인합니다.
3. `path`를 `/stream1`, `/stream2`로 바꿔봅니다.
4. username/password가 맞는지 확인합니다.
5. 한 대만 켜서 테스트합니다.

```bash
python scripts/run_live_from_camera_csv.py \
  --camera-csv config/cameras/cameras.local.csv \
  --max-runtime-seconds 60 \
  --osc-dry-run
```

## MacBook/webcam 권한 문제

macOS:

- System Settings
- Privacy & Security
- Camera
- Terminal, Python, Codex, 또는 사용 중인 앱에 camera 권한 허용

권한 확인:

```bash
python scripts/test_camera_macos.py --source webcam:0
```

## mp4가 너무 짧게 쪼개질 때

확인할 항목:

- `--post-roll-seconds 2`
- `--max-clip-seconds 0` 또는 충분히 큰 값
- `--tracker-reid`
- `stitch_events.jsonl`의 reject reason
- `_discarded`에 들어간 이유

현재 runtime에는 tracklet stitching과 duplicate track absorb가 기본으로 포함되어 있습니다.

## Top-12에 특정 카메라가 비어 보일 때

`query_events.jsonl` 또는 export의 `results.json`에서 확인합니다.

- `missing_cam_labels`
- `coverage_slot_map`
- `coverage_fallback`
- `intended_cam_label`
- `actual_cam_label`

특정 카메라에 아직 gallery clip이 없으면 그 슬롯은 유사도 높은 다른 clip으로 채워집니다.

## TouchDesigner에 영상이 안 들어올 때

1. OSC host/port 확인
2. TouchDesigner OSC In DAT port 확인
3. `--osc-dry-run`으로 payload가 만들어지는지 확인
4. Movie File In TOP 이름이 `movie_clip_1`~`movie_clip_12`인지 확인
5. clip path가 해당 컴퓨터에서 접근 가능한 절대 경로인지 확인

## 성능이 부족할 때

권장 순서:

1. `--inference-interval`을 2에서 3으로 올립니다.
2. preview를 끕니다.
3. tracker를 `botsort`에서 `bytetrack`으로 비교합니다.
4. RTSP를 720p stream으로 고정합니다.
5. Windows CUDA PyTorch가 제대로 설치되었는지 확인합니다.

