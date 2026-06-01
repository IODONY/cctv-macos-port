#!/usr/bin/env python3
"""Safe macOS diagnostics for the CCTV project.

This script does not open cameras, RTSP streams, or TouchDesigner. It checks the
active Python environment and project-local paths only.
"""

from __future__ import annotations

import importlib
import json
import os
import platform
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("YOLO_CONFIG_DIR", str(PROJECT_ROOT / "logs" / "ultralytics"))


def under_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        return False
    return True


def result(name: str, ok: bool, **details: object) -> dict[str, object]:
    return {"name": name, "ok": ok, **details}


def import_probe(module_name: str, attr: str | None = "__version__") -> dict[str, object]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic should report import failures.
        return result(module_name, False, error=repr(exc))

    details: dict[str, object] = {"module": module_name}
    if attr is not None:
        details["version"] = getattr(module, attr, "unknown")
    return result(module_name, True, **details)


def check_python() -> dict[str, object]:
    return result(
        "python",
        True,
        executable=sys.executable,
        version=sys.version.split()[0],
        platform=sys.platform,
        machine=platform.machine(),
        cwd=str(Path.cwd().resolve()),
        project_root=str(PROJECT_ROOT),
    )


def check_torch() -> list[dict[str, object]]:
    torch_result = import_probe("torch")
    checks = [torch_result]
    if not torch_result["ok"]:
        checks.append(result("torch_mps", False, error="torch import failed"))
        return checks

    torch = sys.modules["torch"]
    mps = getattr(getattr(torch, "backends", None), "mps", None)
    cuda_available = bool(torch.cuda.is_available())
    mps_available = bool(mps and mps.is_available())
    checks.append(
        result(
            "torch_mps",
            True,
            is_built=bool(mps and mps.is_built()),
            is_available=mps_available,
            cuda_available=cuda_available,
            preferred_device="cuda" if cuda_available else "mps" if mps_available else "cpu",
        )
    )
    return checks


def check_cv2_backend() -> list[dict[str, object]]:
    cv2_result = import_probe("cv2")
    checks = [cv2_result]
    if not cv2_result["ok"]:
        return checks

    cv2 = sys.modules["cv2"]
    build_info = cv2.getBuildInformation()
    checks.append(
        result(
            "opencv_backends",
            True,
            has_avfoundation=hasattr(cv2, "CAP_AVFOUNDATION"),
            has_ffmpeg=hasattr(cv2, "CAP_FFMPEG"),
            ffmpeg_enabled="FFMPEG:                      YES" in build_info
            or "FFMPEG: YES" in build_info,
        )
    )
    return checks


def check_models() -> list[dict[str, object]]:
    checks = []
    for rel in ("models/yolov8n.pt", "models/yolov8n-pose.pt"):
        path = PROJECT_ROOT / rel
        checks.append(
            result(
                rel,
                path.is_file() and path.stat().st_size > 0 and under_root(path),
                exists=path.exists(),
                size=path.stat().st_size if path.exists() else 0,
                path=str(path),
                under_root=under_root(path),
            )
        )
    return checks


def check_writable_dirs() -> list[dict[str, object]]:
    checks = []
    for rel in ("logs", "snapshots"):
        path = PROJECT_ROOT / rel
        ok = path.is_dir() and under_root(path)
        error = None
        if ok:
            try:
                with tempfile.NamedTemporaryFile(
                    prefix=".write_probe_", dir=path, delete=True
                ) as tmp:
                    tmp.write(b"ok")
            except Exception as exc:  # noqa: BLE001 - diagnostic should report failures.
                ok = False
                error = repr(exc)
        checks.append(result(f"{rel}_writable", ok, path=str(path), error=error))
    return checks


def main() -> int:
    checks: list[dict[str, object]] = []
    checks.append(check_python())
    checks.extend(check_torch())
    checks.append(import_probe("ultralytics"))
    checks.extend(check_cv2_backend())
    checks.append(import_probe("pythonosc", attr=None))
    checks.extend(check_models())
    checks.extend(check_writable_dirs())

    report = {
        "project_root": str(PROJECT_ROOT),
        "checks": checks,
        "ok": all(bool(check["ok"]) for check in checks),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
