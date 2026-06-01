#!/usr/bin/env python3
"""Fast OSC loopback probe on 127.0.0.1."""

from __future__ import annotations

import argparse
import json
import socket
import threading
import time


def udp_server(host: str, port: int, received: list[bytes]) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    sock.bind((host, port))
    try:
        data, _ = sock.recvfrom(2048)
        received.append(data)
    except socket.timeout:
        pass
    finally:
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9700)
    args = parser.parse_args()

    if args.host != "127.0.0.1":
        print(json.dumps({"ok": False, "error": "loopback host must be 127.0.0.1"}))
        return 1

    received: list[bytes] = []
    thread = threading.Thread(target=udp_server, args=(args.host, args.port, received))
    thread.start()
    time.sleep(0.05)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(b"/walnut/diagnostic\x00,si\x00\x00loopback\x00\x00\x00\x00\x00\x00\x00\x01", (args.host, args.port))
    finally:
        sock.close()
    thread.join(timeout=1.5)

    report = {
        "host": args.host,
        "port": args.port,
        "received": bool(received),
        "bytes": len(received[0]) if received else 0,
        "ok": bool(received),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
