import os
import sys
import json
import pathlib
import site
from pprint import pprint

from onvif import ONVIFCamera
from zeep.helpers import serialize_object


def find_wsdl_dir():
    """
    onvif-zeep 설치 위치에서 wsdl 폴더를 최대한 자동으로 찾는다.
    못 찾으면 None을 반환하고, ONVIFCamera의 기본 동작에 맡긴다.
    """
    candidates = []

    try:
        import onvif
        onvif_dir = pathlib.Path(onvif.__file__).resolve().parent
        candidates.append(onvif_dir / "wsdl")
    except Exception:
        pass

    try:
        candidates.append(pathlib.Path(sys.prefix) / "wsdl")
    except Exception:
        pass

    candidates.append(pathlib.Path("/etc/onvif/wsdl"))

    site_dirs = []
    try:
        site_dirs.extend(site.getsitepackages())
    except Exception:
        pass

    try:
        site_dirs.append(site.getusersitepackages())
    except Exception:
        pass

    for base in site_dirs:
        base = pathlib.Path(base)
        if base.exists():
            for p in base.rglob("devicemgmt.wsdl"):
                candidates.append(p.parent)

    for c in candidates:
        if c and (c / "devicemgmt.wsdl").exists():
            return str(c)

    return None


def to_plain(obj):
    return serialize_object(obj, target_cls=dict)


def main():
    host = os.environ.get("CAM_IP")
    user = os.environ.get("TAPO_USER")
    password = os.environ.get("TAPO_PASS")
    port = int(os.environ.get("ONVIF_PORT", "2020"))

    if not host or not user or not password:
        print("환경변수를 먼저 설정하세요:")
        print('export CAM_IP="192.168.0.50"')
        print('export TAPO_USER="your_camera_account"')
        print('read -s TAPO_PASS')
        print("export TAPO_PASS")
        sys.exit(1)

    wsdl_dir = os.environ.get("ONVIF_WSDL") or find_wsdl_dir()

    print(f"[INFO] Host: {host}")
    print(f"[INFO] Port: {port}")
    print(f"[INFO] User: {user}")
    print(f"[INFO] WSDL: {wsdl_dir or '(library default)'}")

    if wsdl_dir:
        cam = ONVIFCamera(host, port, user, password, wsdl_dir)
    else:
        cam = ONVIFCamera(host, port, user, password)

    print("\n[1] Device information")
    try:
        info = cam.devicemgmt.GetDeviceInformation()
        pprint(to_plain(info))
    except Exception as e:
        print("[ERROR] GetDeviceInformation 실패")
        print(repr(e))
        sys.exit(1)

    print("\n[2] Media profiles")
    media = cam.create_media_service()
    profiles = media.GetProfiles()

    if not profiles:
        print("[ERROR] Media profile이 없습니다.")
        sys.exit(1)

    for i, p in enumerate(profiles):
        print(f"\n--- Profile {i} ---")
        print("Name:", getattr(p, "Name", None))
        print("Token:", getattr(p, "token", None))

        vsc = getattr(p, "VideoSourceConfiguration", None)
        if vsc:
            print("VideoSourceConfiguration token:", getattr(vsc, "token", None))
            print("SourceToken:", getattr(vsc, "SourceToken", None))

    print("\n[3] Imaging service check")
    try:
        imaging = cam.create_imaging_service()
    except Exception as e:
        print("[ERROR] Imaging service 생성 실패")
        print("이 경우 이 카메라는 ONVIF Imaging Service를 노출하지 않을 가능성이 큽니다.")
        print(repr(e))
        sys.exit(1)

    checked_tokens = set()

    for i, p in enumerate(profiles):
        vsc = getattr(p, "VideoSourceConfiguration", None)
        if not vsc:
            continue

        source_token = getattr(vsc, "SourceToken", None)
        if not source_token or source_token in checked_tokens:
            continue

        checked_tokens.add(source_token)

        print(f"\n--- Imaging for SourceToken: {source_token} ---")

        try:
            settings = imaging.GetImagingSettings({
                "VideoSourceToken": source_token
            })
            print("\nCurrent ImagingSettings:")
            pprint(to_plain(settings))
        except Exception as e:
            print("[ERROR] GetImagingSettings 실패")
            print("NoImagingForSource / ActionNotSupported 류라면 ONVIF로 WB 제어가 안 됩니다.")
            print(repr(e))
            continue

        try:
            options = imaging.GetOptions({
                "VideoSourceToken": source_token
            })
            print("\nImaging Options:")
            pprint(to_plain(options))
        except Exception as e:
            print("[WARN] GetOptions 실패")
            print("현재값은 읽혔지만, 수동 설정 가능 범위 확인은 어렵습니다.")
            print(repr(e))

        wb = getattr(settings, "WhiteBalance", None)
        print("\nWhiteBalance summary:")
        if wb is None:
            print("WhiteBalance 항목 없음 → ONVIF로 WB 조작 불가 가능성이 큼")
        else:
            pprint(to_plain(wb))


if __name__ == "__main__":
    main()
