# 03. 작업 흐름

## 전체 흐름

```text
RTSP/Webcam frame 수신
  -> YOLO person detection
  -> BoT-SORT 또는 ByteTrack tracker
  -> track별 full-frame mp4 녹화
  -> 사람이 사라지면 post-roll 후 clip 종료
  -> clip에서 ReID용 best crop/top-N crop 선택
  -> OSNet embedding 생성
  -> gallery에 저장
  -> query 인물 embedding과 비교
  -> Top-K clip export
```

## mp4 생성 타이밍

사람 track이 새로 생기면 해당 track에 대해 mp4 recorder가 열립니다. 저장되는 영상은 기본적으로 원본 full-frame입니다.

```bash
--record-video-mode full-frame
```

즉, ReID에는 crop을 쓰지만 mp4 자체는 화면 전체를 저장합니다.

## mp4 종료 타이밍

tracker가 더 이상 사람을 보지 못하면 바로 닫지 않고 post-roll 동안 기다립니다.

```bash
--post-roll-seconds 2
```

기본값은 2초입니다. 사람이 짧게 사라졌다가 돌아오는 경우를 조금 완화합니다.

## 너무 짧은 clip 처리

짧은 track은 mp4는 남기되 ReID gallery에는 넣지 않습니다.

```bash
--min-clip-seconds 1.5
```

이 때문에 mp4 수보다 `_best.jpg` 또는 gallery log 수가 적을 수 있습니다.

## ReID crop 생성 타이밍

ReID crop은 clip 종료 후 생성됩니다. 실행 중 매 frame마다 모든 crop을 embedding하지 않고, clip에서 가장 좋은 best shot/top-N crop을 고른 뒤 OSNet에 넣습니다.

## BoT-SORT `with_reid`와 OSNet Top-K의 차이

- `config/trackers/botsort_reid.yaml`의 `with_reid: true`: tracker 내부에서 track id 유지에 appearance 정보를 쓰는 옵션입니다.
- `--embedding-model osnet_x0_25`: clip 종료 후 Top-K 검색에 쓰는 person-ReID embedding입니다.

둘은 서로 다른 단계입니다. `with_reid: false`여도 Top-K용 OSNet은 켜져 있을 수 있습니다.

## similarity group의 의미

`similarity_groups/`는 live 중 임시로 비슷한 clip을 묶어 보는 폴더입니다.

`similarity_groups_merged/`는 세션 종료 후 전체 clip embedding을 다시 비교해서 만든 최종 확인용 폴더입니다.

중요: Top-K ranking은 group 폴더에 제한되지 않고 전체 gallery clip을 대상으로 수행하는 것이 원칙입니다.

