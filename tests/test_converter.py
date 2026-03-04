import os
from pathlib import Path

import pytest

from repulp.converter import ConversionResult, convert_file, convert_directory, SUPPORTED_EXTENSIONS


FIXTURES = Path(__file__).parent / "fixtures"


class TestSupportedExtensions:
    def test_common_formats_present(self):
        assert ".pdf" in SUPPORTED_EXTENSIONS
        assert ".docx" in SUPPORTED_EXTENSIONS
        assert ".pptx" in SUPPORTED_EXTENSIONS
        assert ".xlsx" in SUPPORTED_EXTENSIONS
        assert ".html" in SUPPORTED_EXTENSIONS
        assert ".csv" in SUPPORTED_EXTENSIONS

    def test_unknown_format_not_present(self):
        assert ".xyz123" not in SUPPORTED_EXTENSIONS


class TestConvertFile:
    def test_convert_txt_file(self):
        result = convert_file(FIXTURES / "sample.txt")
        assert result.success is True
        assert "Hello World" in result.markdown
        assert result.source_path == FIXTURES / "sample.txt"
        assert result.error is None

    def test_convert_html_file(self):
        result = convert_file(FIXTURES / "sample.html")
        assert result.success is True
        assert "Title" in result.markdown
        assert "Hello from HTML" in result.markdown

    def test_convert_csv_file(self):
        result = convert_file(FIXTURES / "sample.csv")
        assert result.success is True
        assert "Alice" in result.markdown
        assert "Bob" in result.markdown

    def test_convert_nonexistent_file(self):
        result = convert_file(Path("/tmp/nonexistent_file_abc123.pdf"))
        assert result.success is False
        assert result.error is not None

    def test_convert_with_clean_enabled(self):
        result = convert_file(FIXTURES / "sample.html", clean=True)
        assert result.success is True
        assert "\n\n\n" not in result.markdown


class TestConvertDirectory:
    def test_convert_fixtures_directory(self):
        results = convert_directory(FIXTURES, recursive=False)
        assert len(results) >= 3
        successes = [r for r in results if r.success]
        assert len(successes) >= 3

    def test_convert_with_include_filter(self):
        results = convert_directory(FIXTURES, include=["*.csv"])
        assert len(results) == 1
        assert results[0].source_path.suffix == ".csv"

    def test_convert_with_exclude_filter(self):
        results = convert_directory(FIXTURES, exclude=["*.csv"])
        csv_results = [r for r in results if r.source_path.suffix == ".csv"]
        assert len(csv_results) == 0

    def test_convert_empty_directory(self, tmp_path: Path):
        results = convert_directory(tmp_path)
        assert results == []
