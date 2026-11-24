from pathlib import Path
from zipfile import ZipFile

from vxlib.packaging import create_zip, get_target_info


def test_small_directory_uses_zip(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "game.exe").write_bytes(b"hello")

    assert get_target_info(source)["format"] == "ZIP"


def test_many_files_use_iso(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for index in range(51):
        (source / f"file-{index}.txt").write_text("x", encoding="utf-8")

    assert get_target_info(source)["format"] == "ISO"


def test_zip_preserves_relative_paths(tmp_path: Path) -> None:
    source = tmp_path / "source"
    nested = source / "nested"
    nested.mkdir(parents=True)
    (nested / "file.txt").write_text("data", encoding="utf-8")

    zip_path = create_zip(tmp_path, "archive", source)

    with ZipFile(zip_path) as archive:
        assert archive.namelist() == ["nested/file.txt"]
