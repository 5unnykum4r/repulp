from __future__ import annotations

import json
import re
from typing import Optional

from repulp.extractor import extract_all


def to_plain_text(markdown: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", markdown, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^[\s]*[-*+]\s+", "  ", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def to_json(
    markdown: str,
    source: str,
    metadata: Optional[dict] = None,
) -> str:
    extracted = extract_all(markdown)

    data = {
        "source": source,
        "content": markdown,
        "plain_text": to_plain_text(markdown),
        "metadata": metadata or {},
        "structure": {
            "headings": extracted.headings,
            "links": extracted.links,
            "tables_count": len(extracted.tables),
            "images": extracted.images,
        },
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_output(
    markdown: str,
    fmt: str = "md",
    source: str = "",
    metadata: Optional[dict] = None,
) -> str:
    if fmt == "text":
        return to_plain_text(markdown)
    elif fmt == "json":
        return to_json(markdown, source, metadata)
    return markdown
