"""Tests for PathsDatManager and PathsDatHistory."""

from pathlib import Path

import pytest

from stormatter.study_manager import PathsDatHistory, PathsDatManager


def test_paths_dat_manager_get_paths(tmp_path: Path) -> None:
    """Test reading and parsing paths.dat."""
    paths_dat = tmp_path / "paths.dat"
    paths_dat.write_text('Name1 "/path/to/file1.dat"\nName2 "/path/to/file2.dat"\n')

    manager = PathsDatManager(paths_dat)
    paths = manager.get_paths(track_history=False)

    assert paths["Name1"] == Path("/path/to/file1.dat")
    assert paths["Name2"] == Path("/path/to/file2.dat")


def test_paths_dat_manager_tracks_history(tmp_path: Path) -> None:
    """Test that get_paths records history."""
    paths_dat = tmp_path / "paths.dat"
    paths_dat.write_text('Name1 "/path/to/file1.dat"\n')

    history_file = tmp_path / "test_history.json"
    history = PathsDatHistory(history_file)
    manager = PathsDatManager(paths_dat, history)

    manager.get_paths(track_history=True)

    assert history_file.exists()
    last_path = history.get_last_path(paths_dat, "Name1")
    assert last_path == Path("/path/to/file1.dat")


def test_paths_dat_manager_make_local(tmp_path: Path) -> None:
    """Test copying a file locally and updating paths.dat."""
    # Setup source file
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_file = source_dir / "data.dat"
    source_file.write_text("original data")

    # Setup paths.dat
    paths_dat = tmp_path / "paths.dat"
    paths_dat.write_text(f'Name1 "{source_file}"\n')

    # Setup destination
    dest_dir = tmp_path / "local"
    dest_dir.mkdir()

    history_file = tmp_path / "test_history.json"
    history = PathsDatHistory(history_file)
    manager = PathsDatManager(paths_dat, history)

    # Make local
    manager.make_local("Name1", dest_dir)

    # Check file was copied
    copied_file = dest_dir / "data.dat"
    assert copied_file.exists()
    assert copied_file.read_text() == "original data"

    # Check paths.dat was updated
    updated_paths = manager.get_paths(track_history=False)
    assert updated_paths["Name1"] == copied_file.resolve()

    # Check history recorded the change
    entries = history.get_file_history(paths_dat).get("Name1", [])
    assert len(entries) >= 1


def test_paths_dat_manager_revert_last_change_for_file(tmp_path: Path) -> None:
    """Test reverting a single file to its previous path."""
    paths_dat = tmp_path / "paths.dat"
    paths_dat.write_text('Name1 "/path/v1.dat"\n')

    history_file = tmp_path / "test_history.json"
    history = PathsDatHistory(history_file)
    manager = PathsDatManager(paths_dat, history)

    # Initial read
    manager.get_paths(track_history=True)

    # Update paths.dat manually to simulate a change
    paths_dat.write_text('Name1 "/path/v2.dat"\n')
    manager.get_paths(track_history=True)

    # Revert
    manager.revert_last_change_for_file("Name1")

    # Check reverted
    paths = manager.get_paths(track_history=False)
    assert paths["Name1"] == Path("/path/v1.dat")


def test_paths_dat_manager_revert_last_change(tmp_path: Path) -> None:
    """Test reverting all files to their previous paths."""
    paths_dat = tmp_path / "paths.dat"
    paths_dat.write_text('Name1 "/path/v1.dat"\nName2 "/path2/v1.dat"\n')

    history_file = tmp_path / "test_history.json"
    history = PathsDatHistory(history_file)
    manager = PathsDatManager(paths_dat, history)

    # Initial read
    manager.get_paths(track_history=True)

    # Update paths.dat
    paths_dat.write_text('Name1 "/path/v2.dat"\nName2 "/path2/v2.dat"\n')
    manager.get_paths(track_history=True)

    # Revert all
    manager.revert_last_change()

    # Check both reverted
    paths = manager.get_paths(track_history=False)
    assert paths["Name1"] == Path("/path/v1.dat")
    assert paths["Name2"] == Path("/path2/v1.dat")


def test_paths_dat_history_helpers(tmp_path: Path) -> None:
    """Test PathsDatHistory helper methods."""
    paths_dat = tmp_path / "paths.dat"
    history_file = tmp_path / "test_history.json"
    history = PathsDatHistory(history_file)

    # Record some entries
    history.record(paths_dat, "Name1", Path("/path/v1.dat"), timestamp=1000.0)
    history.record(paths_dat, "Name1", Path("/path/v2.dat"), timestamp=2000.0)
    history.save()

    # Test get_last_update
    last_update = history.get_last_update(paths_dat, "Name1")
    assert last_update is not None
    assert last_update["path"] == "/path/v2.dat"
    assert last_update["timestamp"] == 2000.0

    # Test get_last_path
    last_path = history.get_last_path(paths_dat, "Name1")
    assert last_path == Path("/path/v2.dat")

    # Test get_last_timestamp
    last_ts = history.get_last_timestamp(paths_dat, "Name1")
    assert last_ts == 2000.0

    # Test get_latest_snapshot
    snapshot = history.get_latest_snapshot(paths_dat)
    assert snapshot["Name1"] == Path("/path/v2.dat")


def test_paths_dat_history_persistence(tmp_path: Path) -> None:
    """Test that history persists across instances."""
    paths_dat = tmp_path / "paths.dat"
    history_file = tmp_path / "test_history.json"

    # First instance
    history1 = PathsDatHistory(history_file)
    history1.record(paths_dat, "Name1", Path("/path/v1.dat"))
    history1.save()

    # Second instance
    history2 = PathsDatHistory(history_file)
    last_path = history2.get_last_path(paths_dat, "Name1")
    assert last_path == Path("/path/v1.dat")


def test_paths_dat_manager_make_local_nonexistent_name(tmp_path: Path) -> None:
    """Test that make_local raises ValueError for nonexistent names."""
    paths_dat = tmp_path / "paths.dat"
    paths_dat.write_text('Name1 "/path/to/file.dat"\n')

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    manager = PathsDatManager(paths_dat)

    with pytest.raises(ValueError, match="No entry named"):
        manager.make_local("NonExistent", dest_dir)


def test_paths_dat_manager_make_local_missing_source(tmp_path: Path) -> None:
    """Test that make_local raises FileNotFoundError for missing source."""
    paths_dat = tmp_path / "paths.dat"
    paths_dat.write_text('Name1 "/nonexistent/file.dat"\n')

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    manager = PathsDatManager(paths_dat)

    with pytest.raises(FileNotFoundError, match="Source path not found"):
        manager.make_local("Name1", dest_dir)
