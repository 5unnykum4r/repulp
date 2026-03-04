# repulp

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-162%20passing-brightgreen)]()

Parallel batch document conversion, watch mode, and structured extraction — powered by [MarkItDown](https://github.com/microsoft/markitdown).

repulp wraps Microsoft's MarkItDown with a production workflow layer: parallel batch processing, incremental caching, file watching, table extraction, and a rich CLI.

## Why repulp?

MarkItDown converts files one at a time. repulp adds everything you need for real-world document pipelines:

| Feature | MarkItDown | repulp |
|---------|-----------|--------|
| Single file conversion | Yes | Yes |
| Parallel batch conversion | No | Yes (ProcessPoolExecutor) |
| Incremental cache (skip unchanged) | No | Yes (SHA256 hashing) |
| Watch mode (auto-convert on save) | No | Yes (watchfiles) |
| Extract tables as DataFrames/CSV | No | Yes |
| CLI with progress bars | No | Yes (Rich + Typer) |
| Config files (`.repulp.toml`) | No | Yes |

## Supported Formats

PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS, CSV, HTML, TXT, MD, RST, JSON, XML, YAML, images (JPEG, PNG, GIF, BMP, TIFF, WEBP), audio (MP3, WAV, FLAC), and more via MarkItDown.

> **Note:** Formats like HTML, CSV, PDF, DOCX, PPTX, and XLSX produce the richest Markdown output. Plain text formats (TXT, JSON, YAML, XML, RST) are passed through with minimal transformation by the underlying MarkItDown engine.

## Quick Start

```bash
pip install repulp
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add repulp
```

**Convert a directory with parallel workers:**

```bash
repulp convert ./documents --workers 4 --output ./markdown
```

**Watch a folder and auto-convert on changes:**

```bash
repulp watch ./incoming --output ./converted
```

**Extract tables from a PDF as CSV:**

```bash
repulp extract tables report.pdf --format csv --output ./tables
```

## CLI Reference

### `repulp convert`

Convert files, directories, or URLs to Markdown.

```bash
# Single file
repulp convert report.pdf

# Directory with parallel workers
repulp convert ./docs --workers 4 --output ./markdown

# Recursive with filters
repulp convert ./docs -r --include "*.pdf,*.docx" --exclude "*.tmp"

# Incremental (skip unchanged files, enabled by default)
repulp convert ./docs
repulp convert ./docs  # second run skips unchanged files

# Force reconvert all
repulp convert ./docs --no-cache

# URL
repulp convert https://example.com/page

# Stdin
cat file.html | repulp convert -

# Output to stdout
repulp convert report.pdf --stdout

# With frontmatter metadata
repulp convert report.pdf --frontmatter

# Different output formats
repulp convert report.pdf --format text
repulp convert report.pdf --format json
```

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output directory |
| `--recursive` | `-r` | Scan subdirectories |
| `--workers` | `-w` | Parallel workers (0 = auto) |
| `--no-cache` | | Disable incremental cache |
| `--include` | `-I` | Glob patterns to include |
| `--exclude` | `-E` | Glob patterns to exclude |
| `--stdout` | `-s` | Print to stdout |
| `--frontmatter` | `-f` | Add YAML frontmatter |
| `--format` | `-F` | Output format: md, text, json |
| `--no-clean` | | Skip markdown post-processing |

### `repulp watch`

Watch a directory and auto-convert on file changes.

```bash
repulp watch ./incoming --output ./converted
repulp watch ./docs --include "*.pdf" --debounce 1000
repulp watch ./docs --on-change "echo converted"
```

| Option | Description |
|--------|-------------|
| `--output` / `-o` | Output directory |
| `--include` / `-I` | Glob patterns to include |
| `--exclude` / `-E` | Glob patterns to exclude |
| `--no-clean` | Skip markdown cleanup |
| `--debounce` | Debounce interval in ms (default: 500) |
| `--on-change` | Shell command after each conversion |

### `repulp extract`

Extract structured elements from documents.

```bash
# Tables as CSV
repulp extract tables report.pdf --format csv

# Tables as JSON
repulp extract tables report.pdf --format json

# Save tables to files
repulp extract tables report.pdf --format csv --output ./tables

# Links
repulp extract links page.html
repulp extract links page.html --format json

# Headings
repulp extract headings report.pdf

# Images
repulp extract images document.docx
```

## Python API

```python
import repulp

# Convert a single file
result = repulp.convert("report.pdf")
print(result.markdown)

# Convert with options
result = repulp.convert("report.pdf", frontmatter=True, format="json")

# Batch convert a directory
result = repulp.batch("./documents", workers=4, recursive=True)
print(f"{result.succeeded}/{result.total} converted in {result.elapsed:.1f}s")

# Incremental batch (skip unchanged)
result = repulp.batch("./documents", incremental=True)
print(f"{result.skipped} skipped, {result.succeeded} converted")

# Extract tables as list of dicts
tables = repulp.extract_tables("report.pdf")
for table in tables:
    for row in table:
        print(row)

# Extract tables as pandas DataFrames
tables = repulp.extract_tables("report.pdf", format="dataframe")
df = tables[0]

# Extract tables as CSV strings
tables = repulp.extract_tables("report.pdf", format="csv")

# Watch a directory
repulp.watch("./incoming", output_dir="./converted")
```

### DataFrame Support

Install with the `tables` extra for pandas DataFrame support:

```bash
pip install repulp[tables]
```

```python
import repulp

tables = repulp.extract_tables("financials.xlsx", format="dataframe")
df = tables[0]
print(df.describe())
df.to_csv("output.csv", index=False)
```

## Configuration

Create `.repulp.toml` in your project root:

```toml
[repulp]
output_dir = "./markdown"
recursive = true
clean = true
workers = 0          # 0 = auto (CPU count - 1)
include = ["*.pdf", "*.docx", "*.pptx"]
exclude = ["*.tmp"]
```

Or use `[tool.repulp]` in `pyproject.toml`:

```toml
[tool.repulp]
output_dir = "./markdown"
recursive = true
```

CLI flags override config file values.

## Architecture

```
src/repulp/
├── __init__.py       # Public API: convert(), batch(), extract_tables(), watch()
├── cli.py            # Typer CLI with convert, watch, extract subcommands
├── converter.py      # MarkItDown wrapper for single-file conversion
├── engine.py         # Parallel batch engine (ProcessPoolExecutor)
├── cache.py          # Incremental build cache (SHA256 file hashing)
├── watcher.py        # File watcher (watchfiles) for auto-conversion
├── extractor.py      # Table, link, heading, image extraction from Markdown
├── cleaner.py        # Markdown post-processing and cleanup
├── config.py         # TOML config file loading (.repulp.toml / pyproject.toml)
├── fetcher.py        # URL fetching via httpx
├── frontmatter.py    # YAML frontmatter injection
└── formatter.py      # Output format handling (md, text, json)
```

## Libraries Used

repulp is built on top of these libraries:

| Library | Purpose |
|---------|---------|
| [MarkItDown](https://github.com/microsoft/markitdown) | Core document-to-Markdown conversion engine by Microsoft. Handles PDF, DOCX, PPTX, XLSX, HTML, CSV, images, audio, and more. |
| [Typer](https://typer.tiangolo.com/) | CLI framework built on Click. Provides argument parsing, help generation, and shell completion. |
| [Rich](https://rich.readthedocs.io/) | Terminal formatting — progress bars, tables, panels, colored output. |
| [watchfiles](https://watchfiles.helpmanual.io/) | Rust-backed file watcher. Used for the `watch` command to detect file changes with low latency. |
| [httpx](https://www.python-httpx.org/) | HTTP client for URL fetching. Used when converting URLs to Markdown. |
| [pandas](https://pandas.pydata.org/) | *(optional)* DataFrame support for structured table extraction. Install with `pip install repulp[tables]`. |
| [tomli](https://github.com/hukkin/tomli) | TOML parser for `.repulp.toml` config files. Only needed on Python < 3.11 (3.11+ has `tomllib` in stdlib). |

### Build & Dev Tools

| Tool | Purpose |
|------|---------|
| [hatchling](https://hatch.pypa.io/) | Build backend for packaging |
| [uv](https://docs.astral.sh/uv/) | Fast Python package manager |
| [pytest](https://docs.pytest.org/) | Test framework (162 tests) |

## Contributing

Contributions are welcome! Here's how to get started:

### Setup

```bash
git clone https://github.com/5unnykum4r/repulp.git
cd repulp
uv sync --group dev
```

### Running Tests

```bash
uv run pytest tests/ -v
```

### Project Conventions

- **Python 3.10+** — uses `from __future__ import annotations` for modern type hints
- **No vague comments** — code should be self-documenting; comments explain *why*, not *what*
- **Tests live in `tests/`** — mirror the source structure (e.g., `test_engine.py` tests `engine.py`)
- **Incremental commits** — one logical change per commit

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Write tests for your changes
4. Make sure all tests pass (`uv run pytest tests/ -v`)
5. Commit your changes with a descriptive message
6. Push to your fork and open a Pull Request

### Areas for Contribution

- Adding support for new output formats
- Performance improvements to the batch engine
- Better error messages and diagnostics
- Documentation improvements
- New extraction types (e.g., code blocks, footnotes)

## Samples

The `samples/` directory contains example files (HTML, CSV) that demonstrate repulp's conversion capabilities:

```bash
# Convert all samples
repulp convert samples/ --output samples/converted --workers 4 --no-cache

# Extract tables from a sample
repulp extract tables samples/architecture.html --format json
```

## License

[MIT](LICENSE) — Sunny Kumar
