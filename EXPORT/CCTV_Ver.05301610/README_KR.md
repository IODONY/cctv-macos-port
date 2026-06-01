# Live YOLO-ReID Top-K Export Package

이 폴더는 다른 컴퓨터로 복사해서 Tapo RTSP 카메라와 웹캠 query를 실행하기 위한 운영 패키지입니다.

## 핵심 실행 흐름

1. Tapo 카메라들은 gallery 역할로 RTSP 영상을 보냅니다.
2. query 카메라는 MacBook/Windows 내장 웹캠 또는 USB 카메라입니다.
3. 카메라 수신 thread는 각 카메라의 최신 full-frame만 유지합니다.
4. inference coordinator가 카메라를 round-robin으로 돌며 기본 `2프레임당 1번` YOLO+BoT-SORT 분석을 실행합니다.
5. 사람이 등장하면 원본 full-frame mp4 녹화를 시작합니다.
6. 사람이 사라져도 기본 2초 post-roll 후 clip을 종료합니다.
7. 종료된 clip에서 top-N ReID crop을 뽑아 OSNet embedding으로 gallery에 저장합니다.
8. query 카메라에 사람이 들어오면 gallery 전체와 비교해 Top-K clip을 `snapshots/live_topk_exports/`에 저장합니다.

## 폴더 구조

- `src/`: live pipeline과 ReID/YOLO 핵심 코드
- `scripts/`: 검증, 평가, regroup, 진단 스크립트
- `touchdesigner/`: TouchDesigner OSC callback 참고 코드
- `config/trackers/`: BoT-SORT/ByteTrack 설정
- `models/`: YOLO nano / pose 모델 파일
- `config/cameras/`: 카메라 설정 CSV 템플릿
- `run/`: 가상환경 설치와 CSV 기반 실행 래퍼
- `logs/`, `snapshots/`: 실행 중 생성되는 로그와 영상

## 가장 짧은 실행 순서

Windows:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run\setup_windows_venv.ps1
Copy-Item .\config\cameras\cameras.example.csv .\config\cameras\cameras.local.csv
notepad .\config\cameras\cameras.local.csv
.\.venv\Scripts\python.exe .\run\run_live_from_camera_csv.py --camera-csv config\cameras\cameras.local.csv --disable-osc
```

macOS:

```bash
bash run/setup_macos_venv.sh
cp config/cameras/cameras.example.csv config/cameras/cameras.local.csv
open -e config/cameras/cameras.local.csv
source .venv/bin/activate
python run/run_live_from_camera_csv.py --camera-csv config/cameras/cameras.local.csv --disable-osc
```

실제 카메라 ID/PW는 `config/cameras/cameras.local.csv`에만 입력하세요. 이 파일은 `.gitignore`에 포함되어 있습니다.

