"""
Read-only probe for Tapo local/proprietary image settings using pytapo.

Purpose:
    Look for hidden/local fields such as wb_R_gain, wb_G_gain, wb_B_gain,
    wb_type, style, chroma, luma, contrast, saturation, night_vision_mode, etc.

This script does not write any setting to the camera.

Install:
    source ~/tapo-onvif/.venv/bin/activate
    python -m pip install pytapo

Run:
    python probe_tapo_local_image_readonly.py
"""

import json
from pprint import pprint

from pytapo import Tapo

# ============================================================
# 사용자 설정 영역
# Tapo 앱 로그인 계정이 아니라,
# Tapo 앱 > 카메라 설정 > Advanced Settings > Camera Account
# 에서 만든 카메라 전용 ID / PW를 입력하세요.
# ============================================================
CAMERA_IP = "192.168.5.51"
CAMERA_ID = "iodony418@gmail.com"
CAMERA_PW = "12qwaszx//"

# 결과 전체를 저장할 파일명
OUTPUT_JSON = "tapo_local_probe_output.json"

# ============================================================

INTERESTING_KEY_PARTS = [
    "wb", "white", "gain", "lock_red", "lock_green", "lock_blue",
    "chroma", "luma", "saturation", "contrast", "sharpness",
    "style", "night", "vision", "inf_", "wtl", "light_freq",
    "exp", "shutter", "wide_dynamic", "backlight", "dehaze",
]


def find_interesting(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else str(key)
            lower_key = str(key).lower()
            if any(part in lower_key for part in INTERESTING_KEY_PARTS):
                hits.append((new_path, value))
            hits.extend(find_interesting(value, new_path))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            hits.extend(find_interesting(value, f"{path}[{index}]"))
    return hits


def safe_call(label, func):
    print(f"\n=== {label} ===")
    try:
        data = func()
        pprint(data)
        return data
    except Exception as exc:
        print(f"[FAILED] {label}: {exc}")
        return {"__error__": str(exc)}


def main():
    if "YOUR_CAMERA_PASSWORD_HERE" in CAMERA_PW:
        raise SystemExit("CAMERA_PW를 실제 Camera Account 비밀번호로 바꿔주세요.")

    tapo = Tapo(CAMERA_IP, CAMERA_ID, CAMERA_PW)
    results = {}

    results["getBasicInfo"] = safe_call("getBasicInfo", tapo.getBasicInfo)

    # pytapo에 내장된 메서드가 있으면 사용
    for method_name in [
        "getMost",
        "getDayNightModeConfig",
        "getRotationStatus",
    ]:
        if hasattr(tapo, method_name):
            results[method_name] = safe_call(method_name, getattr(tapo, method_name))

    # HomeAssistant-Tapo-Control 로그에서 보이는 함수명들을 읽기 전용으로 직접 호출
    raw_calls = {
        "getLdc_common_switch": (
            "getLdc",
            {"image": {"name": ["common", "switch"]}},
        ),
        "getLightFrequencyInfo_common": (
            "getLightFrequencyInfo",
            {"image": {"name": ["common"]}},
        ),
        "getNightVisionModeConfig_switch": (
            "getNightVisionModeConfig",
            {"image": {"name": ["switch"]}},
        ),
        "getWhitelampConfig_switch": (
            "getWhitelampConfig",
            {"image": {"name": ["switch"]}},
        ),
        "getNightVisionCapability": (
            "getNightVisionCapability",
            {"image_capability": {"name": ["supplement_lamp"]}},
        ),
    }

    for label, (method, params) in raw_calls.items():
        results[label] = safe_call(
            f"executeFunction({method})",
            lambda method=method, params=params: tapo.executeFunction(method, params),
        )

    print("\n\n==============================")
    print("INTERESTING IMAGE/WB-LIKE FIELDS")
    print("==============================")

    hits = find_interesting(results)
    if not hits:
        print("관심 필드를 찾지 못했습니다.")
    else:
        for path, value in hits:
            if isinstance(value, (dict, list)):
                value_repr = json.dumps(value, ensure_ascii=False)[:500]
            else:
                value_repr = repr(value)
            print(f"{path} = {value_repr}")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n전체 결과 저장: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
