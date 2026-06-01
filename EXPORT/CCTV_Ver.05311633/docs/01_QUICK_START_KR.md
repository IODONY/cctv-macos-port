# 01. 빠른 시작

## 1. 준비물

- Python 3.11 권장
- Tapo 카메라 RTSP 접속 가능 상태
- 카메라와 실행 PC가 같은 LAN에 있거나 RTSP 접속이 가능한 네트워크
- macOS는 MPS, Windows는 NVIDIA CUDA 사용 권장
- Windows 9대 운영 목표 장비: i7-13700K, RTX 4070 Ti, RAM 64GB 이상급

## 2. 가상환경 설치

macOS:

```bash
cd CCTV_Ver.05311633
bash run/setup_macos_venv.sh
```

Windows PowerShell:

```powershell
cd CCTV_Ver.05311633
.\run\setup_windows_venv.ps1
```

Windows에서 PyTorch CUDA 설치가 실패하면 PyTorch 공식 selector에서 CUDA 버전에 맞는 명령을 먼저 실행한 뒤 `pip install -r requirements.txt`를 다시 실행하세요.

## 3. 카메라 설정 파일 만들기

```bash
cp config/cameras/cameras.local.template.csv config/cameras/cameras.local.csv
```

Windows:

```powershell
Copy-Item config\cameras\cameras.local.template.csv config\cameras\cameras.local.csv
```

그 다음 `config/cameras/cameras.local.csv`의 `ip`, `username`, `password`, `path`, `enabled`를 수정합니다.

## 4. 2분 smoke test

```bash
source .venv/bin/activate
python run/run_live_from_camera_csv.py \
  --max-runtime-seconds 120 \
  --disable-osc
```

Windows:

```powershell
.\.venv\Scripts\python.exe run\run_live_from_camera_csv.py `
  --max-runtime-seconds 120 `
  --disable-osc
```

## 5. BoT-SORT 내부 ReID 켜서 테스트

`with_reid: true` 테스트는 다음처럼 실행합니다.

```bash
python run/run_live_from_camera_csv.py \
  --max-runtime-seconds 120 \
  --disable-osc \
  -- --tracker-config-path config/trackers/botsort_reid.yaml
```

## 6. 결과 확인

- mp4: `snapshots/live_topk/<session>/<cam_label>/`
- best crop: mp4와 같은 폴더의 `*_best.jpg`
- gallery log: `logs/topk_live/<session>/gallery_events.jsonl`
- merged grouping: `snapshots/live_topk/<session>/similarity_groups_merged/`
- Top-K export: `snapshots/live_topk_exports/<session>/`

