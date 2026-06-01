# TouchDesigner Top-12 송출 규칙

## 기본 규칙

3층 query가 발생하면 시스템은 gallery 전체를 ReID similarity로 점수화합니다.

그 뒤 순수 점수순 12개가 아니라, 전시장 출력 구성을 위해 camera-covered Top-12를 만듭니다.

## 슬롯 배치

```text
rank 01 = tapo_1 best
rank 02 = tapo_2 best
rank 03 = tapo_3 best
rank 04 = duplicate score #1

rank 05 = tapo_4 best
rank 06 = tapo_5 best
rank 07 = tapo_6 best
rank 08 = duplicate score #2

rank 09 = tapo_7 best
rank 10 = tapo_8 best
rank 11 = tapo_9 best
rank 12 = duplicate score #3
```

TouchDesigner에서는 `movie_clip_1`~`movie_clip_12` Movie File In TOP을 준비합니다.

`touchdesigner/touchdesigner_topk_callbacks.py`는 rank 번호에 맞게 각 `movie_clip_N.par.file`에 mp4 path를 넣습니다.

## 카메라 clip이 없을 때

특정 camera label에 gallery clip이 아직 없을 수 있습니다.

이 경우:

- 해당 슬롯을 비워두지 않습니다.
- 아직 선택되지 않은 전체 후보 중 similarity score가 가장 높은 clip으로 채웁니다.
- `coverage_fallback=true`로 기록합니다.
- `intended_cam_label`에는 원래 들어가야 했던 카메라가 기록됩니다.
- `actual_cam_label`에는 실제 들어간 카메라가 기록됩니다.

## OSC payload

Flat row:

```text
event_id, timestamp, query_id, query_cam_id, k, result_count, gallery_count,
rank_1, clip_id_1, clip_path_1, score_1, cam_id_1, fallback_1, ...
```

개별 OSC:

```text
/walnut/topk/cam/<query_cam>/result/<rank>/path
/walnut/topk/cam/<query_cam>/result/<rank>/score
/walnut/topk/cam/<query_cam>/result/<rank>/cam_label
/walnut/topk/cam/<query_cam>/result/<rank>/slot_type
/walnut/topk/cam/<query_cam>/result/<rank>/intended_cam_label
/walnut/topk/cam/<query_cam>/result/<rank>/actual_cam_label
```

## Dry run

TouchDesigner 없이 payload를 확인하려면:

```bash
python scripts/run_live_from_camera_csv.py \
  --camera-csv config/cameras/cameras.local.csv \
  --topk 12 \
  --candidate-pool 60 \
  --topk-selection-mode camera-covered \
  --osc-dry-run
```

