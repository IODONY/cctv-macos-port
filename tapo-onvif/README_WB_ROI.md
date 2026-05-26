# ROI-based manual white balance for Tapo C200C/C210

This module lets you choose a white/neutral reference region per camera angle,
then computes manual RGB WB gains from that region. It is safe to code and test
without a camera because `--mock` and `--image` modes do not connect to Tapo.

## Setup

```bash
cd /Users/fullcodex/CCTV_Project/tapo-onvif
test -d .venv || python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-wb.txt
test -f wb_profiles.json || cp wb_profiles.example.json wb_profiles.json
cp .env.example .env
```

## Camera-less test

```bash
python wb_auto_calibrate.py --profile wb_profiles.example.json --camera c210_1f --angle entrance --mock
python wb_roi_picker.py --profile wb_profiles.json --camera c210_1f --angle entrance --mock
```

Headless ROI save without a UI:

```bash
python wb_roi_picker.py --profile wb_profiles.json --camera c210_1f --angle entrance --mock --headless-save --x 640 --y 360 --size 5
```

## Later, after the Tapo account unlocks

```bash
python wb_roi_picker.py --profile wb_profiles.json --camera c210_1f --angle entrance
python wb_auto_calibrate.py --profile wb_profiles.json --camera c210_1f --angle entrance --apply --iterations 5 --write-profile
```

`--apply` is the only mode that contacts the camera through the local API.
Before applying changes, the current `image.common` response is backed up under
`/Users/fullcodex/CCTV_Project/logs/tapo_wb_backups/`.

For interactive preview, press `s` in the ROI picker with `--apply-on-save`.
This saves the ROI, applies the proposed WB gain once, waits briefly, and
refreshes the preview frame in the same window. Press `-` to lower exposure
and `=` to raise exposure; each keypress applies the exposure change and
refreshes the preview.

```bash
TAPO_C210_1F_RTSP_URL='rtsp://CAMERA_RTSP_USER:CAMERA_RTSP_PASSWORD@CAMERA_IP:554/stream1' \
python wb_roi_picker.py --profile wb_profiles.json --camera c210_1f --angle entrance --apply-on-save
```

Add `--force` only when you intentionally want to apply even if the ROI safety
checks report clipping, darkness, or uneven patches.
