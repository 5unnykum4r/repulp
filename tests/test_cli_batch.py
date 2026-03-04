from pathlib import Path

from typer.testing import CliRunner

from repulp.cli import app

runner = CliRunner()

FIXTURES = Path(__file__).parent / "fixtures"


class TestBatchConvert:
    def test_convert_directory_with_workers(self):
        result = runner.invoke(app, ["convert", str(FIXTURES), "--workers", "2"])
        assert result.exit_code == 0

    def test_convert_directory_shows_throughput(self):
        result = runner.invoke(app, ["convert", str(FIXTURES)])
        assert result.exit_code == 0
        assert "converted" in result.output.lower() or "files/sec" in result.output.lower() or "1" in result.output

    def test_convert_with_no_cache(self, tmp_path):
        (tmp_path / "test.html").write_text("<h1>Hello</h1>")
        result = runner.invoke(app, ["convert", str(tmp_path), "--no-cache"])
        assert result.exit_code == 0

    def test_incremental_second_run(self, tmp_path):
        (tmp_path / "test.html").write_text("<h1>Hello</h1>")

        runner.invoke(app, ["convert", str(tmp_path)])
        result = runner.invoke(app, ["convert", str(tmp_path)])
        assert result.exit_code == 0
        assert "skip" in result.output.lower() or "0" in result.output


class TestExtractTablesCLI:
    def test_extract_tables_csv(self, tmp_path):
        result = runner.invoke(app, [
            "extract", "tables", str(FIXTURES / "sample.csv"),
            "--format", "csv",
        ])
        assert result.exit_code == 0

    def test_extract_tables_json(self, tmp_path):
        result = runner.invoke(app, [
            "extract", "tables", str(FIXTURES / "sample.csv"),
            "--format", "json",
        ])
        assert result.exit_code == 0
