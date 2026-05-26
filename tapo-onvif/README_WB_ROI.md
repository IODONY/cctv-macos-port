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
python wb_roi_picker.py --profile wb_profiles.json --camera c210_1f --angle entrance --mock --headless-save --x 640 --y 360 --size 21
```

## Later, after the Tapo account unlocks

```bash
python wb_roi_picker.py --profile wb_profiles.json --camera c210_1f --angle entrance
python wb_auto_calibrate.py --profile wb_profiles.json --camera c210_1f --angle entrance --apply --iterations 5 --write-profile
```

`--apply` is the only mode that contacts the camera through the local API.
Before applying changes, the current `image.common` response is backed up under
`/Users/fullcodex/CCTV_Project/logs/tapo_wb_backups/`.
