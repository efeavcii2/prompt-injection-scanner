"""Pano (clipboard) icerigini okur - xclip/xsel/wl-paste araclarini kullanir,
harici Python bagimliligi gerektirmez.
"""

from __future__ import annotations

import shutil
import subprocess


class ClipboardUnavailableError(RuntimeError):
    pass


def _run(cmd: list[str]) -> str | None:
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=5)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace")


def read_clipboard() -> str:
    """Pano icerigini okur.

    Mumkunse HTML hedefini tercih eder - CSS/gizli-metin bilgisi (opacity:0
    gibi) sadece HTML kopyasinda korunur, duz metin kopyasinda cogunlukla
    kaybolur. HTML yoksa duz metni basit bir HTML sargisi icine alir.
    """
    text: str | None = None

    if shutil.which("xclip"):
        html = _run(["xclip", "-selection", "clipboard", "-t", "text/html", "-o"])
        if html and html.strip():
            return html
        text = _run(["xclip", "-selection", "clipboard", "-o"])
    elif shutil.which("wl-paste"):
        html = _run(["wl-paste", "--type", "text/html"])
        if html and html.strip():
            return html
        text = _run(["wl-paste"])
    elif shutil.which("xsel"):
        text = _run(["xsel", "--clipboard", "--output"])
    else:
        raise ClipboardUnavailableError(
            "Pano okuma araci bulunamadi (xclip/xsel/wl-paste). "
            "Kurulum: sudo apt install xclip"
        )

    if not text or not text.strip():
        raise ClipboardUnavailableError("Pano bos veya okunamadi.")

    return f"<html><body>{text}</body></html>"
