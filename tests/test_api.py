from pathlib import Path

import pytest

from repulp import convert, batch, extract_tables


FIXTURES = Path(__file__).parent / "fixtures"


class TestConvertAPI:
    def test_convert_file(self):
        result = convert(FIXTURES / "sample.txt")
        assert result.success
        assert "Hello World" in result.markdown

    def test_convert_html(self):
        result = convert(FIXTURES / "sample.html")
        assert result.success
        assert "Title" in result.markdown

    def test_convert_with_frontmatter(self):
        result = convert(FIXTURES / "sample.html", frontmatter=True)
        assert result.success
        assert result.markdown.startswith("---\n")
        assert "title:" in result.markdown
        assert "word_count:" in result.markdown

    def test_convert_format_text(self):
        result = convert(FIXTURES / "sample.html", format="text")
        assert result.success
        assert "#" not in result.markdown
        assert "Title" in result.markdown

    def test_convert_format_json(self):
        import json
        result = convert(FIXTURES / "sample.html", format="json")
        assert result.success
        data = json.loads(result.markdown)
        assert "content" in data
        assert "structure" in data

    def test_convert_nonexistent(self):
        result = convert("/tmp/nonexistent_abc123.pdf")
        assert not result.success


class TestBatchAPI:
    def test_batch_fixtures(self):
        result = batch(FIXTURES)
        assert result.succeeded >= 3
        assert result.total >= 3

    def test_batch_with_workers(self):
        result = batch(FIXTURES, workers=1)
        assert result.succeeded >= 3

    def test_batch_with_include(self):
        result = batch(FIXTURES, include=["*.csv"])
        assert result.total == 1

    def test_batch_empty_dir(self, tmp_path):
        result = batch(tmp_path)
        assert result.total == 0


class TestExtractTablesAPI:
    def test_extract_from_csv(self):
        tables = extract_tables(FIXTURES / "sample.csv")
        assert len(tables) >= 1
        assert isinstance(tables[0], list)

    def test_extract_format_csv(self):
        tables = extract_tables(FIXTURES / "sample.csv", format="csv")
        assert len(tables) >= 1
        assert isinstance(tables[0], str)
        assert "," in tables[0]

    def test_extract_dataframe(self):
        pd = pytest.importorskip("pandas")
        tables = extract_tables(FIXTURES / "sample.csv", format="dataframe")
        assert len(tables) >= 1
        assert isinstance(tables[0], pd.DataFrame)
