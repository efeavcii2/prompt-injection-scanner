"""HTML icerigini okur, metin parcalarini ebeveyn stil zinciriyle cikarir.

Guvenlik: hicbir script calistirmaz, sadece statik metin/stil parse eder.
"""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser

_VOID_TAGS = {
    "br", "hr", "img", "input", "meta", "link", "area",
    "base", "col", "embed", "source", "track", "wbr",
}
_SKIP_CONTENT_TAGS = {"script", "style", "head", "title"}


@dataclass
class TextNode:
    text: str
    styles: list[str]  # bu metne kadar ebeveyn zincirindeki inline style degerleri
    tag_chain: list[str]  # ebeveyn etiket adlari (en disdan en ice)


class _DOMTextExtractor(HTMLParser):
    """HTML'i gezerken her metin parcasini, ebeveyn stil zinciriyle toplar."""

    def __init__(self) -> None:
        super().__init__()
        self.nodes: list[TextNode] = []
        self._style_stack: list[str] = []
        self._tag_stack: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in _SKIP_CONTENT_TAGS:
            self._skip_depth += 1
        if tag in _VOID_TAGS:
            return
        style = (dict(attrs).get("style") or "").lower()
        self._style_stack.append(style)
        self._tag_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _SKIP_CONTENT_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in _VOID_TAGS:
            return
        if self._style_stack:
            self._style_stack.pop()
        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        text = data.strip()
        if not text:
            return
        self.nodes.append(
            TextNode(
                text=text,
                styles=[s for s in self._style_stack if s],
                tag_chain=list(self._tag_stack),
            )
        )


def parse_html(html: str) -> list[TextNode]:
    """HTML'i parse edip metin parcalarini ebeveyn stil bilgisiyle doner."""
    extractor = _DOMTextExtractor()
    extractor.feed(html)
    return extractor.nodes


def fetch_url(url: str, timeout: int = 10) -> str:
    """Bir URL'den HTML icerigini ceker (sadece okur, hicbir JS calistirmaz)."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def load_source(path_or_url: str) -> str:
    """Hem http(s):// URL hem yerel dosya yolu destekler."""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return fetch_url(path_or_url)
    with open(path_or_url, encoding="utf-8", errors="replace") as f:
        return f.read()
