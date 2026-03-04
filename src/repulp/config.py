from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class RepulpConfig:
    output_dir: str = ""
    recursive: bool = False
    clean: bool = True
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    def merge_cli_overrides(
        self,
        output_dir: Optional[str] = None,
        recursive: Optional[bool] = None,
        clean: Optional[bool] = None,
        include: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
    ) -> RepulpConfig:
        return RepulpConfig(
            output_dir=output_dir if output_dir is not None else self.output_dir,
            recursive=recursive if recursive is not None else self.recursive,
            clean=clean if clean is not None else self.clean,
            include=include if include is not None else self.include,
            exclude=exclude if exclude is not None else self.exclude,
        )


def _parse_toml_file(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config(search_dir: Optional[Path] = None) -> RepulpConfig:
    search_dir = Path(search_dir) if search_dir else Path.cwd()

    # .repulp.toml takes precedence over pyproject.toml
    dotfile = search_dir / ".repulp.toml"
    if dotfile.exists():
        data = _parse_toml_file(dotfile)
        section = data.get("repulp", {})
        return RepulpConfig(**{
            k: v for k, v in section.items()
            if k in RepulpConfig.__dataclass_fields__
        })

    # Fall back to pyproject.toml [tool.repulp] section
    pyproject = search_dir / "pyproject.toml"
    if pyproject.exists():
        data = _parse_toml_file(pyproject)
        section = data.get("tool", {}).get("repulp", {})
        if section:
            return RepulpConfig(**{
                k: v for k, v in section.items()
                if k in RepulpConfig.__dataclass_fields__
            })

    # No config file found; return defaults
    return RepulpConfig()
