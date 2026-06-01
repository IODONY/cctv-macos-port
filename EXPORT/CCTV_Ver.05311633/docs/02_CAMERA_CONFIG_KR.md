# 02. 카메라 설정

카메라 설정은 `config/cameras/cameras.local.csv`에서만 수정합니다. 이 파일은 실제 ID/PW를 담을 수 있으므로 외부 공유하지 않습니다.

## CSV 컬럼 의미

| 컬럼 | 의미 |
| --- | --- |
| `enabled` | `1`이면 사용, `0`이면 비활성 |
| `role` | `G`는 gallery, `Q`는 query |
| `label` | 저장 폴더와 로그에 쓰는 사람이 읽는 이름 |
| `source_type` | `rtsp`, `webcam`, `file` 중 하나 |
| `camera_no` | 물리 카메라 번호 또는 webcam index |
| `ip` | RTSP 카메라 IP |
| `username` | 카메라 ID |
| `password` | 카메라 PW |
| `path` | Tapo RTSP path. 보통 `/stream1` 또는 `/stream2` |
| `source` | 직접 source를 쓰고 싶을 때 사용. 있으면 다른 RTSP 조합보다 우선 |

## RTSP URL 생성 방식

CSV가 다음과 같으면:

```csv
enabled,role,label,source_type,camera_no,ip,username,password,path,source
1,G,tapo_1,rtsp,1,192.168.5.59,myid,mypw,/stream1,
```

실행 스크립트는 내부적으로 다음 source를 만듭니다.

```text
rtsp://myid:mypw@192.168.5.59/stream1
```

터미널 출력에서는 PW가 `***`로 가려집니다.

## 3대 테스트 예시

```csv
enabled,role,label,source_type,camera_no,ip,username,password,path,source
1,G,tapo_1,rtsp,1,192.168.5.59,CHANGE_CAMERA_ID,CHANGE_CAMERA_PASSWORD,/stream1,
1,G,tapo_2,rtsp,2,192.168.5.57,CHANGE_CAMERA_ID,CHANGE_CAMERA_PASSWORD,/stream1,
1,G,tapo_3,rtsp,3,192.168.5.64,CHANGE_CAMERA_ID,CHANGE_CAMERA_PASSWORD,/stream1,
0,Q,query_webcam,webcam,0,,,,,webcam:0
```

## 9대 gallery + webcam query 구조

9대 전체 운영에서는 `tapo_1`부터 `tapo_9`까지 `enabled=1`, `role=G`로 두고, MacBook/노트북 내장 카메라는 `role=Q`로 둡니다.

```csv
1,Q,query_webcam,webcam,0,,,,,webcam:0
```

## RTSP가 열리지 않을 때

1. 같은 LAN인지 확인합니다.
2. 카메라 앱에서 RTSP/ONVIF 계정이 활성화되어 있는지 확인합니다.
3. `/stream1`이 안 되면 `/stream2`를 시도합니다.
4. 방화벽 또는 공유기 isolation 기능을 확인합니다.
5. 한 대씩 먼저 테스트합니다.

