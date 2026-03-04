from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from markitdown import MarkItDown

from repulp.cleaner import clean_markdown
from repulp.fetcher import is_url, fetch_url

SUPPORTED_EXTENSIONS: set[str] = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt",
    ".xlsx", ".xls", ".csv",
    ".html", ".htm",
    ".txt", ".md", ".rst",
    ".json", ".xml", ".yaml", ".yml",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
    ".mp3", ".wav", ".m4a", ".ogg", ".flac",
    ".epub", ".zip",
    ".ipynb",
}


@dataclass
class ConversionResult:
    source_path: Path
    markdown: str
    success: bool
    error: Optional[str] = None


def convert_file(
    path: Path,
    clean: bool = True,
) -> ConversionResult:
    """Convert a single file to Markdown using MarkItDown.

    Args:
        path: Path to the source file.
        clean: If True, run the cleaner pipeline on the resulting Markdown.

    Returns:
        ConversionResult with the Markdown text or an error description.
    """
    path = Path(path)
    if not path.exists():
        return ConversionResult(
            source_path=path,
            markdown="",
            success=False,
            error=f"File not found: {path}",
        )

    try:
        md = MarkItDown()
        result = md.convert(str(path))
        text = result.text_content or ""
        if clean:
            text = clean_markdown(text)
        return ConversionResult(source_path=path, markdown=text, success=True)
    except Exception as e:
        return ConversionResult(
            source_path=path,
            markdown="",
            success=False,
            error=str(e),
        )


def convert_url(
    url: str,
    clean: bool = True,
) -> ConversionResult:
    """Fetch a URL, save to a temp file, and convert to Markdown.

    Args:
        url: The HTTP/HTTPS URL to fetch and convert.
        clean: If True, run the cleaner pipeline on the resulting Markdown.

    Returns:
        ConversionResult with the Markdown text or an error description.
    """
    try:
        tmp_path = fetch_url(url)
        try:
            result = convert_file(tmp_path, clean=clean)
            return ConversionResult(
                source_path=Path(url),
                markdown=result.markdown,
                success=result.success,
                error=result.error,
            )
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception as e:
        return ConversionResult(
            source_path=Path(url),
            markdown="",
            success=False,
            error=str(e),
        )


def _matches_patterns(filename: str, patterns: list[str]) -> bool:
    """Return True if filename matches any of the given glob patterns."""
    return any(fnmatch.fnmatch(filename, p) for p in patterns)


def convert_directory(
    directory: Path,
    recursive: bool = False,
    clean: bool = True,
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
) -> list[ConversionResult]:
    """Convert all supported files in a directory to Markdown.

    Args:
        directory: Path to the directory to scan.
        recursive: If True, descend into subdirectories.
        clean: If True, run the cleaner pipeline on each converted file.
        include: Optional list of glob patterns; only matching files are converted.
        exclude: Optional list of glob patterns; matching files are skipped.

    Returns:
        List of ConversionResult objects, one per converted file.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []

    if recursive:
        files = sorted(directory.rglob("*"))
    else:
        files = sorted(directory.iterdir())

    files = [f for f in files if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

    if include:
        files = [f for f in files if _matches_patterns(f.name, include)]
    if exclude:
        files = [f for f in files if not _matches_patterns(f.name, exclude)]

    results: list[ConversionResult] = []
    for file_path in files:
        result = convert_file(file_path, clean=clean)
        results.append(result)

    return results
