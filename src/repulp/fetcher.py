from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Optional

import httpx

USER_AGENT = "repulp/0.1.0 (https://github.com/5unnyKu/repulp)"

CONTENT_TYPE_TO_EXT: dict[str, str] = {
    "text/html": ".html",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/csv": ".csv",
    "application/json": ".json",
    "application/xml": ".xml",
    "text/xml": ".xml",
    "text/plain": ".txt",
}


def is_url(path: str) -> bool:
    try:
        parsed = urlparse(path)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


def _guess_extension(url: str, content_type: Optional[str]) -> str:
    path = urlparse(url).path
    name = unquote(path.split("/")[-1]) if path else ""
    if "." in name:
        ext = "." + name.rsplit(".", 1)[-1].lower()
        if len(ext) <= 6:
            return ext

    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        if ct in CONTENT_TYPE_TO_EXT:
            return CONTENT_TYPE_TO_EXT[ct]

    return ".html"


def fetch_url(url: str, timeout: float = 30.0) -> Path:
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        response = client.get(url, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()

    content_type = response.headers.get("content-type")
    ext = _guess_extension(url, content_type)

    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tmp.write(response.content)
    tmp.close()

    return Path(tmp.name)
