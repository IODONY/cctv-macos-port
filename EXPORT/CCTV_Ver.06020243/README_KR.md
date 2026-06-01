# CCTV Live Top-K Exhibition Runtime Export

이 폴더는 전시장 실전 구동에 필요한 코드와 도구만 분리한 버전입니다.

- Export version: `CCTV_Ver.06020243`
- Source commit: `2cb12d1`
- Runtime goal: 1~9번 Tapo gallery 카메라에서 사람별 full-frame clip을 저장하고, 3층 query 카메라 인물이 등장하면 TouchDesigner로 Top-12 clip path를 전달합니다.
- Top-12 layout: `cam1, cam2, cam3, duplicate1 / cam4, cam5, cam6, duplicate2 / cam7, cam8, cam9, duplicate3`

## 빠른 시작

1. 가상환경을 만듭니다.

Windows:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\run\setup_windows_venv.ps1
```

macOS:
```bash
./run/setup_macos_venv.sh
```

2. 카메라 설정 파일을 만듭니다.

```bash
cp config/cameras/cameras.production.template.csv config/cameras/cameras.local.csv
```

`config/cameras/cameras.local.csv`에서 IP, camera ID, password만 수정합니다. 이 파일은 `.gitignore` 대상이며 공유하지 않습니다.

3. 실행합니다.

```bash
python scripts/run_live_from_camera_csv.py \
  --camera-csv config/cameras/cameras.local.csv \
  --tracker-backend botsort \
  --tracker-reid \
  --inference-interval 2 \
  --recording-fps 25 \
  --record-video-mode full-frame \
  --storage-layout similarity \
  --topk 12 \
  --candidate-pool 60 \
  --topk-selection-mode camera-covered \
  --export-topk-dir snapshots/live_topk_exports
```

TouchDesigner 없이 먼저 확인하려면 `--osc-dry-run`을 추가합니다.

## 문서

- `docs/01_RUNTIME_FLOW_BY_FEATURE_KR.md`: 기능별, 순서별 실전 작동 설명
- `docs/02_CAMERA_CONFIG_KR.md`: 카메라 CSV 수정법
- `docs/03_TOP12_TOUCHDESIGNER_KR.md`: 12슬롯 TouchDesigner 송출 규칙
- `docs/04_SCRIPT_REFERENCE_KR.md`: 스크립트별 기능
- `docs/05_FILE_STRUCTURE_KR.md`: 파일/폴더 구조
- `docs/06_TROUBLESHOOTING_KR.md`: 현장 문제 해결

