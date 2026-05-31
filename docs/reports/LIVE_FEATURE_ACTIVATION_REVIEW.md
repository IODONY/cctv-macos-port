# Live Feature Activation Review

Date: 2026-05-31

## Scope

Reviewed live camera execution paths for implemented features that were easy to miss at runtime, especially tracker-side ReID and session-end similarity grouping.

## Findings

### BoT-SORT tracker-side ReID was available but too hidden

- `config/trackers/botsort.yaml` intentionally keeps `with_reid: false`.
- `config/trackers/botsort_reid.yaml` enables `with_reid: true`.
- Before this update, the CSV runner could only use the ReID tracker config by passing raw bridge arguments after `--`.
- The live console/logs did not clearly state which tracker config was active.

Resolution:

- Added first-class CSV runner options:
  - `--tracker-reid`
  - `--tracker-config-path`
- Live startup now prints the resolved tracker config and `tracker_with_reid` value.
- `gallery_events.jsonl` now records `tracker_config_path` and `tracker_with_reid` per saved gallery clip.

### Session-end grouping default was too permissive for the latest multi-person truth set

- Previous default final grouping used reciprocal `topN=8`.
- The latest p1-p7 truth review showed this could over-merge different people into one large group.
- The best high-precision sweep result for that session used reciprocal `threshold=0.65`, `topN=4`.

Resolution:

- Updated live session-end merge default from `merge_reciprocal_topn=8` to `4`.
- Updated regroup/sweep script defaults to `4`.
- Updated the runbook to document the new conservative default.

## Still intentionally optional

Tracker-side ReID is not forced on globally. It is useful for reducing track ID switches, but it can add load and should be tested per machine/camera count.

Recommended test command:

```bash
python scripts/run_live_from_camera_csv.py \
  --camera-csv config/cameras/cameras.local.csv \
  --tracker-reid \
  --max-runtime-seconds 120 \
  --disable-osc
```

For a lighter baseline:

```bash
python scripts/run_live_from_camera_csv.py \
  --camera-csv config/cameras/cameras.local.csv \
  --max-runtime-seconds 120 \
  --disable-osc
```

Compare:

- total mp4 count
- gallery record count
- short clip count
- repeated track ids with multiple event tokens
- `tracker_with_reid` in `gallery_events.jsonl`

