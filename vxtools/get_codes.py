from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

CODE_POOL = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "A", "B", "C", "D", "E", "F", "G", "H", "J", "K",
    "L", "M", "N", "P", "Q", "R", "S", "T", "U", "V",
    "W", "X", "Y",
]


def generate_app_id(app_name: str) -> str:
    checksum = hashlib.sha1()
    checksum.update(app_name.encode("ascii"))
    code = "".join(CODE_POOL[value % len(CODE_POOL)] for value in bytearray(checksum.digest()))
    return f"{code[0:3]}-{code[3:6]}-{code[6:9]}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate VX app IDs for app folders.")
    parser.add_argument("apps_root", nargs="?", default=os.environ.get("VXAPPS_ROOT", "."), help="Directory of VX apps.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    apps_root = Path(args.apps_root).resolve()
    for app in sorted(apps_root.iterdir()):
        app_name = app.stem
        print(f"{app_name}: {generate_app_id(app_name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
