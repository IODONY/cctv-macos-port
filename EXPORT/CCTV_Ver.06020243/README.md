# CCTV Live Top-K Exhibition Runtime Export

Production-oriented export for the live YOLO + BoT-SORT + OSNet ReID + TouchDesigner Top-12 pipeline.

Use `README_KR.md` and the Korean docs in `docs/` for the full runbook.

Main command:

```bash
python scripts/run_live_from_camera_csv.py \
  --camera-csv config/cameras/cameras.local.csv \
  --tracker-backend botsort \
  --tracker-reid \
  --topk 12 \
  --candidate-pool 60 \
  --topk-selection-mode camera-covered \
  --export-topk-dir snapshots/live_topk_exports
```

Never share `config/cameras/cameras.local.csv`; it contains local camera credentials.

