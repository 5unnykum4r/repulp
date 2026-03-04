from pathlib import Path

from typer.testing import CliRunner

from repulp.cli import app


runner = CliRunner()

FIXTURES = Path(__file__).parent / "fixtures"


class TestConvertCommand:
    def test_convert_single_file(self):
        result = runner.invoke(app, ["convert", str(FIXTURES / "sample.txt")])
        assert result.exit_code == 0

    def test_convert_directory(self):
        result = runner.invoke(app, ["convert", str(FIXTURES)])
        assert result.exit_code == 0

    def test_convert_to_stdout(self):
        result = runner.invoke(app, ["convert", str(FIXTURES / "sample.txt"), "--stdout"])
        assert result.exit_code == 0
        assert "Hello World" in result.output

    def test_convert_with_output_dir(self, tmp_path: Path):
        result = runner.invoke(app, [
            "convert", str(FIXTURES / "sample.txt"),
            "-o", str(tmp_path),
        ])
        assert result.exit_code == 0
        output_files = list(tmp_path.glob("*.md"))
        assert len(output_files) == 1

    def test_convert_nonexistent_path(self):
        result = runner.invoke(app, ["convert", "/tmp/nonexistent_abc123"])
        assert result.exit_code != 0 or "Error" in result.output or "not found" in result.output.lower()

    def test_convert_with_no_clean(self):
        result = runner.invoke(app, [
            "convert", str(FIXTURES / "sample.txt"), "--no-clean", "--stdout"
        ])
        assert result.exit_code == 0

    def test_convert_recursive(self, tmp_path: Path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "test.txt").write_text("Nested file content")

        result = runner.invoke(app, ["convert", str(tmp_path), "--recursive"])
        assert result.exit_code == 0

    def test_convert_with_include_filter(self):
        result = runner.invoke(app, [
            "convert", str(FIXTURES), "--include", "*.csv"
        ])
        assert result.exit_code == 0

    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
