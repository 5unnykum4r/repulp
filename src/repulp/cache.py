"""Incremental build cache for repulp.

Tracks SHA256 hashes of source files so that batch_convert() can skip
files that have not changed since the last successful conversion.
The cache is persisted as a JSON file (typically `.repulp.cache` inside
the source directory).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional


class ConversionCache:
    """File-hash cache that detects which source files have changed.

    Keys are resolved absolute path strings; values are hex-encoded SHA256
    digests of the file contents at the time of last successful conversion.
    """

    def __init__(self, cache_path: Path) -> None:
        self._cache_path = Path(cache_path)
        self._hashes: dict[str, str] = {}

        if self._cache_path.exists():
            try:
                self._hashes = json.loads(self._cache_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._hashes = {}

    @staticmethod
    def _hash_file(path: Path) -> Optional[str]:
        """Return the SHA256 hex digest of *path*'s contents, or None if unreadable."""
        try:
            data = Path(path).resolve().read_bytes()
            return hashlib.sha256(data).hexdigest()
        except (OSError, PermissionError):
            return None

    def is_changed(self, path: Path) -> bool:
        """Return True if *path* has changed since the last cached conversion.

        A file is considered changed when:
        - It has never been cached before.
        - Its current SHA256 hash differs from the stored hash.
        - The file no longer exists (hash returns None).
        """
        key = str(Path(path).resolve())
        current_hash = self._hash_file(path)
        if current_hash is None:
            return True
        return self._hashes.get(key) != current_hash

    def mark_converted(self, path: Path) -> None:
        """Record the current SHA256 hash for *path* as the latest converted state."""
        key = str(Path(path).resolve())
        file_hash = self._hash_file(path)
        if file_hash is not None:
            self._hashes[key] = file_hash

    def partition(self, files: list[Path]) -> tuple[list[Path], list[Path]]:
        """Split *files* into (changed, unchanged) based on cached hashes.

        Args:
            files: List of file paths to check.

        Returns:
            A 2-tuple of (changed_files, unchanged_files).
        """
        changed: list[Path] = []
        unchanged: list[Path] = []
        for f in files:
            if self.is_changed(f):
                changed.append(f)
            else:
                unchanged.append(f)
        return changed, unchanged

    def save(self) -> None:
        """Persist the hash cache to disk as JSON."""
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_path.write_text(
            json.dumps(self._hashes, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
