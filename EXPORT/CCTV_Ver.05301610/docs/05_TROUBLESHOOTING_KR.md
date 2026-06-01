# Troubleshooting

## RTSP가 열리지 않을 때

1. 같은 네트워크에 있는지 확인합니다.
2. 카메라 IP를 ping으로 확인합니다.
3. Tapo 앱에서 RTSP/ONVIF 계정이 켜져 있는지 확인합니다.
4. `config/cameras/cameras.local.csv`의 `path`를 `/stream1`, `/stream2`로 바꿔봅니다.
5. ID/PW에 특수문자가 있어도 runner가 URL encoding을 수행합니다.

## CUDA/GPU가 안 잡힐 때

PowerShell에서:

```powershell
.\.venv\Scripts\python.exe - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO_CUDA")
PY
```

`False`라면 NVIDIA driver, PyTorch CUDA wheel, Python 버전을 다시 확인하세요. PyTorch 설치는 [공식 selector](https://pytorch.org/get-started/locally/) 기준으로 맞추는 것이 가장 안전합니다.

## BoT-SORT 실행 중 lap 에러

`requirements.txt`에 `lap>=0.5.12`가 포함되어 있습니다.

```powershell
.\.venv\Scripts\python.exe -m pip install lap>=0.5.12
```

## 같은 사람이 여러 clip/group으로 쪼개질 때

- `--tracker-backend botsort`를 먼저 사용합니다.
- 사람이 자주 겹치지 않는 환경에서 FPS가 부족하면 `--tracker-backend bytetrack`도 비교합니다.
- `--post-roll-seconds 2.0`을 `3.0`으로 올립니다.
- 너무 짧은 fragment가 많으면 `--min-clip-seconds 2.0`으로 올립니다.
- session 종료 후 `scripts/regroup_live_session.py`로 `similarity_groups_merged/`를 확인합니다.

## 처리 속도가 부족할 때

- `--inference-interval 3` 또는 `4`로 올립니다.
- `--frame-width 960 --frame-height 540`로 낮춥니다.
- `--tracker-backend bytetrack`을 시험합니다.
- preview 창을 끕니다.
- RTSP stream path를 저해상도 stream으로 바꿉니다.

