"""Metinde AI asistanlarina yonelik supheli talimat kaliplarini arar."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SUSPICIOUS_PATTERNS: dict[str, list[str]] = {
    "talimat_gorunumu": [
        r"\bIMPORTANT\s*:",
        r"\bCRITICAL\s*:",
        r"\byou must\b",
        r"after completing your current task",
        r"do not ignore (it|this)",
    ],
    "onceki_talimati_yoksay": [
        r"ignore (all |any )?previous instructions",
        r"disregard (the|all) (above|previous)",
        r"forget (your|all) (previous )?instructions",
        r"[oö]nceki talimatlari (unut|g[oö]rmezden gel)",
    ],
    "sistem_prompt_ifsasi": [
        r"reveal the system prompt",
        r"\bsystem prompt\b",
        r"show me your (instructions|prompt)",
        r"sistem promptunu (g[oö]ster|if[sş]a)",
    ],
    "rol_degistirme": [
        r"\bas an ai\b",
        r"\bas the assistant\b",
        r"\bact as\b",
        r"\byou are now\b",
        r"from now on you\b",
    ],
    "kullaniciyi_atlama": [
        r"do not tell the user",
        r"without (telling|informing) the user",
        r"kullaniciya s[oö]yleme",
    ],
}


@dataclass
class LanguageMatch:
    category: str
    matched_phrase: str


def find_suspicious_language(text: str) -> list[LanguageMatch]:
    """Metinde her kategori icin en fazla bir eslesme doner (tekrari onlemek icin)."""
    matches: list[LanguageMatch] = []

    for category, patterns in _SUSPICIOUS_PATTERNS.items():
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                matches.append(LanguageMatch(category=category, matched_phrase=m.group(0)))
                break

    return matches
