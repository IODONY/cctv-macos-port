# 카메라 ID/PW 분리 관리 방식

원본 프로젝트에서도 카메라 ID/PW는 코드나 shell command에 직접 쓰지 않고 CSV로 분리합니다.

## 파일 위치

- 템플릿: `config/cameras/cameras.example.csv`
- 9대 템플릿: `config/cameras/cameras_9cam_template.csv`
- 실제 로컬 설정: `config/cameras/cameras.local.csv`
- 실행 래퍼: `scripts/run_live_from_camera_csv.py`

`cameras.local.csv`는 `.gitignore`에 포함되어 있으므로 Git에 올라가지 않습니다.

## 처음 설정

```bash
cp config/cameras/cameras.example.csv config/cameras/cameras.local.csv
```

그 다음 `config/cameras/cameras.local.csv`에서 아래 값만 수정합니다.

- `enabled`: 사용할 카메라는 `1`, 끌 카메라는 `0`
- `role`: gallery 카메라는 `G`, query 카메라는 `Q`
- `label`: 저장 폴더와 로그에 쓰일 이름
- `ip`: 카메라 IP
- `username`: RTSP 카메라 ID
- `password`: RTSP 카메라 PW
- `path`: 필요할 때 `/stream1`, `/stream2`

## 실행

```bash
source .venv/bin/activate
python scripts/run_live_from_camera_csv.py \
  --camera-csv config/cameras/cameras.local.csv \
  --tracker-backend botsort \
  --inference-interval 2 \
  --topk 7 \
  --disable-osc
```

미리보기까지 보고 싶으면:

```bash
python scripts/run_live_from_camera_csv.py \
  --camera-csv config/cameras/cameras.local.csv \
  --show-preview \
  --preview-reid-crops \
  --disable-osc
```

## CSV 예시

```csv
enabled,role,label,source_type,camera_no,ip,username,password,path,source
1,G,tapo_1,rtsp,1,192.168.5.59,my_id,my_pw,,
1,G,tapo_2,rtsp,2,192.168.5.57,my_id,my_pw,,
1,G,tapo_3,rtsp,3,192.168.5.64,my_id,my_pw,,
1,Q,query_webcam,webcam,0,,,,,webcam:0
```

실행 래퍼는 CSV를 읽어 RTSP URL을 만들고, 비밀번호가 command history에 남지 않도록 환경변수로 `live_topk_bridge.py`에 전달합니다.
