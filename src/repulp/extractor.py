from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExtractionResult:
    tables: list[str] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    headings: list[dict[str, str]] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)


def extract_tables(markdown: str) -> list[str]:
    lines = markdown.split("\n")
    tables: list[str] = []
    i = 0
    while i < len(lines):
        if "|" in lines[i] and i + 1 < len(lines) and re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[i + 1]):
            table_lines: list[str] = []
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            tables.append("\n".join(table_lines))
        else:
            i += 1
    return tables


def _deduplicate_headers(headers: list[str]) -> list[str]:
    """Append _1, _2, etc. to duplicate header names to prevent data loss."""
    seen: dict[str, int] = {}
    result: list[str] = []
    for h in headers:
        if h in seen:
            seen[h] += 1
            result.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            result.append(h)
    return result


def parse_markdown_table(table_text: str) -> list[dict[str, str]]:
    """Parse a single markdown pipe table string into a list of dicts (one dict per data row, headers as keys)."""
    lines = [line.strip() for line in table_text.strip().split("\n") if line.strip()]
    if len(lines) < 2:
        return []
    raw_headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    headers = _deduplicate_headers(raw_headers)
    rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        while len(cells) < len(headers):
            cells.append("")
        row = {headers[i]: cells[i] for i in range(len(headers))}
        rows.append(row)
    return rows


def extract_tables_structured(markdown: str, format: str = "dict") -> list:
    """Extract all tables from markdown in structured formats.

    Supported formats:
        - "dict": list of list[dict] (parsed rows as dicts)
        - "csv": list of CSV strings
        - "dataframe": list of pandas DataFrames (raises ImportError if pandas not installed)
        - "markdown": list of raw markdown table strings (same as extract_tables)
    """
    raw_tables = extract_tables(markdown)
    if format == "markdown":
        return raw_tables
    parsed = [parse_markdown_table(t) for t in raw_tables]
    if format == "dict":
        return parsed
    if format == "csv":
        results = []
        for rows in parsed:
            if not rows:
                results.append("")
                continue
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
            results.append(output.getvalue())
        return results
    if format == "dataframe":
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for DataFrame output. "
                "Install it with: pip install repulp[tables]"
            )
        return [pd.DataFrame(rows) for rows in parsed]
    raise ValueError(
        f"Unknown format: {format!r}. Use 'dict', 'csv', 'dataframe', or 'markdown'."
    )


def extract_links(markdown: str) -> list[dict[str, str]]:
    pattern = r"\[([^\]]*)\]\(([^)]+)\)"
    matches = re.findall(pattern, markdown)
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for text, url in matches:
        if url.startswith("data:"):
            continue
        if url not in seen:
            links.append({"text": text.strip(), "url": url.strip()})
            seen.add(url)
    return links


def extract_headings(markdown: str) -> list[dict[str, str]]:
    pattern = r"^(#{1,6})\s+(.+)$"
    headings: list[dict[str, str]] = []
    for match in re.finditer(pattern, markdown, re.MULTILINE):
        level = len(match.group(1))
        text = match.group(2).strip()
        headings.append({"level": str(level), "text": text})
    return headings


def extract_images(markdown: str) -> list[dict[str, str]]:
    pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
    images: list[dict[str, str]] = []
    for match in re.finditer(pattern, markdown):
        alt = match.group(1).strip()
        src = match.group(2).strip()
        if src.startswith("data:"):
            continue
        images.append({"alt": alt, "src": src})
    return images


def extract_all(markdown: str) -> ExtractionResult:
    return ExtractionResult(
        tables=extract_tables(markdown),
        links=extract_links(markdown),
        headings=extract_headings(markdown),
        images=extract_images(markdown),
    )


def extract_elements(
    markdown: str,
    elements: Optional[list[str]] = None,
) -> ExtractionResult:
    if not elements:
        return extract_all(markdown)

    result = ExtractionResult()
    for elem in elements:
        if elem == "tables":
            result.tables = extract_tables(markdown)
        elif elem == "links":
            result.links = extract_links(markdown)
        elif elem == "headings":
            result.headings = extract_headings(markdown)
        elif elem == "images":
            result.images = extract_images(markdown)
    return result
