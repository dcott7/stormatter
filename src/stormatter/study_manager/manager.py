from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from .paths_parser import PathsDatParser


class PathsDatHistory:
    """Class for file based tracking changes to paths.dat file."""

    def __init__(self, history_path: Optional[Path] = None) -> None:
        self.history_path = history_path or (Path.home() / ".paths_history.json")
        self.data: Dict[str, Dict[str, List[Dict[str, str | float]]]] = {}
        self.load()

    def load(self) -> None:
        if not self.history_path.exists():
            self.data = {}
            return

        try:
            raw = self.history_path.read_text(encoding="utf-8")
            self.data = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            self.data = {}

    def save(self) -> None:
        self.history_path.write_text(
            json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8"
        )

    def get_file_history(
        self, paths_dat_path: Path
    ) -> Dict[str, List[Dict[str, str | float]]]:
        key = str(paths_dat_path.resolve())
        if key not in self.data:
            self.data[key] = {}
        return self.data[key]

    def record(
        self,
        paths_dat_path: Path,
        name: str,
        path: Path,
        timestamp: Optional[float] = None,
    ) -> None:
        file_history = self.get_file_history(paths_dat_path)
        if name not in file_history:
            file_history[name] = []

        entries = file_history[name]
        path_value = str(path)
        if entries and entries[-1].get("path") == path_value:
            return

        entries.append(
            {
                "timestamp": timestamp if timestamp is not None else time.time(),
                "path": path_value,
            }
        )

    def update_from_paths(
        self,
        paths_dat_path: Path,
        paths: Dict[str, Path],
        timestamp: Optional[float] = None,
    ) -> None:
        file_history = self.get_file_history(paths_dat_path)
        for name, path in paths.items():
            if name not in file_history:
                file_history[name] = []
            self.record(paths_dat_path, name, path, timestamp)
        self.save()

    def get_last_update(
        self, paths_dat_path: Path, name: str
    ) -> Optional[Dict[str, str | float]]:
        """
        Return the last update entry for a given name in paths.dat, or
        None if no history.
        """
        file_history = self.get_file_history(paths_dat_path)
        entries = file_history.get(name, [])
        if not entries:
            return None
        return entries[-1]

    def get_last_path(self, paths_dat_path: Path, name: str) -> Optional[Path]:
        """Return the last path for a given name in paths.dat, or None if no history."""
        last = self.get_last_update(paths_dat_path, name)
        if last is None:
            return None
        value = last.get("path")
        return Path(value).resolve() if isinstance(value, str) else None

    def get_last_timestamp(self, paths_dat_path: Path, name: str) -> Optional[float]:
        """Return the last timestamp for a given name in paths.dat, or None if no history."""
        last = self.get_last_update(paths_dat_path, name)
        if last is None:
            return None
        value = last.get("timestamp")
        return float(value) if value is not None else None

    def get_latest_snapshot(self, paths_dat_path: Path) -> Dict[str, Path]:
        """Return a snapshot of the latest paths for all names in paths.dat based on history."""
        file_history = self.get_file_history(paths_dat_path)
        snapshot: Dict[str, Path] = {}
        for name, entries in file_history.items():
            if not entries:
                continue
            value = entries[-1].get("path")
            if isinstance(value, str):
                snapshot[name] = Path(value).resolve()
        return snapshot


class PathsDatManager:
    """Manager class for handling paths.dat file operations."""

    def __init__(
        self,
        paths_dat_path: Path,
        history: Optional[PathsDatHistory] = None,
    ) -> None:
        self.paths_dat_path = paths_dat_path
        self.history = history or PathsDatHistory()

    def get_paths(self, track_history: bool = True) -> Dict[str, Path]:
        """Get the parsed paths from the paths.dat file."""
        source = self.paths_dat_path.read_text(encoding="utf-8")
        parser = PathsDatParser(source)
        paths = parser.parse()

        if track_history:
            self.history.update_from_paths(self.paths_dat_path, paths)

        return paths

    def make_local(self, name: str, destination_dir: Path) -> None:
        """
        Copy a single file to the local directory and update paths.dat/history.
        """
        destination_dir = Path(destination_dir).resolve()
        if not destination_dir.is_dir():
            raise NotADirectoryError(
                f"Destination must be a directory: {destination_dir}"
            )

        current_paths = self.get_paths(track_history=False)
        if name not in current_paths:
            raise ValueError(f"No entry named '{name}' in paths.dat")

        source_path = Path(current_paths[name]).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source path not found for {name}: {source_path}")

        destination = destination_dir / source_path.name
        destination.write_bytes(source_path.read_bytes())  # copy content

        current_paths[name] = destination.resolve()  # update to new local path
        self._write_paths_dat(current_paths)
        self.history.update_from_paths(self.paths_dat_path, current_paths)

    def revert_last_change(self) -> None:
        """
        Revert the last change made to the paths.dat file. This does NOT
        remove the file that was copied to the local directory, but it will
        update paths.dat to point back to the previous path and record that
        change in the history.
        """
        file_history = self.history.get_file_history(self.paths_dat_path)
        if not file_history:
            return

        current_paths = self.get_paths(track_history=False)
        updated_any = False

        for name, entries in file_history.items():
            if len(entries) < 2:
                continue
            previous_path = entries[-2].get("path")
            if not isinstance(previous_path, str):
                continue
            current_paths[name] = Path(previous_path).resolve()
            updated_any = True

        if not updated_any:
            return

        self._write_paths_dat(current_paths)
        self.history.update_from_paths(self.paths_dat_path, current_paths)

    def revert_last_change_for_file(self, name: str) -> None:
        """
        Revert the last change made to a specific file in paths.dat. This does
        NOT remove the file that was copied to the local directory, but it will
        update paths.dat to point back to the previous path and record that
        change in the history.
        """
        file_history = self.history.get_file_history(self.paths_dat_path)
        if name not in file_history or len(file_history[name]) < 2:
            return

        previous_path = file_history[name][-2].get("path")
        if not isinstance(previous_path, str):
            return

        current_paths = self.get_paths(track_history=False)
        current_paths[name] = Path(previous_path).resolve()

        self._write_paths_dat(current_paths)
        self.history.update_from_paths(self.paths_dat_path, current_paths)

    def _write_paths_dat(self, paths: Dict[str, Path]) -> None:
        parser = PathsDatParser("")
        parser.data = paths
        parser.write(self.paths_dat_path)


class StudyManager:
    """"""

    def __init__(self) -> None:
        pass
