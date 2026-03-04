from __future__ import annotations

import re


def _normalize_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def _strip_trailing_whitespace(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.split("\n"))


def _ensure_heading_spacing(text: str) -> str:
    lines = text.split("\n")
    result: list[str] = []
    for i, line in enumerate(lines):
        is_heading = bool(re.match(r"^#{1,6}\s", line))
        if is_heading and i > 0 and result and result[-1] != "":
            result.append("")
        result.append(line)
        if is_heading and i < len(lines) - 1 and lines[i + 1] != "":
            result.append("")
    return "\n".join(result)


def _fix_table_alignment(text: str) -> str:
    lines = text.split("\n")
    i = 0
    result_lines: list[str] = []

    while i < len(lines):
        if "|" in lines[i] and i + 1 < len(lines) and re.match(
            r"^\|[\s\-:|]+\|$", lines[i + 1].strip()
        ):
            table_lines: list[str] = []
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            result_lines.extend(_format_table(table_lines))
        else:
            result_lines.append(lines[i])
            i += 1

    return "\n".join(result_lines)


def _format_table(table_lines: list[str]) -> list[str]:
    rows: list[list[str]] = []
    separator_idx = 1

    for line in table_lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)

    if len(rows) < 2:
        return table_lines

    num_cols = max(len(row) for row in rows)
    for row in rows:
        while len(row) < num_cols:
            row.append("")

    col_widths = [
        max(len(rows[r][c]) for r in range(len(rows)) if r != separator_idx)
        for c in range(num_cols)
    ]
    col_widths = [max(w, 3) for w in col_widths]

    formatted: list[str] = []
    for r, row in enumerate(rows):
        if r == separator_idx:
            cells = ["-" * w for w in col_widths]
            formatted.append("| " + " | ".join(cells) + " |")
        else:
            cells = [row[c].ljust(col_widths[c]) for c in range(num_cols)]
            formatted.append("| " + " | ".join(cells) + " |")

    return formatted


def _strip_artifacts(text: str) -> str:
    text = text.replace("\x0c", "\n")
    text = text.replace("\x00", "")
    text = re.sub(r"[\x01-\x08\x0b\x0e-\x1f\x7f]", "", text)
    return text


def clean_markdown(text: str) -> str:
    if not text:
        return ""

    text = _strip_artifacts(text)
    text = _strip_trailing_whitespace(text)
    text = _ensure_heading_spacing(text)
    text = _normalize_blank_lines(text)
    text = _fix_table_alignment(text)
    text = text.strip()
    return text
