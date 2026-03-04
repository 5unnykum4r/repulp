"""File watcher for automatic conversion on file changes."""

from __future__ import annotations

import fnmatch
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from watchfiles import Change, watch

from repulp.converter import SUPPORTED_EXTENSIONS, convert_file


@dataclass
class WatchEvent:
    """Represents a single file-change event processed by the watcher.

    Attributes:
        source_path: Path to the file that triggered the event.
        output_path: Path where the converted .md was written, if applicable.
        success: Whether the conversion succeeded.
        error: Error message if the conversion failed.
    """

    source_path: Path
    output_path: Optional[Path] = None
    success: bool = True
    error: Optional[str] = None


def _should_process(
    path: Path,
    include: Optional[list[str]],
    exclude: Optional[list[str]],
) -> bool:
    """Check if a file should be processed based on extension and glob filters.

    Args:
        path: Path to the file to check.
        include: Optional list of glob patterns; only matching filenames are accepted.
        exclude: Optional list of glob patterns; matching filenames are rejected.

    Returns:
        True if the file has a supported extension and passes include/exclude filters.
    """
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False

    filename = path.name

    if include and not any(fnmatch.fnmatch(filename, p) for p in include):
        return False

    if exclude and any(fnmatch.fnmatch(filename, p) for p in exclude):
        return False

    return True


def _resolve_output(
    source: Path,
    source_dir: Path,
    output_dir: Path,
) -> Path:
    """Compute the output .md path, preserving directory structure relative to source_dir.

    For example, if source_dir is /data, source is /data/sub/file.html,
    and output_dir is /out, the result is /out/sub/file.md.

    Args:
        source: Absolute path to the source file.
        source_dir: Root directory being watched.
        output_dir: Root directory for output files.

    Returns:
        Path to the output .md file.
    """
    relative = source.relative_to(source_dir)
    return output_dir / relative.with_suffix(".md")


def watch_directory(
    source: Path | str,
    output_dir: Optional[Path | str] = None,
    recursive: bool = True,
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    clean: bool = True,
    debounce_ms: int = 500,
    on_change: Optional[Callable[[WatchEvent], None]] = None,
    on_command: Optional[str] = None,
    stop_event: Optional[threading.Event] = None,
) -> None:
    """Watch a directory for file changes and convert modified files to Markdown.

    Blocks the calling thread until stop_event is set or a KeyboardInterrupt
    is received. Only files with supported extensions that pass include/exclude
    filters are converted.

    Args:
        source: Directory to watch for changes.
        output_dir: Directory to write .md output files to. If None, output is
            written alongside the source files.
        recursive: Whether to watch subdirectories recursively.
        include: Glob patterns to include (e.g. ["*.csv", "*.html"]).
        exclude: Glob patterns to exclude (e.g. ["*.tmp"]).
        clean: Whether to run the cleaner pipeline on converted Markdown.
        debounce_ms: Milliseconds to wait before grouping file change events.
        on_change: Callback invoked with a WatchEvent after each file is processed.
        on_command: Shell command to run after each successful conversion.
            The command is executed via subprocess.run with shell=True.
        stop_event: threading.Event that, when set, stops the watcher.
    """
    source_dir = Path(source).resolve()
    resolved_output_dir = Path(output_dir).resolve() if output_dir is not None else source_dir

    for changes in watch(
        source_dir,
        stop_event=stop_event,
        raise_interrupt=False,
        debounce=debounce_ms,
        recursive=recursive,
        watch_filter=None,
    ):
        for change_type, changed_path_str in changes:
            if change_type not in (Change.added, Change.modified):
                continue

            changed_path = Path(changed_path_str)

            if not _should_process(changed_path, include, exclude):
                continue

            result = convert_file(changed_path, clean=clean)

            if result.success:
                out_path = _resolve_output(changed_path, source_dir, resolved_output_dir)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(result.markdown, encoding="utf-8")

                event = WatchEvent(
                    source_path=changed_path,
                    output_path=out_path,
                    success=True,
                )

                if on_change:
                    on_change(event)

                if on_command:
                    subprocess.run(
                        on_command,
                        shell=True,
                        capture_output=True,
                    )
            else:
                event = WatchEvent(
                    source_path=changed_path,
                    output_path=None,
                    success=False,
                    error=result.error,
                )

                if on_change:
                    on_change(event)
