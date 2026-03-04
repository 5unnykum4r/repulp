from pathlib import Path

from repulp.config import RepulpConfig, load_config


class TestRepulpConfig:
    def test_default_config(self):
        config = RepulpConfig()
        assert config.output_dir == ""
        assert config.recursive is False
        assert config.clean is True
        assert config.include == []
        assert config.exclude == []

    def test_load_from_toml_file(self, tmp_path: Path):
        toml_file = tmp_path / ".repulp.toml"
        toml_file.write_text('[repulp]\noutput_dir = "output"\nrecursive = true\n')
        config = load_config(search_dir=tmp_path)
        assert config.output_dir == "output"
        assert config.recursive is True

    def test_load_from_pyproject_toml(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.repulp]\noutput_dir = "from_pyproject"\n')
        config = load_config(search_dir=tmp_path)
        assert config.output_dir == "from_pyproject"

    def test_dotfile_takes_precedence_over_pyproject(self, tmp_path: Path):
        (tmp_path / ".repulp.toml").write_text('[repulp]\noutput_dir = "from_dotfile"\n')
        (tmp_path / "pyproject.toml").write_text('[tool.repulp]\noutput_dir = "from_pyproject"\n')
        config = load_config(search_dir=tmp_path)
        assert config.output_dir == "from_dotfile"

    def test_no_config_file_returns_defaults(self, tmp_path: Path):
        config = load_config(search_dir=tmp_path)
        assert config.output_dir == ""
        assert config.recursive is False

    def test_cli_overrides_merge(self):
        config = RepulpConfig(output_dir="original", recursive=False)
        merged = config.merge_cli_overrides(output_dir="override", recursive=True)
        assert merged.output_dir == "override"
        assert merged.recursive is True

    def test_cli_overrides_none_keeps_config_value(self):
        config = RepulpConfig(output_dir="keep_me", recursive=True)
        merged = config.merge_cli_overrides(output_dir=None, recursive=None)
        assert merged.output_dir == "keep_me"
        assert merged.recursive is True
