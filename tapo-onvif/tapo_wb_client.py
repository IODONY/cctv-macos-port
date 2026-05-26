#!/usr/bin/env python3
"""Small Tapo local API wrapper for manual RGB white-balance gain updates.

This file imports pytapo only when a real camera client is created, so all
calibration code can be tested while the Tapo account is locked.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, Optional

from wb_core import clamp_gain, normalize_gains

DEFAULT_SETTER_METHOD = "setDayNightModeConfig"


def default_backup_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "logs" / "tapo_wb_backups"


def load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    load_dotenv()


def build_manual_wb_payload(gains: Dict[str, Any], wb_type: str = "manual") -> Dict[str, Any]:
    normalized = normalize_gains(gains)
    return {
        "image": {
            "common": {
                "wb_type": str(wb_type),
                "wb_R_gain": str(clamp_gain(normalized["R"])),
                "wb_G_gain": str(clamp_gain(normalized["G"])),
                "wb_B_gain": str(clamp_gain(normalized["B"])),
            }
        }
    }


class TapoWBClient:
    def __init__(self, ip: str, username: str, password: str, setter_method: str = DEFAULT_SETTER_METHOD):
        if not ip:
            raise ValueError("Camera IP is empty.")
        if not username or not password:
            raise ValueError("Tapo username/password are missing. Use .env or environment variables.")
        from pytapo import Tapo

        self.ip = ip
        self.setter_method = setter_method or DEFAULT_SETTER_METHOD
        self.tapo = Tapo(ip, username, password)

    def get_image_common(self) -> Dict[str, Any]:
        try:
            data = self.tapo.getDayNightModeConfig()
        except AttributeError:
            data = self.tapo.executeFunction("getDayNightModeConfig", {"image": {"name": "common"}})

        common = data.get("image", {}).get("common")
        if not isinstance(common, dict):
            raise RuntimeError(f"Could not find image.common in response: {data}")
        return common

    def backup_image_common(self, backup_dir: str | Path | None = None) -> Path:
        common = self.get_image_common()
        backup_path = Path(backup_dir) if backup_dir is not None else default_backup_dir()
        backup_path.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = backup_path / f"tapo_image_common_backup_{self.ip.replace('.', '_')}_{stamp}.json"
        path.write_text(json.dumps(common, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def apply_manual_wb_gains(self, gains: Dict[str, Any], wb_type: str = "manual") -> Dict[str, Any]:
        payload = build_manual_wb_payload(gains, wb_type=wb_type)
        return self.tapo.executeFunction(self.setter_method, payload)


def get_env_or_profile(profile: Dict[str, Any], value_key: str, env_key: str) -> Optional[str]:
    env_name = profile.get(env_key)
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    value = profile.get(value_key)
    return str(value) if value else None


def client_from_camera_profile(camera: Dict[str, Any]) -> TapoWBClient:
    load_dotenv_if_available()
    ip = str(camera.get("ip", ""))
    username = get_env_or_profile(camera, "tapo_username", "tapo_username_env")
    password = get_env_or_profile(camera, "tapo_password", "tapo_password_env")
    setter_method = str(camera.get("setter_method", DEFAULT_SETTER_METHOD))
    return TapoWBClient(ip=ip, username=username or "", password=password or "", setter_method=setter_method)


def print_dry_run_payload(gains: Dict[str, Any], setter_method: str = DEFAULT_SETTER_METHOD) -> None:
    print("\n=== DRY-RUN Tapo payload ===")
    pprint({"method": setter_method, "params": build_manual_wb_payload(gains)})
