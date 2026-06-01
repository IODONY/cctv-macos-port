#!/usr/bin/env python3
"""
Tapo C210/C200C local API white-balance experiment script.

This uses pytapo's local API, not ONVIF. It is intentionally conservative:
- APPLY_CHANGES defaults to False.
- It backs up the current image.common block before applying.
- It only sends wb_type / wb_R_gain / wb_G_gain / wb_B_gain.

Install in your venv first:
  python -m pip install pytapo

Run:
  python set_tapo_wb_local_api_with_vars.py
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from pprint import pprint

from pytapo import Tapo

# ============================================================
# 사용자 설정 영역
# ============================================================
CAMERA_IP = "192.168.1.9"
CAMERA_ID = "humanjh@gmail.com"              # Tapo Camera Account 또는 성공한 pytapo 로그인 ID
CAMERA_PW = "tapohyeop2001"  # 여기에 비밀번호 입력. 공유하지 마세요.

# 기본은 테스트만 하고 쓰지 않습니다. 실제 적용하려면 True로 바꾸세요.
APPLY_CHANGES = True

# 가장 가능성 높은 setter 후보.
# 1차 추천: setDayNightModeConfig
# 실패하면 수동으로 "setLdc" 또는 "setLightFrequencyInfo"를 넣어 재시도해볼 수 있습니다.
SETTER_METHOD = "setDayNightModeConfig"

# WB 설정값. Kelvin이 아니라 RGB gain입니다.
# 따뜻하게: R↑, B↓ / 차갑게: R↓, B↑ / G는 처음엔 50 유지 권장.
WB_TYPE = "manual"  # 로그상 현재값은 "auto". 수동 시도값은 보통 "manual".
WB_R_GAIN = 80
WB_G_GAIN = 50
WB_B_GAIN = 20

# 너무 큰 값을 실수로 넣지 않기 위한 안전 범위.
MIN_GAIN = 0
MAX_GAIN = 100

# ============================================================


def clamp_int(value: int, min_value: int = MIN_GAIN, max_value: int = MAX_GAIN) -> str:
    value = int(value)
    if not (min_value <= value <= max_value):
        raise ValueError(f"Gain value out of range: {value}. Use {min_value}~{max_value}.")
    return str(value)


def get_image_common(tapo: Tapo) -> dict:
    """Read image.common from the most relevant available getter."""
    # Your probe showed getDayNightModeConfig returns image.common directly.
    try:
        data = tapo.getDayNightModeConfig()
    except AttributeError:
        data = tapo.executeFunction("getDayNightModeConfig", {"image": {"name": "common"}})

    common = data.get("image", {}).get("common")
    if not isinstance(common, dict):
        raise RuntimeError(f"Could not find image.common in response: {data}")
    return common


def show_wb(common: dict, title: str) -> None:
    print(f"\n=== {title} ===")
    for key in [
        "wb_type",
        "wb_R_gain",
        "wb_G_gain",
        "wb_B_gain",
        "style",
        "luma",
        "chroma",
        "saturation",
        "contrast",
        "sharpness",
        "light_freq_mode",
    ]:
        if key in common:
            print(f"{key}: {common[key]}")


def save_backup(common: dict) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(f"tapo_image_common_backup_{stamp}.json")
    path.write_text(json.dumps(common, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    if CAMERA_PW == "YOUR_PASSWORD_HERE":
        print("ERROR: 스크립트 상단 CAMERA_PW에 실제 비밀번호를 넣어주세요.")
        return 1

    print(f"[INFO] Connecting to {CAMERA_IP} as {CAMERA_ID} ...")
    tapo = Tapo(CAMERA_IP, CAMERA_ID, CAMERA_PW)

    before = get_image_common(tapo)
    show_wb(before, "CURRENT WB / IMAGE COMMON")

    backup_path = save_backup(before)
    print(f"\n[BACKUP] 현재 image.common 백업 저장: {backup_path}")

    payload_common = {
        "wb_type": str(WB_TYPE),
        "wb_R_gain": clamp_int(WB_R_GAIN),
        "wb_G_gain": clamp_int(WB_G_GAIN),
        "wb_B_gain": clamp_int(WB_B_GAIN),
    }

    payload = {"image": {"common": payload_common}}

    print("\n=== PAYLOAD TO SEND ===")
    pprint({"method": SETTER_METHOD, "params": payload})

    if not APPLY_CHANGES:
        print("\n[DRY RUN] APPLY_CHANGES = False 이므로 실제 변경하지 않았습니다.")
        print("실제 적용하려면 스크립트 상단 APPLY_CHANGES = True 로 바꾼 뒤 다시 실행하세요.")
        return 0

    print(f"\n[APPLY] executeFunction({SETTER_METHOD!r}, payload) 실행 중...")
    try:
        result = tapo.executeFunction(SETTER_METHOD, payload)
    except Exception as exc:
        print("\n[ERROR] 설정 요청 실패")
        print(repr(exc))
        print("\n다음 후보를 수동으로 바꿔 재시도할 수 있습니다:")
        print('  SETTER_METHOD = "setLdc"')
        print('  SETTER_METHOD = "setLightFrequencyInfo"')
        print("단, 첫 시도는 setDayNightModeConfig가 가장 논리적으로 맞습니다.")
        return 2

    print("\n=== SET RESPONSE ===")
    pprint(result)

    after = get_image_common(tapo)
    show_wb(after, "AFTER WB / IMAGE COMMON")

    requested = deepcopy(payload_common)
    observed = {k: str(after.get(k)) for k in requested}

    print("\n=== VERIFY ===")
    print("requested:")
    pprint(requested)
    print("observed:")
    pprint(observed)

    if observed == requested:
        print("\n[OK] 읽기값 기준으로 WB 설정이 반영되었습니다.")
    else:
        print("\n[WARN] 요청은 보냈지만 읽기값이 완전히 일치하지 않습니다.")
        print("카메라가 일부 값을 무시했거나, wb_type=manual이 허용되지 않았거나, 다른 setter가 필요할 수 있습니다.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
