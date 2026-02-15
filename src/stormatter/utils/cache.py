from __future__ import annotations

import hashlib
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Tuple


# (mtime, size, sha256)
FileInfo = Tuple[float, int, str]


def file_hash(path: Path) -> str:
    """Compute a SHA-256 hash of the file contents."""
    data: bytes = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def get_file_info(path: Path) -> FileInfo:
    """Return (mtime, size, hash) for a file."""
    stat = path.stat()
    return (stat.st_mtime, stat.st_size, file_hash(path))


@dataclass
class Cache:
    cache_file: Path
    data: Dict[str, FileInfo] = field(default_factory=lambda: {})

    @classmethod
    def load(cls, cache_file: Path) -> "Cache":
        """Load cache from disk, or return an empty cache if missing/corrupt."""
        if not cache_file.exists():
            return cls(cache_file)

        try:
            with cache_file.open("rb") as f:
                loaded: Dict[str, FileInfo] = pickle.load(f)
        except Exception:
            return cls(cache_file)

        # Ensure values are FileInfo tuples
        typed_data: Dict[str, FileInfo] = {}
        for k, v in loaded.items():
            typed_data[k] = v

        return cls(cache_file, typed_data)

    def is_changed(self, path: Path) -> bool:
        """Return True if the file has changed since last cached."""
        key = str(path.resolve())
        old: FileInfo | None = self.data.get(key)

        if old is None:
            return True

        old_mtime, old_size, old_hash = old
        stat = path.stat()

        # Fast checks
        if stat.st_size != old_size:
            return True
        if stat.st_mtime != old_mtime:
            # Confirm with hash
            new_hash = file_hash(path)
            if new_hash != old_hash:
                return True

        return False

    def update(self, paths: Iterable[Path]) -> None:
        """Update cache entries for the given paths."""
        for p in paths:
            self.data[str(p.resolve())] = get_file_info(p)

    def save(self) -> None:
        """Write cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_file.open("wb") as f:
            pickle.dump(self.data, f, protocol=4)
