# Clip Match Evaluation

## Current Folder Structure

The current local dataset root is:

```text
data/labeld_clips/
  Origin/
  person_001/
  person_002/
  person_003/
```

The misspelled folder name `labeld_clips` is supported as the current source of truth. Do not rename it automatically. `data/labeled_clips/` is the preferred spelling for a future manual cleanup only.

`Origin/` is raw/source material and is excluded from identity labels by default.

## Manifest Generation

Generate clip and pair manifests:

```sh
source .venv/bin/activate
python scripts/generate_clip_manifest.py --root data/labeld_clips --out-dir data/labels --max-negative-pairs 100
```

Outputs:

- `data/labels/clips.csv`
- `data/labels/pair_labels.csv`

`clips.csv` columns:

```text
clip_id,identity_id,cam_id,take_id,clip_path,notes
```

Example:

```text
person_002_cam_2_04,person_002,cam_2,04,data/labeld_clips/person_002/cam_2_04.mp4,
```

`pair_labels.csv` columns:

```text
pair_id,clip_id_a,clip_id_b,identity_id_a,identity_id_b,label,pair_type,notes
```

- Same identity pairs use `label=1`.
- Different identity pairs use `label=0`.
- Same-person cross-camera pairs are listed before same-camera pairs.
- Hard negatives between different identities sharing the same camera are listed before other negative pairs.

## Evaluation

Run evaluation only on local project MP4 files:

```sh
source .venv/bin/activate
python scripts/evaluate_labeled_clips.py \
  --clips data/labels/clips.csv \
  --pairs data/labels/pair_labels.csv \
  --allow-provisional
```

Outputs:

- JSON: `logs/clip_eval/results.json`
- Markdown: `docs/reports/CLIP_MATCH_EVAL_REPORT.md`

The evaluator preserves these outcomes:

- `matched`
- `ambiguous`
- `low_confidence`
- `no_match`

Default scoring uses appearance-weighted profile comparison with a `0.75` match threshold and `0.60` ambiguous threshold. Type A/B match flags and the original Type C-style raw score are still included in JSON as reference signals, but the report keeps uncertain cases as `ambiguous` or `low_confidence` instead of forcing a binary answer.

Optional weight override format:

```sh
python scripts/evaluate_labeled_clips.py --weights top=1.4,bottom=1.0,bag=0.8
```

No camera, RTSP, TouchDesigner, full tracking, or long-running GUI tests are started by these manifest scripts. Generated logs remain under ignored `logs/`.
