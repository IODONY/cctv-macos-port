# 05. 문제 해결

## RTSP 카메라가 안 열림

- `config/cameras/cameras.local.csv`의 IP, ID, PW, path를 확인합니다.
- `/stream1` 대신 `/stream2`를 시도합니다.
- PC와 카메라가 같은 LAN인지 확인합니다.
- 카메라 앱에서 RTSP/ONVIF 계정이 활성화되어 있는지 확인합니다.
- 한 번에 9대를 열지 말고 1대만 `enabled=1`로 두고 테스트합니다.

## MacBook webcam 권한 문제

macOS 설정에서 Terminal, Codex, Python 또는 사용 중인 IDE에 Camera 권한을 허용해야 합니다.

## mp4는 있는데 `_best.jpg`가 없음

clip이 너무 짧아 ReID gallery 등록이 생략된 경우가 많습니다.

관련 옵션:

```bash
--min-clip-seconds 1.5
```

## 같은 사람이 여러 mp4로 쪼개짐

원인 후보:

- YOLO box가 잠깐 사라짐
- occlusion
- 여러 사람이 교차
- tracker id switch
- inference FPS 부족
- post-roll이 짧음

완화 옵션:

```bash
--post-roll-seconds 2
--tracker-backend botsort
-- --tracker-config-path config/trackers/botsort_reid.yaml
```

`with_reid: true`는 도움이 될 수 있지만 완전한 해결책은 아닙니다. 같은 조건에서 `false`와 `true`를 각각 2분씩 돌려 short clip 수와 track 재생성 횟수를 비교하세요.

## group 폴더가 사람별로 정확히 안 묶임

`similarity_groups_merged/`는 디버깅용입니다. Top-K 검색은 전체 gallery 대상으로 수행합니다.

grouping을 개선하려면:

```bash
python scripts/sweep_live_similarity_groups.py \
  --session <session> \
  --embedding-model osnet_x0_25 \
  --thresholds 0.50,0.55,0.60,0.65,0.70
```

최근 테스트에서는 `reciprocal top-N`이 너무 크면 over-merge가 생길 수 있었습니다.

## Top-K 결과가 약한 사람 그룹

가능한 원인:

- best crop이 흐림
- crop 안에 전신이 충분히 안 보임
- 조명/각도 차이가 큼
- 비슷한 옷의 hard negative가 있음
- clip 수가 부족함

파일 단위 Top-K 리포트를 먼저 확인하세요.

```bash
python scripts/export_live_file_topk_rankings.py --session <session> --k 7
```

## Windows CUDA가 안 잡힘

`python -c "import torch; print(torch.cuda.is_available())"`가 `False`면 PyTorch CUDA wheel이 맞지 않는 것입니다. PyTorch 공식 설치 명령으로 CUDA 버전에 맞게 다시 설치하세요.

