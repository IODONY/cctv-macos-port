# 스크립트별 기능 정리

## Live 운영

- `run/run_live_from_camera_csv.py`
  - 카메라 CSV를 읽어 `src/live_topk_bridge.py`를 실행합니다.
  - 카메라 수/IP/ID/PW 변경은 이 CSV만 수정하면 됩니다.
  - RTSP URL은 환경변수로 넘겨서 터미널 명령줄에 비밀번호가 직접 노출되지 않게 합니다.

- `src/live_topk_bridge.py`
  - 메인 live runtime입니다.
  - RTSP/webcam/file 입력을 받고, full-frame clip 녹화, ReID embedding, Top-K export/OSC를 처리합니다.
  - 주요 옵션: `--tracker-backend`, `--inference-interval`, `--post-roll-seconds`, `--live-visual-top-n`, `--topk`.

- `src/walnut_core.py`
  - YOLO pose/person detection과 tracker backend를 담당합니다.
  - `custom`, `botsort`, `bytetrack`을 지원합니다.

- `src/visual_reid.py`
  - best-shot crop, crop quality, OSNet/MobileNet embedding을 담당합니다.
  - 기본 ReID 모델은 `osnet_x0_25`입니다.

## 그룹 정리와 디버깅

- `scripts/regroup_live_session.py`
  - 이미 저장된 live session의 `_best.jpg`를 다시 임베딩해 `similarity_groups_merged/`를 생성합니다.

- `scripts/sweep_live_similarity_groups.py`
  - threshold별 grouping 결과를 비교합니다.
  - 같은 사람이 여러 group으로 갈라지는지 확인할 때 사용합니다.

- `src/live_session_grouping.py`, `src/visual_grouping.py`
  - session-end similarity regrouping 공통 로직입니다.

## Offline 평가

- `scripts/generate_clip_manifest.py`
  - labeled clip 폴더를 읽어 `data/labels/clips.csv`를 만듭니다.

- `scripts/evaluate_topk_retrieval.py`
  - labeled dataset으로 Top-K retrieval 성능을 평가합니다.
  - backend `profile`, `visual`, `hybrid`를 지원합니다.

- `scripts/evaluate_labeled_clips.py`
  - 이전 pairwise/label 평가 계열입니다.
  - 현재 최종 목표는 Top-K retrieval이므로 보조 진단용으로만 봅니다.

## 검증/진단

- `scripts/test_live_topk_units.py`
  - 카메라 없이 live helper, Top-K payload, grouping, recorder top-N embedding을 검사합니다.

- `scripts/agent_validate.sh`
  - 프로젝트 기본 환경, 모델 파일, 로그/스냅샷 쓰기 가능 여부를 확인합니다.

- `scripts/mac_diagnostics.py`, `scripts/test_camera_macos.py`
  - macOS 카메라/환경 진단용입니다.

- `scripts/test_osc_loopback.py`
  - OSC 송수신 테스트입니다.

- `scripts/test_video_writer_codecs.py`
  - mp4 writer codec 테스트입니다.

## TouchDesigner

- `touchdesigner/touchdesigner_topk_callbacks.py`
  - Top-K clip path를 TouchDesigner Movie File In 등에 연결하는 callback 참고 코드입니다.

- `touchdesigner/touchdesigner_oscin2_callbacks.py`, `touchdesigner/touchdesigner_type_c_multiplay_callbacks.py`
  - 이전/보조 TouchDesigner OSC callback입니다.

