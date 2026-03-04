"""repulp — Parallel batch document conversion, watch mode, and structured extraction."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Optional, Union

__version__ = "0.1.0"


def convert(
    source: Union[str, Path],
    clean: bool = True,
    frontmatter: bool = False,
    format: str = "md",
) -> "ConversionResult":
    """Convert a file, URL, or path to Markdown.

    Args:
        source: File path, URL (http/https), or "-" for stdin.
        clean: Post-process the markdown output.
        frontmatter: Inject YAML frontmatter with metadata.
        format: Output format - "md", "text", or "json".

    Returns:
        ConversionResult with markdown content and metadata.
    """
    from repulp.converter import convert_file, convert_url, ConversionResult
    from repulp.fetcher import is_url
    from repulp.frontmatter import inject_frontmatter
    from repulp.formatter import format_output

    source_str = str(source)

    if source_str == "-":
        content = sys.stdin.buffer.read()
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
        tmp.write(content)
        tmp.close()
        try:
            result = convert_file(Path(tmp.name), clean=clean)
            result = ConversionResult(
                source_path=Path("stdin"),
                markdown=result.markdown,
                success=result.success,
                error=result.error,
            )
        finally:
            Path(tmp.name).unlink(missing_ok=True)
    elif is_url(source_str):
        result = convert_url(source_str, clean=clean)
    else:
        result = convert_file(Path(source_str), clean=clean)

    if result.success and frontmatter:
        result = ConversionResult(
            source_path=result.source_path,
            markdown=inject_frontmatter(result.markdown, source_str),
            success=True,
        )

    if result.success and format != "md":
        result = ConversionResult(
            source_path=result.source_path,
            markdown=format_output(result.markdown, format, source_str),
            success=True,
        )

    return result


def batch(
    source: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    workers: Optional[int] = None,
    recursive: bool = False,
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    clean: bool = True,
    incremental: bool = False,
) -> "BatchResult":
    """Convert all supported files in a directory using parallel workers.

    Args:
        source: Directory to scan.
        output_dir: Output directory for .md files.
        workers: Number of parallel workers. None = auto.
        recursive: Scan subdirectories.
        include: Glob patterns to include.
        exclude: Glob patterns to exclude.
        clean: Post-process markdown.
        incremental: Skip unchanged files.

    Returns:
        BatchResult with conversion results and statistics.
    """
    from repulp.engine import batch_convert

    return batch_convert(
        Path(source),
        workers=workers,
        recursive=recursive,
        include=include,
        exclude=exclude,
        clean=clean,
        incremental=incremental,
    )


def extract_tables(
    source: Union[str, Path],
    format: str = "dict",
    clean: bool = True,
) -> list:
    """Extract tables from a document as structured data.

    Args:
        source: File path or URL.
        format: "dict" (list[dict]), "csv" (strings), "dataframe" (pandas), "markdown" (raw).
        clean: Post-process markdown before extraction.

    Returns:
        List of tables in the requested format.
    """
    from repulp.extractor import extract_tables_structured

    result = convert(source, clean=clean)
    if not result.success:
        return []

    return extract_tables_structured(result.markdown, format=format)


def watch(
    source: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    recursive: bool = True,
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    clean: bool = True,
    debounce_ms: int = 500,
    on_change=None,
    on_command: Optional[str] = None,
) -> None:
    """Watch a directory and auto-convert files on change.

    Args:
        source: Directory to watch.
        output_dir: Where to write .md files.
        recursive: Watch subdirectories.
        include: Glob patterns to include.
        exclude: Glob patterns to exclude.
        clean: Post-process markdown.
        debounce_ms: Debounce interval in milliseconds.
        on_change: Callback(WatchEvent) after each conversion.
        on_command: Shell command to run after each conversion.
    """
    from repulp.watcher import watch_directory

    watch_directory(
        Path(source),
        output_dir=Path(output_dir) if output_dir else None,
        recursive=recursive,
        include=include,
        exclude=exclude,
        clean=clean,
        debounce_ms=debounce_ms,
        on_change=on_change,
        on_command=on_command,
    )
