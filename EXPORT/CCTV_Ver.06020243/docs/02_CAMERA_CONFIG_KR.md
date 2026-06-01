# 카메라 설정 CSV 수정법

## 파일 만들기

```bash
cp config/cameras/cameras.production.template.csv config/cameras/cameras.local.csv
```

`cameras.local.csv`만 현장에 맞게 수정합니다. 이 파일은 비밀번호를 포함하므로 공유하지 않습니다.

## 컬럼 의미

```text
enabled,role,label,source_type,camera_no,ip,username,password,path,source
```

- `enabled`: `1`이면 사용, `0`이면 무시
- `role`: `G`는 gallery, `Q`는 3층 query
- `label`: `tapo_1`~`tapo_9`처럼 고정 앵글 이름
- `source_type`: `rtsp`, `webcam`, `file`
- `camera_no`: 물리 카메라 번호
- `ip`: RTSP 카메라 IP
- `username`: 카메라 ID
- `password`: 카메라 password
- `path`: Tapo stream path. 기본 `/stream1`
- `source`: 직접 source를 지정할 때 사용. webcam은 `webcam:0`

## 9대 Tapo + 3층 query 예시

```csv
enabled,role,label,source_type,camera_no,ip,username,password,path,source
1,G,tapo_1,rtsp,1,192.168.1.101,myid,mypw,/stream1,
1,G,tapo_2,rtsp,2,192.168.1.102,myid,mypw,/stream1,
1,G,tapo_3,rtsp,3,192.168.1.103,myid,mypw,/stream1,
1,G,tapo_4,rtsp,4,192.168.1.104,myid,mypw,/stream1,
1,G,tapo_5,rtsp,5,192.168.1.105,myid,mypw,/stream1,
1,G,tapo_6,rtsp,6,192.168.1.106,myid,mypw,/stream1,
1,G,tapo_7,rtsp,7,192.168.1.107,myid,mypw,/stream1,
1,G,tapo_8,rtsp,8,192.168.1.108,myid,mypw,/stream1,
1,G,tapo_9,rtsp,9,192.168.1.109,myid,mypw,/stream1,
1,Q,query_3f,webcam,0,,,,,webcam:0
```

## 주의

- `label`은 Top-12 coverage 기준이므로 `tapo_1`~`tapo_9`를 유지하는 것이 좋습니다.
- query 카메라는 coverage 대상이 아닙니다.
- RTSP가 열리지 않으면 `/stream1`, `/stream2`를 바꿔 테스트합니다.
- Windows에서 webcam 번호는 장치에 따라 `webcam:0`, `webcam:1`이 달라질 수 있습니다.

