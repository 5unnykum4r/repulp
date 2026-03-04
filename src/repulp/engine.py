"""Parallel batch conversion engine for repulp.

Provides batch_convert() which uses ProcessPoolExecutor to convert multiple
files in parallel, and _collect_files() to scan directories with glob-based
include/exclude filters.
"""

from __future__ import annotations

import fnmatch
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from repulp.cache import ConversionCache
from repulp.converter import SUPPORTED_EXTENSIONS, ConversionResult, convert_file


@dataclass
class BatchResult:
    """Aggregated result of a batch conversion run."""

    results: list[ConversionResult] = field(default_factory=list)
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    elapsed: float = 0.0
    throughput: float = 0.0


def _collect_files(
    directory: Path,
    recursive: bool = False,
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
) -> list[Path]:
    """Scan a directory for supported files, applying include/exclude filters.

    Args:
        directory: Root directory to scan.
        recursive: If True, descend into subdirectories.
        include: Glob patterns to whitelist (only matching files are kept).
        exclude: Glob patterns to blacklist (matching files are dropped).

    Returns:
        Sorted list of Path objects for files that pass all filters.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []

    if recursive:
        candidates = sorted(directory.rglob("*"))
    else:
        candidates = sorted(directory.iterdir())

    files = [
        f for f in candidates
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if include:
        files = [
            f for f in files
            if any(fnmatch.fnmatch(f.name, pat) for pat in include)
        ]
    if exclude:
        files = [
            f for f in files
            if not any(fnmatch.fnmatch(f.name, pat) for pat in exclude)
        ]

    return files


def _convert_single(
    file_path: Path,
    clean: bool,
) -> ConversionResult:
    """Convert a single file — standalone function so it is picklable for ProcessPoolExecutor.

    Args:
        file_path: Absolute path to the file to convert.
        clean: Whether to run the cleaner pipeline on the output.

    Returns:
        ConversionResult for the given file.
    """
    return convert_file(file_path, clean=clean)


def _auto_workers() -> int:
    """Return a sensible default worker count (cpu_count - 1, minimum 1)."""
    cpu = os.cpu_count() or 2
    return max(1, cpu - 1)


def batch_convert(
    directory: Path,
    *,
    recursive: bool = False,
    clean: bool = True,
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    workers: Optional[int] = None,
    incremental: bool = True,
    on_progress: Optional[Callable[[int, int, ConversionResult], None]] = None,
) -> BatchResult:
    """Convert all supported files in *directory* using parallel workers.

    Args:
        directory: Root directory to scan for files.
        recursive: Descend into subdirectories.
        clean: Run the cleaner pipeline on each converted file.
        include: Glob patterns to whitelist filenames.
        exclude: Glob patterns to blacklist filenames.
        workers: Number of parallel worker processes.
                 None or 0 means auto-detect (cpu_count - 1).
                 1 means sequential execution (no subprocess overhead).
        incremental: When True, use a file-hash cache to skip files that
                     have not changed since the last successful conversion.
        on_progress: Optional callback invoked after each file finishes.
                     Signature: (completed_count, total_count, result).

    Returns:
        BatchResult with per-file results and aggregate statistics.
    """
    directory = Path(directory)
    files = _collect_files(directory, recursive=recursive, include=include, exclude=exclude)
    total = len(files)

    if total == 0:
        return BatchResult(
            results=[],
            total=0,
            succeeded=0,
            failed=0,
            skipped=0,
            elapsed=0.0,
            throughput=0.0,
        )

    # Incremental cache: partition files into changed / unchanged
    cache: Optional[ConversionCache] = None
    skipped_results: list[ConversionResult] = []

    if incremental:
        cache = ConversionCache(directory / ".repulp.cache")
        changed_files, unchanged_files = cache.partition(files)

        # Build skipped ConversionResult entries for unchanged files
        skipped_results = [
            ConversionResult(source_path=f, markdown="", success=True)
            for f in unchanged_files
        ]
        files_to_convert = changed_files
    else:
        files_to_convert = files

    convert_total = len(files_to_convert)

    if workers is None or workers == 0:
        worker_count = _auto_workers()
    else:
        worker_count = max(1, workers)

    start = time.monotonic()

    # Map from original index to result, so we can re-sort after parallel execution
    indexed_results: dict[int, ConversionResult] = {}
    completed_count = 0

    if convert_total == 0:
        pass
    elif worker_count == 1:
        # Sequential path — avoids subprocess serialization overhead
        for idx, file_path in enumerate(files_to_convert):
            result = _convert_single(file_path, clean)
            indexed_results[idx] = result
            completed_count += 1
            if on_progress is not None:
                on_progress(completed_count, total, result)
    else:
        # Parallel path using ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            future_to_idx = {
                executor.submit(_convert_single, file_path, clean): idx
                for idx, file_path in enumerate(files_to_convert)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = ConversionResult(
                        source_path=files_to_convert[idx],
                        markdown="",
                        success=False,
                        error=f"Worker process error: {exc}",
                    )
                indexed_results[idx] = result
                completed_count += 1
                if on_progress is not None:
                    on_progress(completed_count, total, result)

    elapsed = time.monotonic() - start

    # Collect converted results in submission order
    converted_results = [indexed_results[i] for i in range(convert_total)]

    # Update cache for successfully converted files
    if cache is not None:
        for r in converted_results:
            if r.success:
                cache.mark_converted(r.source_path)
        cache.save()

    # Merge converted + skipped results, preserving original file order
    result_map: dict[str, ConversionResult] = {}
    for r in converted_results:
        result_map[str(r.source_path.resolve())] = r
    for r in skipped_results:
        result_map[str(r.source_path.resolve())] = r

    results = [result_map[str(f.resolve())] for f in files]

    succeeded = sum(1 for r in converted_results if r.success)
    failed = sum(1 for r in converted_results if not r.success)
    skipped = len(skipped_results)

    return BatchResult(
        results=results,
        total=total,
        succeeded=succeeded,
        failed=failed,
        skipped=skipped,
        elapsed=elapsed,
        throughput=total / elapsed if elapsed > 0 else 0.0,
    )
