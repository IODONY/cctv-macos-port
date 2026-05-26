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

Live ROI picker mode now applies on exit by default: click the ROI, press `q`,
then it saves the ROI, applies `--exposure-level` if provided, and iterates WB
until the target Kelvin error is under threshold.

```bash
TAPO_C210_1F_RTSP_URL='rtsp://CAMERA_RTSP_USER:CAMERA_RTSP_PASSWORD@CAMERA_IP:554/stream1' \
python wb_roi_picker.py --profile wb_profiles.json --camera c210_1f --angle entrance --target-kelvin 6500 --exposure-level 0 --iterations 10
```

For interactive preview, press `s` in the ROI picker with `--apply-on-save`.
This saves the ROI, applies the proposed WB gain once, waits briefly, and
refreshes the preview frame in the same window. Press `-` to lower exposure
and `=` to raise exposure; each keypress applies the exposure change and
refreshes the preview. The default exposure gain step is 100, exposure key changes
wait only 0.2 seconds before refresh, and queued repeated exposure keys are
dropped so `q`/ESC can still close the picker. No software limit is applied
unless `--exposure-min` or `--exposure-max` is provided. ROI exposure changes
send `exp_type=manual` and change `exp_gain` by default, leaving shutter alone
for video. Pass `--exposure-type auto` to restore the previous auto-exposure
mode or `--exposure-field exp_level` to test the old field.

```bash
TAPO_C210_1F_RTSP_URL='rtsp://CAMERA_RTSP_USER:CAMERA_RTSP_PASSWORD@CAMERA_IP:554/stream1' \
python wb_roi_picker.py --profile wb_profiles.json --camera c210_1f --angle entrance --apply-on-save
```

Add `--force` only when you intentionally want to apply even if the ROI safety
checks report clipping, darkness, or uneven patches.
Use `--no-apply-on-exit` if you want the picker to close without final camera
changes. If you run without `--exposure-level`, the last exposure value adjusted
with `-`/`=` is saved to the profile on exit. Before applying changes, the
current `image.common` response is backed up under
`/Users/fullcodex/CCTV_Project/logs/tapo_wb_backups/`.
