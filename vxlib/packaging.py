from __future__ import annotations

import math
import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
import json

GB = 1024**3
MB = 1024**2
ALLOCATION_UNIT = 32768


@dataclass(frozen=True)
class ImageBuildOptions:
    mkisofs_path: Path
    diskpart_command: str = "DISKPART"
    dry_run: bool = False


@dataclass(frozen=True)
class PackageRequest:
    source_path: Path
    staging_root: Path
    config_path: Path | None
    windows_base_path: Path
    image_options: ImageBuildOptions


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_mkisofs_path() -> Path:
    executable_name = "mkisofs.exe" if platform.system() == "Windows" else "mkisofs"
    on_path = shutil.which(executable_name)
    return Path(on_path) if on_path else Path(executable_name)


def default_windows_base_path() -> Path:
    return repo_root() / "templates" / "windows_base.zip"


def get_target_info(target: str | Path = ".") -> dict[str, int | str]:
    target_info: dict[str, int | str] = {
        "num_entries": 0,
        "size": 0,
        "num_blocks": 0,
        "format": "ZIP",
    }
    target_path = Path(target)
    large_file = False

    for item in target_path.rglob("*"):
        if not item.is_file():
            continue

        item_size = item.stat().st_size
        if item_size > 4 * GB:
            large_file = True

        target_info["num_entries"] += 1
        target_info["size"] += item_size
        target_info["num_blocks"] += math.ceil(item_size / ALLOCATION_UNIT)

    if large_file or target_info["num_entries"] > 1000 or target_info["size"] > 8 * GB:
        target_info["format"] = "VHDX"
    elif target_info["num_entries"] > 50 or target_info["size"] > 128 * MB:
        target_info["format"] = "ISO"

    return target_info


def create_zip(out_root: str | Path, out_name: str, target: str | Path = ".") -> Path:
    target_path = Path(target)
    out_path = Path(out_root) / f"{out_name}.zip"
    with ZipFile(out_path, "w") as zip_file:
        for item in target_path.rglob("*"):
            if item.is_file():
                zip_file.write(item, item.relative_to(target_path))
    return out_path


def create_iso(
    out_root: str | Path,
    out_name: str,
    target: str | Path,
    options: ImageBuildOptions | None = None,
) -> Path:
    build_options = options or ImageBuildOptions(default_mkisofs_path())
    out_path = Path(out_root) / f"{out_name}.iso"
    if build_options.dry_run:
        return out_path

    subprocess.run(
        [
            str(build_options.mkisofs_path),
            "-D",
            "-udf",
            "-o",
            str(out_path),
            str(Path(target).resolve()),
        ],
        check=True,
    )
    return out_path


def create_vhdx(
    out_root: str | Path,
    out_name: str,
    src_data_path: str | Path,
    num_blocks: int,
    options: ImageBuildOptions | None = None,
) -> Path:
    build_options = options or ImageBuildOptions(default_mkisofs_path())
    vhdx_path = (Path(out_root) / f"{out_name}.vhdx").resolve()
    package_size_mb = int((num_blocks * ALLOCATION_UNIT) / MB) + 1
    package_size_mb += int((40964 * package_size_mb) / MB) + 1

    if build_options.dry_run:
        return vhdx_path

    mounted_root_path = Path(tempfile.mkdtemp())
    start_script_file = tempfile.NamedTemporaryFile("w", encoding="ascii", delete=False)
    end_script_file = tempfile.NamedTemporaryFile("w", encoding="ascii", delete=False)

    try:
        start_script_file.write(
            "\n".join(
                [
                    f'CREATE VDISK FILE="{vhdx_path}" maximum={package_size_mb} type=expandable',
                    f'SELECT VDISK FILE="{vhdx_path}"',
                    "ATTACH VDISK",
                    "CLEAN",
                    "CREATE PART PRI",
                    "SELECT PART 1",
                    "FORMAT FS=NTFS QUICK",
                    f"ASSIGN MOUNT={mounted_root_path}",
                    "EXIT",
                ]
            )
        )
        start_script_file.close()
        subprocess.run([build_options.diskpart_command, "/s", start_script_file.name], check=True)

        for item in Path(src_data_path).iterdir():
            destination = mounted_root_path / item.name
            if item.is_dir():
                shutil.copytree(item, destination)
            else:
                shutil.copy2(item, destination)

        end_script_file.write(
            "\n".join(
                [
                    f'SELECT VDISK FILE="{vhdx_path}"',
                    "SELECT PARTITION 1",
                    "REMOVE",
                    "DETACH VDISK",
                    "EXIT",
                ]
            )
        )
        end_script_file.close()
        subprocess.run([build_options.diskpart_command, "/s", end_script_file.name], check=True)
    finally:
        Path(start_script_file.name).unlink(missing_ok=True)
        Path(end_script_file.name).unlink(missing_ok=True)
        shutil.rmtree(mounted_root_path, ignore_errors=True)

    return vhdx_path


def create_image(
    target: str | Path,
    out_root: str | Path = ".",
    options: ImageBuildOptions | None = None,
) -> Path:
    image_name = Path(target).name
    if Path(target).suffix:
        image_name = Path(target).stem

    target_info = get_target_info(target)
    image_format = target_info["format"]

    if image_format == "ZIP":
        return create_zip(out_root, image_name, target)
    if image_format == "ISO":
        return create_iso(out_root, image_name, target, options)
    return create_vhdx(out_root, image_name, target, int(target_info["num_blocks"]), options)


def write_vxapp_config(config_path: str | Path) -> None:
    entrypoints = []
    while True:
        entry = input("Input an Entrypoint;title[optional], blank to end: ")
        if entry == "":
            break

        executable_path = entry
        name = "Play Game"
        args = ""
        if entry.count(";") == 1:
            executable_path, name = entry.split(";")
        elif entry.count(";") == 2:
            executable_path, name, args = entry.split(";")

        entrypoints.append(
            {
                "name": name,
                "map": "smoothie.map",
                "executable": f"C:\\app\\{executable_path}",
                "args": args,
                "cwd": "",
                "envar": [],
                "preload": ["pdxproc.dlldynamic", "pdxfs.dlldynamic"],
            }
        )

    with Path(config_path).open("w", encoding="utf-8") as config_file:
        json.dump(entrypoints, config_file, indent=4)


def package_directory(request: PackageRequest) -> Path:
    app_name = request.source_path.name
    app_root = request.staging_root / f"{app_name}.vxapp"
    content_root = app_root / "content"

    if request.image_options.dry_run:
        return app_root

    content_root.mkdir(parents=True, exist_ok=True)
    config_path = app_root / "vxapp.config"

    if request.config_path and request.config_path.exists():
        shutil.copy2(request.config_path, config_path)
    else:
        write_vxapp_config(config_path)

    image_path = create_image(request.source_path, content_root, request.image_options)
    shutil.copy2(request.windows_base_path, content_root / "windows_base.zip")

    smoothie_path = content_root / "smoothie.map"
    with smoothie_path.open("w", encoding="utf-8") as map_file:
        map_file.write("MAP;windows_base.zip;C:\\\n")
        map_file.write(f"MAP;{image_path.name};C:\\app\n")

    return app_root
