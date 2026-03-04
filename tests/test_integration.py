from pathlib import Path

from typer.testing import CliRunner

from repulp.cli import app

runner = CliRunner()


class TestEndToEnd:
    def test_full_pipeline_single_file(self, tmp_path: Path):
        source = tmp_path / "input.html"
        source.write_text("<h1>Hello</h1><p>World</p>")
        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "convert", str(source), "-o", str(output_dir),
        ])

        assert result.exit_code == 0
        md_file = output_dir / "input.md"
        assert md_file.exists()
        content = md_file.read_text()
        assert "Hello" in content
        assert "World" in content

    def test_full_pipeline_directory_recursive(self, tmp_path: Path):
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "a" / "doc.html").write_text("<h1>Doc A</h1>")
        (tmp_path / "a" / "b" / "doc.html").write_text("<h1>Doc B</h1>")

        output_dir = tmp_path / "output"

        result = runner.invoke(app, [
            "convert", str(tmp_path / "a"),
            "-o", str(output_dir),
            "--recursive",
        ])

        assert result.exit_code == 0
        assert (output_dir / "doc.md").exists()
        assert (output_dir / "b" / "doc.md").exists()

    def test_full_pipeline_stdout(self, tmp_path: Path):
        source = tmp_path / "test.csv"
        source.write_text("name,score\nAlice,95\nBob,87")

        result = runner.invoke(app, ["convert", str(source), "--stdout"])
        assert result.exit_code == 0
        assert "Alice" in result.output
        assert "Bob" in result.output

    def test_full_pipeline_with_include_filter(self, tmp_path: Path):
        (tmp_path / "keep.html").write_text("<p>Keep</p>")
        (tmp_path / "skip.csv").write_text("a,b\n1,2")

        output_dir = tmp_path / "output"
        result = runner.invoke(app, [
            "convert", str(tmp_path),
            "-o", str(output_dir),
            "--include", "*.html",
        ])

        assert result.exit_code == 0
        assert (output_dir / "keep.md").exists()
        assert not (output_dir / "skip.md").exists()
