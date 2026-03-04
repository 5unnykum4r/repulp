from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def count_words(text: str) -> int:
    cleaned = re.sub(r"[#*`\[\]()|\-_>~]", " ", text)
    cleaned = re.sub(r"https?://\S+", "", cleaned)
    cleaned = re.sub(r"---+", "", cleaned)
    words = cleaned.split()
    return len(words)


def estimate_reading_time(word_count: int, wpm: int = 200) -> str:
    if word_count < wpm:
        return "< 1 min"
    minutes = math.ceil(word_count / wpm)
    return f"{minutes} min"


def generate_frontmatter(
    markdown: str,
    source: str,
    title: Optional[str] = None,
    extra: Optional[dict[str, str]] = None,
) -> str:
    word_count = count_words(markdown)
    reading_time = estimate_reading_time(word_count)

    if not title:
        heading_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
        if heading_match:
            title = heading_match.group(1).strip()
        else:
            title = Path(source).stem if not source.startswith("http") else source

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "---",
        f"title: \"{title}\"",
        f"source: \"{source}\"",
        f"converted: \"{now}\"",
        f"word_count: {word_count}",
        f"reading_time: \"{reading_time}\"",
    ]

    if extra:
        for key, value in extra.items():
            lines.append(f"{key}: \"{value}\"")

    lines.append("---")
    return "\n".join(lines)


def inject_frontmatter(
    markdown: str,
    source: str,
    title: Optional[str] = None,
    extra: Optional[dict[str, str]] = None,
) -> str:
    fm = generate_frontmatter(markdown, source, title, extra)
    return fm + "\n\n" + markdown
