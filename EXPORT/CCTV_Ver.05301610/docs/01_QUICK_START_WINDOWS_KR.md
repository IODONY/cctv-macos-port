# Windows 빠른 시작

권장 환경: Windows 11, Python 3.11, NVIDIA Driver 최신 버전, RTX 4070 Ti급 GPU.

## 1. 폴더 복사

`EXPORT/` 폴더 전체를 새 컴퓨터의 원하는 위치로 복사합니다. 예:

```powershell
C:\CCTV_Project_EXPORT
```

## 2. 가상환경 설치

PowerShell을 열고:

```powershell
cd C:\CCTV_Project_EXPORT
Set-ExecutionPolicy -Scope Process Bypass
.\run\setup_windows_venv.ps1
```

설치 스크립트는 다음을 수행합니다.

- `.venv` 생성
- PyTorch CUDA wheel 설치
- `requirements.txt` 설치
- Python 문법 검사
- live unit test 실행

PyTorch CUDA 설치가 실패하면 [PyTorch 공식 설치 선택기](https://pytorch.org/get-started/locally/)에서 현재 PC에 맞는 명령을 확인하세요.

## 3. 카메라 CSV 만들기

```powershell
Copy-Item .\config\cameras\cameras.example.csv .\config\cameras\cameras.local.csv
notepad .\config\cameras\cameras.local.csv
```

수정할 것은 보통 이 5개뿐입니다.

- `enabled`: 사용할 카메라면 `1`
- `role`: gallery는 `G`, query는 `Q`
- `label`: `tapo_1`, `tapo_2`, `query_webcam`처럼 사람이 알아볼 이름
- `ip`: Tapo 카메라 IP
- `username`, `password`: Tapo RTSP ID/PW

## 4. 실행

```powershell
.\.venv\Scripts\python.exe .\run\run_live_from_camera_csv.py `
  --camera-csv config\cameras\cameras.local.csv `
  --tracker-backend botsort `
  --inference-interval 2 `
  --topk 7 `
  --disable-osc
```

preview 화면까지 보고 싶다면:

```powershell
.\.venv\Scripts\python.exe .\run\run_live_from_camera_csv.py `
  --camera-csv config\cameras\cameras.local.csv `
  --show-preview `
  --preview-reid-crops `
  --disable-osc
```

## 5. 결과 위치

- 원본 full-frame mp4: `snapshots/live_topk/<session>/<cam_label>/`
- ReID best crop: 같은 폴더의 `*_best.jpg`
- Top-K export: `snapshots/live_topk_exports/<session>/<query_id>/`
- gallery log: `logs/topk_live/<session>/gallery_events.jsonl`
- query log: `logs/topk_live/<session>/query_events.jsonl`

