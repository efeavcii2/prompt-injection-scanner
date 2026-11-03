"""Inline style zincirinden, bir metnin kullanicidan gizlenip gizlenmedigini tahmin eder."""

from __future__ import annotations

import re
from dataclasses import dataclass

from scanner.parsing import TextNode


@dataclass
class HiddenTextFinding:
    text: str
    reason: str
    tag_chain: list[str]


def _parse_css_declarations(style: str) -> dict[str, str]:
    """'color: red; opacity:0' -> {'color': 'red', 'opacity': '0'}"""
    declarations: dict[str, str] = {}
    for part in style.split(";"):
        if ":" not in part:
            continue
        key, _, value = part.partition(":")
        declarations[key.strip()] = value.strip()
    return declarations


def _is_zero_or_tiny_size(value: str) -> bool:
    """font-size/width/height gibi degerlerin pratikte gorunmez (<=1px) olup olmadigini kontrol eder."""
    match = re.match(r"^(-?\d*\.?\d+)\s*(px|pt|em|rem|%)?$", value.strip())
    if not match:
        return False
    try:
        number = float(match.group(1))
    except ValueError:
        return False
    unit = match.group(2) or "px"
    if unit == "%":
        return number <= 0
    return number <= 1


def _is_offscreen_position(value: str) -> bool:
    """left/text-indent gibi degerlerin ekran disina (buyuk negatif) tasiyip tasimadigini kontrol eder."""
    match = re.match(r"^(-?\d*\.?\d+)\s*(px|pt|em|rem)?$", value.strip())
    if not match:
        return False
    try:
        number = float(match.group(1))
    except ValueError:
        return False
    return number <= -500


def _colors_match(color_a: str, color_b: str) -> bool:
    """Iki renk degerinin (basit hex/isim karsilastirmasi) ayni sayilip sayilmayacagini kontrol eder."""
    norm_a = color_a.strip().lower().replace(" ", "")
    norm_b = color_b.strip().lower().replace(" ", "")
    if norm_a == norm_b:
        return True
    whites = {"#fff", "#ffffff", "white", "rgb(255,255,255)"}
    if norm_a in whites and norm_b in whites:
        return True
    return False


def _check_single_style(style: str) -> str | None:
    """Tek bir inline style stringini gizleme kalibi icin kontrol eder, varsa sebep metni doner."""
    decl = _parse_css_declarations(style)

    if decl.get("display") == "none":
        return "display:none"

    if decl.get("visibility") == "hidden":
        return "visibility:hidden"

    opacity = decl.get("opacity", "")
    if opacity in {"0", "0.0", "0%"}:
        return "opacity:0"

    font_size = decl.get("font-size", "")
    if font_size and _is_zero_or_tiny_size(font_size):
        return f"font-size:{font_size}"

    for prop in ("width", "height"):
        value = decl.get(prop, "")
        if value and _is_zero_or_tiny_size(value) and decl.get("overflow") == "hidden":
            return f"{prop}:{value} + overflow:hidden"

    for prop in ("left", "margin-left", "text-indent"):
        value = decl.get(prop, "")
        if value and _is_offscreen_position(value):
            return f"{prop}:{value} (ekran disi)"

    color = decl.get("color", "")
    background = decl.get("background-color") or decl.get("background", "")
    if color and background and _colors_match(color, background):
        return f"color:{color} == background:{background}"

    return None


def find_hidden_text(nodes: list[TextNode]) -> list[HiddenTextFinding]:
    """Metin parcalari arasinda, ebeveyn stil zincirinde bir gizleme kalibi olanlari bulur."""
    findings: list[HiddenTextFinding] = []

    for node in nodes:
        for style in node.styles:
            reason = _check_single_style(style)
            if reason:
                findings.append(
                    HiddenTextFinding(text=node.text, reason=reason, tag_chain=node.tag_chain)
                )
                break

    return findings
