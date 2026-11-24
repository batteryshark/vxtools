from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from convert_vxregistry import convert_vxregistry


def new_entrypoint_template() -> dict:
    return {
        "name": "",
        "map": "smoothie.map",
        "executable": "",
        "args": "",
        "cwd": "",
        "envar": [],
        "preload": [],
    }


def upgrade_vxapp(path_to_vxapp: Path) -> None:
    info_db = {"name": "", "configuration": []}
    path_to_info = path_to_vxapp / "vxapp.info"
    if path_to_info.exists() or not (path_to_vxapp / "metadata.json").exists():
        return

    print(f"Converting: {path_to_vxapp.name}")
    with (path_to_vxapp / "metadata.json").open("r", encoding="utf-8") as metadata_file:
        info_db["name"] = json.load(metadata_file)["name"]

    src_smoothie = path_to_vxapp / "config" / "default" / "vxfilesystem"
    dest_smoothie = path_to_vxapp / "content" / "smoothie.map"
    if src_smoothie.exists():
        shutil.move(src_smoothie, dest_smoothie)

    src_reg = path_to_vxapp / "config" / "default" / "vxregistry"
    dest_reg = path_to_vxapp / "content" / "vxregistry.ini"
    if src_reg.exists():
        convert_vxregistry(str(src_reg), str(dest_reg))

    ep_path = path_to_vxapp / "config" / "default" / "entrypoint"
    with ep_path.open("r", encoding="utf-8") as entrypoint_file:
        data = json.load(entrypoint_file)
        for entrypoint_name, entrypoint_config in data.items():
            entrypoint = new_entrypoint_template()
            if dest_reg.exists():
                entrypoint["envar"].append("PDXREG=C:\\app\\pdxreg.ini")
                entrypoint["preload"].extend(["pdxreg32.dll", "pdxreg64.dll"])

            entrypoint["name"] = entrypoint_name
            entrypoint["executable"] = entrypoint_config.get("executable_path", "")
            entrypoint["args"] = entrypoint_config.get("executable_arguments", "")
            entrypoint["cwd"] = entrypoint_config.get("executable_origin", "")
            info_db["configuration"].append(entrypoint)

    with path_to_info.open("w", encoding="utf-8") as info_file:
        json.dump(info_db, info_file, indent=4)

    shutil.rmtree(path_to_vxapp / "config")
    (path_to_vxapp / "metadata.json").unlink()

    for desktop_ini in path_to_vxapp.rglob("desktop.ini"):
        desktop_ini.unlink()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upgrade legacy VX app folders to vxapp.info format.")
    parser.add_argument("path", help="Directory containing .vxapp folders to upgrade.")
    parser.add_argument("--yes", action="store_true", help="Allow destructive migration of config and metadata files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or [])
    if not args.yes:
        print("Refusing to modify apps without --yes. This command removes legacy config and metadata files.")
        return 2

    vxapp_root = Path(args.path).resolve()
    for app_path in vxapp_root.iterdir():
        if app_path.is_dir():
            upgrade_vxapp(app_path)
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
