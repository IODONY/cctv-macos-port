# 카메라 설정 분리 방식

카메라 수, IP, ID, PW는 코드에서 바꾸지 않습니다. `config/cameras/cameras.local.csv`만 수정합니다.

## CSV 컬럼

```text
enabled,role,label,source_type,camera_no,ip,username,password,path,source
```

- `enabled`: `1`이면 사용, `0`이면 무시
- `role`: `G`는 gallery, `Q`는 query
- `label`: 저장 폴더와 로그에 쓰이는 이름
- `source_type`: `rtsp`, `webcam`, `file`
- `camera_no`: 물리 카메라 번호 또는 웹캠 번호
- `ip`: RTSP 카메라 IP
- `username`: 카메라 RTSP ID
- `password`: 카메라 RTSP PW
- `path`: Tapo 모델에 따라 `/stream1`, `/stream2`가 필요할 때 입력
- `source`: 직접 source를 쓰고 싶을 때 사용. 예: `webcam:0`, `sample.mp4`

## 3대 Tapo + 웹캠 예시

```csv
enabled,role,label,source_type,camera_no,ip,username,password,path,source
1,G,tapo_1,rtsp,1,192.168.5.59,my_id,my_pw,,
1,G,tapo_2,rtsp,2,192.168.5.57,my_id,my_pw,,
1,G,tapo_3,rtsp,3,192.168.5.64,my_id,my_pw,,
1,Q,query_webcam,webcam,0,,,,,webcam:0
```

## 9대 Tapo + 웹캠 예시

`config/cameras/cameras_9cam_template.csv`를 복사해서 사용합니다.

```powershell
Copy-Item .\config\cameras\cameras_9cam_template.csv .\config\cameras\cameras.local.csv
```

## RTSP path 문제

기본 URL은 다음 형태입니다.

```text
rtsp://ID:PW@IP
```

카메라 모델/설정에 따라 안 열리면 `path` 컬럼에 아래를 차례로 시험합니다.

```text
/stream1
/stream2
/live
```

실제 비밀번호가 들어간 `cameras.local.csv`는 공유하거나 Git에 올리지 마세요.

