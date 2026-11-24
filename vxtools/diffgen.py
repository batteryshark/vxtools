from __future__ import annotations

import argparse
import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiffRequest:
    old_path: Path
    new_path: Path
    virtual_root: Path
    out_path: Path


@dataclass(frozen=True)
class DiffResult:
    deleted_entries: list[Path]
    added_entries: list[Path]
    changed_entries: list[Path]


def file_hash_md5(src_path: Path) -> bytes:
    md5_object = hashlib.md5()
    block_size = 128 * md5_object.block_size
    with src_path.open("rb") as source_file:
        chunk = source_file.read(block_size)
        while chunk:
            md5_object.update(chunk)
            chunk = source_file.read(block_size)
    return md5_object.digest()


def rebase_path(path: Path, source_root: Path, destination_root: Path) -> Path:
    return destination_root / path.relative_to(source_root)


def collect_changes(request: DiffRequest) -> DiffResult:
    deleted_entries: list[Path] = []
    added_entries: list[Path] = []
    changed_entries: list[Path] = []

    for entry in request.old_path.rglob("*"):
        matching_new_entry = rebase_path(entry, request.old_path, request.new_path)
        if not matching_new_entry.exists():
            deleted_entries.append(rebase_path(matching_new_entry, request.new_path, request.virtual_root))
        elif entry.is_file() and file_hash_md5(entry) != file_hash_md5(matching_new_entry):
            changed_entries.append(matching_new_entry)

    for entry in request.new_path.rglob("*"):
        matching_old_entry = rebase_path(entry, request.new_path, request.old_path)
        if not matching_old_entry.exists():
            added_entries.append(entry)

    return DiffResult(deleted_entries, added_entries, changed_entries)


def copy_entries(entries: list[Path], source_root: Path, out_path: Path) -> None:
    for entry in entries:
        destination = rebase_path(entry, source_root, out_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if entry.is_dir():
            destination.mkdir(exist_ok=True)
        else:
            shutil.copy2(entry, destination)


def write_diff(request: DiffRequest) -> DiffResult:
    request.out_path.mkdir(parents=True, exist_ok=True)
    result = collect_changes(request)

    copy_entries(result.added_entries, request.new_path, request.out_path)
    copy_entries(result.changed_entries, request.new_path, request.out_path)

    with (request.out_path / "smoothie_addon.map").open("w", encoding="utf-8") as map_file:
        for entry in result.deleted_entries:
            map_file.write(f"REMOVE;{entry}\n")

    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a VX/Smoothie filesystem delta.")
    parser.add_argument("old", help="Original directory.")
    parser.add_argument("new", help="Updated directory.")
    parser.add_argument("virtual_root", help="Virtual root used in REMOVE entries.")
    parser.add_argument("output", help="Output directory for copied changes and smoothie_addon.map.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or [])
    request = DiffRequest(
        old_path=Path(args.old).resolve(),
        new_path=Path(args.new).resolve(),
        virtual_root=Path(args.virtual_root),
        out_path=Path(args.output).resolve(),
    )

    if not request.old_path.exists():
        print("Old Path Does not Exist!")
        return 1
    if not request.new_path.exists():
        print("New Path Does not Exist!")
        return 1

    write_diff(request)
    print("DONE!")
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
