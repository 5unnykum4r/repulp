"""Tests for repulp.engine — parallel batch conversion engine."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from repulp.converter import ConversionResult
from repulp.engine import BatchResult, batch_convert, _collect_files


FIXTURES = Path(__file__).parent / "fixtures"


class TestBatchResult:
    """Verify BatchResult dataclass fields exist with correct types."""

    def test_default_fields(self):
        br = BatchResult()
        assert br.results == []
        assert br.total == 0
        assert br.succeeded == 0
        assert br.failed == 0
        assert br.skipped == 0
        assert br.elapsed == 0.0
        assert br.throughput == 0.0

    def test_fields_accept_values(self):
        dummy = ConversionResult(source_path=Path("a.txt"), markdown="hi", success=True)
        br = BatchResult(
            results=[dummy],
            total=1,
            succeeded=1,
            failed=0,
            skipped=0,
            elapsed=2.5,
            throughput=0.4,
        )
        assert isinstance(br.results, list)
        assert isinstance(br.total, int)
        assert isinstance(br.succeeded, int)
        assert isinstance(br.failed, int)
        assert isinstance(br.skipped, int)
        assert isinstance(br.elapsed, float)
        assert isinstance(br.throughput, float)
        assert br.results[0] is dummy


class TestCollectFiles:
    """Verify _collect_files filtering logic."""

    def test_collects_all_supported(self):
        files = _collect_files(FIXTURES)
        assert len(files) == 4

    def test_include_filter(self):
        files = _collect_files(FIXTURES, include=["*.csv"])
        assert len(files) == 1
        assert files[0].name == "sample.csv"

    def test_exclude_filter(self):
        files = _collect_files(FIXTURES, exclude=["*.csv", "*.md"])
        names = {f.name for f in files}
        assert "sample.csv" not in names
        assert "sample.md" not in names
        assert len(files) == 2

    def test_empty_dir(self, tmp_path: Path):
        files = _collect_files(tmp_path)
        assert files == []

    def test_nonexistent_dir(self):
        files = _collect_files(Path("/tmp/nonexistent_dir_engine_test_xyz"))
        assert files == []


class TestBatchConvert:
    """Integration tests for batch_convert()."""

    def test_converts_all_fixtures(self):
        br = batch_convert(FIXTURES, workers=1, incremental=False)
        assert br.total == 4
        assert br.succeeded == 4
        assert br.failed == 0
        assert br.skipped == 0
        assert len(br.results) == 4
        assert br.elapsed > 0
        assert br.throughput > 0

    def test_respects_include_filter(self):
        br = batch_convert(FIXTURES, include=["*.txt"], workers=1, incremental=False)
        assert br.total == 1
        assert br.succeeded == 1
        assert br.results[0].source_path.name == "sample.txt"

    def test_respects_exclude_filter(self):
        br = batch_convert(FIXTURES, exclude=["*.csv"], workers=1, incremental=False)
        csv_results = [r for r in br.results if r.source_path.suffix == ".csv"]
        assert len(csv_results) == 0
        assert br.total == 3

    def test_empty_directory(self, tmp_path: Path):
        br = batch_convert(tmp_path, workers=1)
        assert br.total == 0
        assert br.succeeded == 0
        assert br.failed == 0
        assert br.elapsed == 0.0
        assert br.throughput == 0.0
        assert br.results == []

    def test_nonexistent_directory(self):
        br = batch_convert(Path("/tmp/nonexistent_dir_engine_test_xyz"), workers=1)
        assert br.total == 0
        assert br.succeeded == 0
        assert br.results == []

    def test_workers_1_sequential(self):
        br = batch_convert(FIXTURES, workers=1, incremental=False)
        assert br.total == 4
        assert br.succeeded == 4
        # Results should preserve input order
        names = [r.source_path.name for r in br.results]
        assert names == sorted(names)

    def test_workers_2_parallel(self):
        br = batch_convert(FIXTURES, workers=2, incremental=False)
        assert br.total == 4
        assert br.succeeded == 4
        # Results must be re-sorted to match input order even with parallel execution
        names = [r.source_path.name for r in br.results]
        assert names == sorted(names)

    def test_clean_false(self):
        br = batch_convert(FIXTURES, clean=False, workers=1, incremental=False)
        assert br.total == 4
        assert br.succeeded == 4
        for r in br.results:
            assert r.success is True
            assert isinstance(r.markdown, str)

    def test_handles_bad_files_gracefully(self, tmp_path: Path):
        bad_file = tmp_path / "broken.html"
        bad_file.write_bytes(b"\x00\x01\x02\x03")
        br = batch_convert(tmp_path, workers=1)
        assert br.total == 1
        # The file may convert (MarkItDown is lenient) or fail; either way no exception
        assert len(br.results) == 1

    def test_on_progress_callback_called(self):
        callback = MagicMock()
        br = batch_convert(FIXTURES, workers=1, incremental=False, on_progress=callback)
        assert callback.call_count == br.total
        # Each call should receive (completed_int, total_int, ConversionResult)
        for call_args in callback.call_args_list:
            completed, total, result = call_args[0]
            assert isinstance(completed, int)
            assert total == br.total
            assert isinstance(result, ConversionResult)

    def test_on_progress_callback_parallel(self):
        callback = MagicMock()
        br = batch_convert(FIXTURES, workers=2, incremental=False, on_progress=callback)
        assert callback.call_count == br.total

    def test_results_order_matches_input(self):
        """Verify results are in the same sorted order as _collect_files returns."""
        br = batch_convert(FIXTURES, workers=2, incremental=False)
        collected = _collect_files(FIXTURES)
        result_paths = [r.source_path for r in br.results]
        assert result_paths == collected

    def test_incremental_parameter_accepted(self):
        """Both incremental=True and incremental=False are accepted without error."""
        br = batch_convert(FIXTURES, workers=1, incremental=False)
        assert br.total == 4
        assert br.skipped == 0


class TestIncrementalConversion:
    """Tests for incremental cache integration in batch_convert()."""

    def test_second_run_skips_unchanged(self, tmp_path: Path):
        """Running batch_convert twice with incremental=True skips unchanged files."""
        sample = tmp_path / "hello.txt"
        sample.write_text("hello world")

        br1 = batch_convert(tmp_path, workers=1, incremental=True)
        assert br1.total == 1
        assert br1.succeeded == 1
        assert br1.skipped == 0

        br2 = batch_convert(tmp_path, workers=1, incremental=True)
        assert br2.total == 1
        assert br2.succeeded == 0
        assert br2.skipped == 1

    def test_changed_file_reconverted(self, tmp_path: Path):
        """A file modified between runs is reconverted instead of skipped."""
        sample = tmp_path / "data.txt"
        sample.write_text("original content")

        br1 = batch_convert(tmp_path, workers=1, incremental=True)
        assert br1.succeeded == 1
        assert br1.skipped == 0

        sample.write_text("modified content")

        br2 = batch_convert(tmp_path, workers=1, incremental=True)
        assert br2.succeeded == 1
        assert br2.skipped == 0

    def test_no_cache_flag(self, tmp_path: Path):
        """With incremental=False, nothing is skipped even if a cache exists."""
        sample = tmp_path / "note.txt"
        sample.write_text("some text")

        # First run with incremental=True to populate the cache
        br1 = batch_convert(tmp_path, workers=1, incremental=True)
        assert br1.succeeded == 1

        # Second run with incremental=False ignores the cache entirely
        br2 = batch_convert(tmp_path, workers=1, incremental=False)
        assert br2.total == 1
        assert br2.succeeded == 1
        assert br2.skipped == 0
