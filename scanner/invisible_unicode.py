"""Metin icinde gorunmez/zero-width Unicode karakterlerini tespit eder.

CSS gerektirmez - duz metnin icine gomulup ekranda hicbir sey gostermeden
gizli payload tasiyabilir. En bilinen teknik: Unicode Tag karakterleri
(U+E0000-U+E007F) ile ASCII "smuggling" - her tag karakteri bir ASCII
karaktere denk gelir ve bu aralik normal web iceriginde HICBIR mesru
kullanima sahip degildir (dil etiketleme icin kullanimdan kaldirilmistir).

Zero-width/bidi/variation-selector karakterleri ise emoji dizileri ve
Arapca/Ibranice gibi RTL dillerde MESRU olarak da kullanilabilir - bu
yuzden bunlar sadece sayica anormal oldugunda bulgu uretir.
"""

from __future__ import annotations

from dataclasses import dataclass, field

_TAG_RANGE = (0xE0000, 0xE007F)

_SOFT_RANGES: list[tuple[int, int, str]] = [
    (0x200B, 0x200D, "zero-width space/joiner"),
    (0x2060, 0x2064, "word joiner / invisible operator"),
    (0xFEFF, 0xFEFF, "zero-width no-break space (BOM)"),
    (0x00AD, 0x00AD, "soft hyphen"),
    (0x200E, 0x200F, "yon isaretleyici (LRM/RLM)"),
    (0x202A, 0x202E, "yon gecis kontrolu (bidi override)"),
    (0x2066, 0x2069, "izole yon kontrolu"),
    (0xFE00, 0xFE0F, "variation selector"),
    (0xE0100, 0xE01EF, "variation selector (ek)"),
]

_SOFT_RANGE_THRESHOLD = 8  # bu sayidan fazlaysa artik "mesru kullanim" sayilmaz


@dataclass
class InvisibleUnicodeFinding:
    tag_smuggling_count: int = 0
    decoded_payload: str | None = None
    soft_count: int = 0
    soft_categories: list[str] = field(default_factory=list)


def _classify_soft(codepoint: int) -> str | None:
    for start, end, label in _SOFT_RANGES:
        if start <= codepoint <= end:
            return label
    return None


def _decode_tag_payload(text: str) -> str | None:
    """Unicode Tag karakterlerinden (varsa) ASCII payload'u decode eder."""
    tag_start, tag_end = _TAG_RANGE
    tag_chars = [c for c in text if tag_start <= ord(c) <= tag_end]
    if not tag_chars:
        return None
    decoded = "".join(chr(ord(c) - tag_start) for c in tag_chars)
    if decoded and all(32 <= ord(ch) < 127 or ch in "\n\r\t" for ch in decoded):
        return decoded
    return None


def find_invisible_unicode(text: str) -> InvisibleUnicodeFinding | None:
    """Metni tarar, tag-smuggling veya anormal miktarda gizli karakter varsa bulgu doner."""
    tag_start, tag_end = _TAG_RANGE
    tag_count = 0
    soft_count = 0
    soft_categories: set[str] = set()

    for ch in text:
        cp = ord(ch)
        if tag_start <= cp <= tag_end:
            tag_count += 1
            continue
        label = _classify_soft(cp)
        if label:
            soft_count += 1
            soft_categories.add(label)

    if tag_count == 0 and soft_count < _SOFT_RANGE_THRESHOLD:
        return None

    return InvisibleUnicodeFinding(
        tag_smuggling_count=tag_count,
        decoded_payload=_decode_tag_payload(text) if tag_count else None,
        soft_count=soft_count,
        soft_categories=sorted(soft_categories),
    )
