from pathlib import Path

from vxtools.diffgen import DiffRequest, collect_changes, write_diff


def test_collect_changes_tracks_added_changed_and_deleted_files(tmp_path: Path) -> None:
    old = tmp_path / "old"
    new = tmp_path / "new"
    old.mkdir()
    new.mkdir()
    (old / "deleted.txt").write_text("old", encoding="utf-8")
    (old / "changed.txt").write_text("old", encoding="utf-8")
    (new / "changed.txt").write_text("new", encoding="utf-8")
    (new / "added.txt").write_text("new", encoding="utf-8")

    request = DiffRequest(old, new, Path("C:/app"), tmp_path / "out")
    result = collect_changes(request)

    assert result.deleted_entries == [Path("C:/app/deleted.txt")]
    assert result.added_entries == [new / "added.txt"]
    assert result.changed_entries == [new / "changed.txt"]


def test_write_diff_copies_added_files_and_writes_removes(tmp_path: Path) -> None:
    old = tmp_path / "old"
    new = tmp_path / "new"
    out = tmp_path / "out"
    old.mkdir()
    new.mkdir()
    (old / "deleted.txt").write_text("old", encoding="utf-8")
    (new / "added.txt").write_text("new", encoding="utf-8")

    write_diff(DiffRequest(old, new, Path("C:/app"), out))

    assert (out / "added.txt").read_text(encoding="utf-8") == "new"
    assert (out / "smoothie_addon.map").read_text(encoding="utf-8") == f"REMOVE;{Path('C:/app/deleted.txt')}\n"
