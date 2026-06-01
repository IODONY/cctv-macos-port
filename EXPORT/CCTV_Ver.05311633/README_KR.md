# CCTV Live Top-K ReID 전달 패키지

이 폴더는 Tapo RTSP 카메라와 Mac/Windows 환경에서 YOLO + BoT-SORT + OSNet ReID 기반으로 사람 clip을 저장하고, query 인물과 유사한 clip을 Top-K로 찾기 위한 전달용 패키지입니다.

## 현재 목표

1. Gallery 카메라에서 사람이 보이면 원본 full-frame mp4 녹화를 시작합니다.
2. 사람이 사라지면 post-roll 후 clip을 종료합니다.
3. 종료된 clip에서 ReID용 best crop과 top-N crop을 선택합니다.
4. OSNet x0.25 person-ReID embedding을 생성해 gallery에 저장합니다.
5. query 카메라 입력이 들어오면 gallery embedding과 비교해 Top 5-12 clip을 export합니다.
6. TouchDesigner 연동 전에는 export 폴더에 Top-K clip을 저장하는 방식으로 테스트합니다.

## 가장 먼저 볼 문서

- `docs/01_QUICK_START_KR.md`: 설치와 첫 실행
- `docs/02_CAMERA_CONFIG_KR.md`: 카메라 IP, ID, PW 수정법
- `docs/03_RUNTIME_FLOW_KR.md`: mp4 생성, crop, ReID, Top-K 흐름
- `docs/04_SCRIPT_REFERENCE_KR.md`: 스크립트별 기능
- `docs/05_TROUBLESHOOTING_KR.md`: 자주 생기는 문제
- `docs/06_FILE_STRUCTURE_KR.md`: 폴더 구조와 산출물 의미

## 중요한 원칙

- `config/cameras/cameras.local.csv`에는 실제 카메라 ID/PW가 들어갈 수 있으므로 외부 공유 금지입니다.
- 이 패키지에는 실제 ID/PW가 들어 있지 않습니다. `cameras.local.template.csv`를 복사해 local CSV를 만들어 사용하세요.
- 녹화 영상과 crop 결과는 `snapshots/` 아래에 저장됩니다.
- 실행 로그는 `logs/` 아래에 저장됩니다.
- `with_reid: true`는 BoT-SORT 내부 추적용 ReID입니다. Top-K 검색용 OSNet ReID와는 별도입니다.

## 빠른 실행 예시

```bash
# macOS
cd CCTV_Ver.05311633
bash run/setup_macos_venv.sh
cp config/cameras/cameras.local.template.csv config/cameras/cameras.local.csv
# cameras.local.csv 수정 후:
source .venv/bin/activate
python run/run_live_from_camera_csv.py --max-runtime-seconds 120 --disable-osc
```

```powershell
# Windows PowerShell
cd CCTV_Ver.05311633
.\run\setup_windows_venv.ps1
Copy-Item config\cameras\cameras.local.template.csv config\cameras\cameras.local.csv
# cameras.local.csv 수정 후:
.\.venv\Scripts\python.exe run\run_live_from_camera_csv.py --max-runtime-seconds 120 --disable-osc
```

