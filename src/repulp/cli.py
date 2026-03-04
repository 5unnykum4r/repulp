from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table

from repulp import __version__
from repulp.config import load_config
from repulp.converter import (
    SUPPORTED_EXTENSIONS,
    ConversionResult,
    convert_file,
    convert_url,
)
from repulp.engine import batch_convert, BatchResult
from repulp.fetcher import is_url
from repulp.formatter import format_output
from repulp.frontmatter import inject_frontmatter

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="repulp",
    help="Parallel batch document conversion, watch mode, and structured extraction.",
    no_args_is_help=True,
)

extract_app = typer.Typer(help="Extract elements from documents.")
app.add_typer(extract_app, name="extract")


def version_callback(value: bool) -> None:
    if value:
        console.print(f"repulp v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    pass


def _resolve_output_path(
    source: Path,
    base_dir: Path,
    output_dir: Path,
) -> Path:
    try:
        relative = source.relative_to(base_dir)
    except ValueError:
        relative = Path(source.name)
    return output_dir / relative.with_suffix(".md")


def _write_result(
    result: ConversionResult,
    base_dir: Path,
    output_dir: Optional[Path],
    stdout: bool,
) -> None:
    if stdout:
        console.print(result.markdown)
        return

    if output_dir:
        out_path = _resolve_output_path(result.source_path, base_dir, output_dir)
    else:
        out_path = result.source_path.with_suffix(".md")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result.markdown, encoding="utf-8")


def _print_batch_summary(batch: BatchResult) -> None:
    table = Table(title="Conversion Summary", show_lines=False)
    table.add_column("Status", style="bold", width=10)
    table.add_column("File", style="dim")
    table.add_column("Details")

    for r in batch.results:
        if r.success:
            size = f"{len(r.markdown):,} chars"
            table.add_row("[green]OK[/green]", str(r.source_path.name), size)
        else:
            table.add_row("[red]FAIL[/red]", str(r.source_path.name), r.error or "Unknown error")

    console.print()
    console.print(table)
    console.print()

    parts = [f"[bold green]{batch.succeeded}[/bold green] converted"]
    if batch.failed:
        parts.append(f"[bold red]{batch.failed}[/bold red] failed")
    if batch.skipped:
        parts.append(f"[dim]{batch.skipped}[/dim] skipped (unchanged)")
    parts.append(f"[bold]{batch.total + batch.skipped}[/bold] total")
    throughput = f" | {batch.throughput:.1f} files/sec" if batch.throughput > 0 else ""
    elapsed = f" | {batch.elapsed:.1f}s" if batch.elapsed > 0 else ""
    summary = ", ".join(parts) + elapsed + throughput

    console.print(Panel(summary, title="Results", border_style="blue"))


def _parse_patterns(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


def _apply_post_processing(
    result: ConversionResult,
    source_str: str,
    frontmatter: bool,
    fmt: str,
) -> ConversionResult:
    if not result.success:
        return result

    markdown = result.markdown

    if frontmatter:
        markdown = inject_frontmatter(markdown, source_str)

    if fmt != "md":
        markdown = format_output(markdown, fmt, source_str)

    return ConversionResult(
        source_path=result.source_path,
        markdown=markdown,
        success=True,
    )


def _convert_stdin(clean: bool) -> ConversionResult:
    content = sys.stdin.buffer.read()
    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    tmp.write(content)
    tmp.close()
    try:
        result = convert_file(Path(tmp.name), clean=clean)
        return ConversionResult(
            source_path=Path("stdin"),
            markdown=result.markdown,
            success=result.success,
            error=result.error,
        )
    finally:
        Path(tmp.name).unlink(missing_ok=True)


def _url_to_slug(url: str) -> str:
    return urlparse(url).path.strip("/").replace("/", "-") or "index"


@app.command()
def convert(
    path: str = typer.Argument(help="File, directory, URL, or '-' for stdin."),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Output directory. Mirrors source structure.",
    ),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Scan directories recursively."),
    no_clean: bool = typer.Option(False, "--no-clean", help="Skip markdown post-processing cleanup."),
    include: Optional[str] = typer.Option(
        None, "--include", "-I",
        help='Glob patterns to include, comma-separated (e.g., "*.pdf,*.docx").',
    ),
    exclude: Optional[str] = typer.Option(
        None, "--exclude", "-E",
        help='Glob patterns to exclude, comma-separated (e.g., "*.tmp").',
    ),
    stdout: bool = typer.Option(False, "--stdout", "-s", help="Print output to stdout instead of writing files."),
    frontmatter: bool = typer.Option(False, "--frontmatter", "-f", help="Inject YAML frontmatter with metadata."),
    fmt: str = typer.Option("md", "--format", "-F", help="Output format: md, text, json."),
    workers: Optional[int] = typer.Option(None, "--workers", "-w", help="Parallel workers for batch conversion. 0=auto."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable incremental cache (reconvert all files)."),
) -> None:
    """Convert a file, directory, or URL to Markdown."""
    use_clean = not no_clean

    # Handle stdin
    if path == "-":
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=err_console,
            transient=True,
        ) as progress:
            progress.add_task("Converting stdin...", total=None)
            result = _convert_stdin(clean=use_clean)

        result = _apply_post_processing(result, "stdin", frontmatter, fmt)

        if result.success:
            console.print(result.markdown)
        else:
            err_console.print(f"[red]Error:[/red] {result.error}")
            raise typer.Exit(1)
        return

    # Handle URL
    if is_url(path):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=err_console if stdout else console,
            transient=stdout,
        ) as progress:
            progress.add_task("Fetching and converting URL...", total=None)
            result = convert_url(path, clean=use_clean)

        result = _apply_post_processing(result, path, frontmatter, fmt)

        if result.success:
            if stdout:
                console.print(result.markdown)
            else:
                slug = _url_to_slug(path)
                out_dir = Path(output_dir) if output_dir else Path(".")
                out_path = out_dir / f"{slug}.md"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(result.markdown, encoding="utf-8")
                err_console.print(f"[green]Saved:[/green] {out_path}")
        else:
            err_console.print(f"[red]Error:[/red] {result.error}")
            raise typer.Exit(1)
        return

    # Handle file/directory
    source = Path(path).resolve()

    if not source.exists():
        err_console.print(f"[red]Error:[/red] Path not found: {source}")
        raise typer.Exit(1)

    config = load_config(search_dir=source.parent if source.is_file() else source)
    merged = config.merge_cli_overrides(
        output_dir=output_dir,
        recursive=recursive if recursive else None,
        clean=use_clean if no_clean else None,
        include=_parse_patterns(include) if include else None,
        exclude=_parse_patterns(exclude) if exclude else None,
    )

    out_dir = Path(merged.output_dir).resolve() if merged.output_dir else None

    if source.is_file():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=err_console if stdout else console,
            transient=stdout,
        ) as progress:
            progress.add_task(f"Converting {source.name}...", total=None)
            result = convert_file(source, clean=merged.clean)

        result = _apply_post_processing(result, str(source), frontmatter, fmt)

        if result.success:
            _write_result(result, source.parent, out_dir, stdout)
            if not stdout:
                err_console.print(f"[green]Converted:[/green] {source.name} ({len(result.markdown):,} chars)")
        else:
            err_console.print(f"[red]Error:[/red] {result.error}")
            raise typer.Exit(1)
    else:
        # Batch directory conversion with parallel engine
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=err_console if stdout else console,
            transient=stdout,
        ) as progress:
            task = progress.add_task("Converting...", total=None)

            batch_result = batch_convert(
                source,
                workers=workers,
                recursive=merged.recursive,
                include=merged.include,
                exclude=merged.exclude,
                clean=merged.clean,
                incremental=not no_cache,
            )

        # Write output files
        for r in batch_result.results:
            if r.success:
                _write_result(r, source, out_dir, stdout)

        if not stdout:
            _print_batch_summary(batch_result)


@app.command()
def watch(
    path: str = typer.Argument(help="Directory to watch."),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory for converted files.",
    ),
    include: Optional[str] = typer.Option(
        None, "--include", "-I", help='Glob patterns to include.',
    ),
    exclude: Optional[str] = typer.Option(
        None, "--exclude", "-E", help='Glob patterns to exclude.',
    ),
    no_clean: bool = typer.Option(False, "--no-clean", help="Skip markdown cleanup."),
    debounce: int = typer.Option(500, "--debounce", help="Debounce interval in milliseconds."),
    on_command: Optional[str] = typer.Option(
        None, "--on-change", help="Shell command to run after each conversion.",
    ),
) -> None:
    """Watch a directory and auto-convert files on change."""
    from repulp.watcher import watch_directory, WatchEvent

    source = Path(path).resolve()
    if not source.is_dir():
        err_console.print(f"[red]Error:[/red] Not a directory: {source}")
        raise typer.Exit(1)

    out_dir = Path(output_dir).resolve() if output_dir else None

    console.print(f"[bold]Watching:[/bold] {source}")
    if out_dir:
        console.print(f"[bold]Output:[/bold] {out_dir}")
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    def on_change(event: WatchEvent):
        if event.success:
            console.print(f"  [green]Converted:[/green] {event.source_path.name} -> {event.output_path}")
        else:
            console.print(f"  [red]Failed:[/red] {event.source_path.name}: {event.error}")

    try:
        watch_directory(
            source,
            output_dir=out_dir,
            include=_parse_patterns(include) if include else None,
            exclude=_parse_patterns(exclude) if exclude else None,
            clean=not no_clean,
            debounce_ms=debounce,
            on_change=on_change,
            on_command=on_command,
        )
    except KeyboardInterrupt:
        console.print("\n[bold]Watch stopped.[/bold]")


@extract_app.command("tables")
def extract_tables_cmd(
    path: str = typer.Argument(help="File or URL to extract tables from."),
    fmt: str = typer.Option("markdown", "--format", "-F", help="Output format: markdown, csv, json, dict."),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Directory to save CSV files (one per table).",
    ),
) -> None:
    """Extract tables from a document as CSV, JSON, or DataFrames."""
    from repulp.extractor import extract_tables_structured

    conv_result = _convert_source(path)

    output_format = fmt if fmt != "json" else "dict"
    tables = extract_tables_structured(conv_result.markdown, format=output_format)

    if not tables:
        err_console.print("[yellow]No tables found.[/yellow]")
        raise typer.Exit(0)

    if fmt == "json":
        console.print(json.dumps(tables, indent=2, ensure_ascii=False))
    elif fmt == "csv" and output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for i, csv_str in enumerate(tables, 1):
            out_file = out / f"table-{i}.csv"
            out_file.write_text(csv_str, encoding="utf-8")
            console.print(f"  [green]Saved:[/green] {out_file}")
    else:
        for i, table in enumerate(tables, 1):
            console.print(f"\n[bold]Table {i}:[/bold]")
            console.print(table)


@extract_app.command("links")
def extract_links_cmd(
    path: str = typer.Argument(help="File or URL to extract links from."),
    fmt: str = typer.Option("text", "--format", "-F", help="Output format: text or json."),
) -> None:
    """Extract links from a document."""
    from repulp.extractor import extract_links

    conv_result = _convert_source(path)
    links = extract_links(conv_result.markdown)

    if not links:
        err_console.print("[yellow]No links found.[/yellow]")
        raise typer.Exit(0)

    if fmt == "json":
        console.print(json.dumps(links, indent=2, ensure_ascii=False))
    else:
        for link in links:
            console.print(f"  {link['text']} -> {link['url']}")


@extract_app.command("headings")
def extract_headings_cmd(
    path: str = typer.Argument(help="File or URL to extract headings from."),
    fmt: str = typer.Option("text", "--format", "-F", help="Output format: text or json."),
) -> None:
    """Extract headings from a document."""
    from repulp.extractor import extract_headings

    conv_result = _convert_source(path)
    headings = extract_headings(conv_result.markdown)

    if not headings:
        err_console.print("[yellow]No headings found.[/yellow]")
        raise typer.Exit(0)

    if fmt == "json":
        console.print(json.dumps(headings, indent=2, ensure_ascii=False))
    else:
        for h in headings:
            indent = "  " * (int(h["level"]) - 1)
            console.print(f"  {indent}{h['text']}")


@extract_app.command("images")
def extract_images_cmd(
    path: str = typer.Argument(help="File or URL to extract images from."),
    fmt: str = typer.Option("text", "--format", "-F", help="Output format: text or json."),
) -> None:
    """Extract image references from a document."""
    from repulp.extractor import extract_images

    conv_result = _convert_source(path)
    images = extract_images(conv_result.markdown)

    if not images:
        err_console.print("[yellow]No images found.[/yellow]")
        raise typer.Exit(0)

    if fmt == "json":
        console.print(json.dumps(images, indent=2, ensure_ascii=False))
    else:
        for img in images:
            console.print(f"  {img['alt'] or '(no alt)'} -> {img['src']}")


def _convert_source(path: str) -> ConversionResult:
    """Convert a file or URL to markdown, or exit on failure."""
    if is_url(path):
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=err_console, transient=True) as p:
            p.add_task("Fetching...", total=None)
            result = convert_url(path, clean=True)
    else:
        source = Path(path).resolve()
        if not source.exists():
            err_console.print(f"[red]Error:[/red] Path not found: {source}")
            raise typer.Exit(1)
        result = convert_file(source, clean=True)

    if not result.success:
        err_console.print(f"[red]Error:[/red] {result.error}")
        raise typer.Exit(1)

    return result


if __name__ == "__main__":
    app()
