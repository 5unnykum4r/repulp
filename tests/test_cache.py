"""Tests for repulp.cache — incremental build cache."""

import json
from pathlib import Path

import pytest

from repulp.cache import ConversionCache


class TestConversionCache:
    """Verify ConversionCache hash-tracking and persistence behaviour."""

    def test_new_cache_is_changed_returns_true(self, tmp_path: Path):
        """A fresh cache should report every file as changed."""
        cache = ConversionCache(tmp_path / ".repulp.cache")
        sample = tmp_path / "doc.txt"
        sample.write_text("hello world")
        assert cache.is_changed(sample) is True

    def test_mark_converted_save_reload_unchanged(self, tmp_path: Path):
        """After mark_converted + save, a reloaded cache sees the file as unchanged."""
        cache_path = tmp_path / ".repulp.cache"
        sample = tmp_path / "doc.txt"
        sample.write_text("hello world")

        cache = ConversionCache(cache_path)
        cache.mark_converted(sample)
        cache.save()

        cache2 = ConversionCache(cache_path)
        assert cache2.is_changed(sample) is False

    def test_modified_file_detected_as_changed(self, tmp_path: Path):
        """Modifying file contents after caching should be detected."""
        cache_path = tmp_path / ".repulp.cache"
        sample = tmp_path / "doc.txt"
        sample.write_text("original content")

        cache = ConversionCache(cache_path)
        cache.mark_converted(sample)
        cache.save()

        sample.write_text("modified content")

        cache2 = ConversionCache(cache_path)
        assert cache2.is_changed(sample) is True

    def test_deleted_file_detected_as_changed(self, tmp_path: Path):
        """A file that existed when cached but has been deleted is reported as changed."""
        cache_path = tmp_path / ".repulp.cache"
        sample = tmp_path / "doc.txt"
        sample.write_text("some data")

        cache = ConversionCache(cache_path)
        cache.mark_converted(sample)
        cache.save()

        sample.unlink()

        cache2 = ConversionCache(cache_path)
        assert cache2.is_changed(sample) is True

    def test_cache_file_is_valid_json(self, tmp_path: Path):
        """The persisted cache file must be parseable JSON."""
        cache_path = tmp_path / ".repulp.cache"
        sample = tmp_path / "a.txt"
        sample.write_text("data")

        cache = ConversionCache(cache_path)
        cache.mark_converted(sample)
        cache.save()

        raw = cache_path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)
        assert len(parsed) == 1
        key = list(parsed.keys())[0]
        assert key == str(sample.resolve())
        assert isinstance(parsed[key], str)
        assert len(parsed[key]) == 64  # SHA256 hex digest length

    def test_partition_splits_changed_and_unchanged(self, tmp_path: Path):
        """partition() should correctly categorise files."""
        cache_path = tmp_path / ".repulp.cache"
        unchanged_file = tmp_path / "old.txt"
        changed_file = tmp_path / "new.txt"
        unchanged_file.write_text("stable")
        changed_file.write_text("original")

        cache = ConversionCache(cache_path)
        cache.mark_converted(unchanged_file)
        cache.mark_converted(changed_file)
        cache.save()

        changed_file.write_text("updated")

        cache2 = ConversionCache(cache_path)
        changed, unchanged = cache2.partition([unchanged_file, changed_file])

        assert unchanged_file in unchanged
        assert changed_file in changed
        assert len(changed) == 1
        assert len(unchanged) == 1

    def test_partition_all_new_files(self, tmp_path: Path):
        """partition() with an empty cache returns all files as changed."""
        cache = ConversionCache(tmp_path / ".repulp.cache")
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("aaa")
        f2.write_text("bbb")

        changed, unchanged = cache.partition([f1, f2])
        assert len(changed) == 2
        assert len(unchanged) == 0

    def test_corrupt_cache_file_treated_as_empty(self, tmp_path: Path):
        """If the cache file contains invalid JSON, it should be treated as empty."""
        cache_path = tmp_path / ".repulp.cache"
        cache_path.write_text("not valid json {{{")

        sample = tmp_path / "doc.txt"
        sample.write_text("data")

        cache = ConversionCache(cache_path)
        assert cache.is_changed(sample) is True
