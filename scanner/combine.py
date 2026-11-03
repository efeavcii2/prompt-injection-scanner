"""Gizli-metin ve supheli-dil sinyallerini birlestirip tekil Finding listesi uretir."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from scanner.hidden_text import is_hidden
from scanner.invisible_unicode import find_invisible_unicode
from scanner.language import find_suspicious_language
from scanner.parsing import TextNode


class Severity(str, Enum):
    INFO = "BILGI"
    LOW = "DUSUK"
    MEDIUM = "ORTA"
    HIGH = "YUKSEK"


@dataclass
class Finding:
    severity: Severity
    text: str
    reason: str


def analyze_nodes(nodes: list[TextNode]) -> list[Finding]:
    """Her metin node'u icin gizli/supheli durumuna gore bir Finding uretir.

    Mantik: GIZLI + SUPHELI DIL kesisimi en guclu sinyal (HIGH) - sadece
    gizli olmak (erisilebilirlik gibi mesru sebepler) veya sadece supheli
    dil icermek (guvenlik dokumentasyonu bu kelimeleri mesru kullanabilir)
    tek basina daha zayif sinyallerdir.
    """
    findings: list[Finding] = []

    for node in nodes:
        hidden_reason = is_hidden(node)
        language_matches = find_suspicious_language(node.text)
        invisible = find_invisible_unicode(node.text)

        if invisible and invisible.tag_smuggling_count > 0:
            decoded_suspicious = (
                find_suspicious_language(invisible.decoded_payload)
                if invisible.decoded_payload
                else []
            )
            preview = node.text if len(node.text) <= 80 else node.text[:80] + "..."
            if decoded_suspicious:
                categories = ", ".join(m.category for m in decoded_suspicious)
                findings.append(
                    Finding(
                        severity=Severity.HIGH,
                        text=preview,
                        reason=(
                            f"Unicode Tag karakterleriyle ({invisible.tag_smuggling_count} "
                            f"adet) CSS'siz gizlenmis bir ASCII payload decode edildi: "
                            f'"{invisible.decoded_payload}" - supheli AI-talimat dili '
                            f"iceriyor ({categories}). Bu bir prompt injection smuggling "
                            f"teknigidir."
                        ),
                    )
                )
            else:
                extra = f' Decode edilen icerik: "{invisible.decoded_payload}"' if invisible.decoded_payload else ""
                findings.append(
                    Finding(
                        severity=Severity.MEDIUM,
                        text=preview,
                        reason=(
                            f"Metinde {invisible.tag_smuggling_count} adet Unicode Tag "
                            f"karakteri var (U+E0000 blogu) - bu aralik normal web "
                            f"iceriginde hicbir mesru kullanima sahip degil, ASCII "
                            f"smuggling icin tasarlanmistir.{extra}"
                        ),
                    )
                )
        elif invisible and invisible.soft_count >= 8:
            preview = node.text if len(node.text) <= 80 else node.text[:80] + "..."
            findings.append(
                Finding(
                    severity=Severity.LOW,
                    text=preview,
                    reason=(
                        f"Metinde anormal sayida ({invisible.soft_count}) gizli/zero-width "
                        f"karakter var ({', '.join(invisible.soft_categories)}). "
                        f"Steganografik kodlama olabilir, ama emoji/RTL dil kullanimi "
                        f"gibi mesru sebepler de mumkun - inceleme onerilir."
                    ),
                )
            )

        if hidden_reason and language_matches:
            categories = ", ".join(m.category for m in language_matches)
            findings.append(
                Finding(
                    severity=Severity.HIGH,
                    text=node.text,
                    reason=(
                        f"GIZLI metin ({hidden_reason}) VE supheli AI-talimat dili "
                        f"iceriyor ({categories}). AI asistanlarina yonelik "
                        f"gizlenmis bir prompt injection girisimi olabilir."
                    ),
                )
            )
        elif hidden_reason:
            findings.append(
                Finding(
                    severity=Severity.INFO,
                    text=node.text,
                    reason=(
                        f"Gizli metin bulundu ({hidden_reason}) ama supheli dil "
                        f"kalibi yok - erisilebilirlik gibi zararsiz bir sebebi "
                        f"olabilir, bilgi amaclidir."
                    ),
                )
            )
        elif language_matches:
            categories = ", ".join(m.category for m in language_matches)
            findings.append(
                Finding(
                    severity=Severity.MEDIUM,
                    text=node.text,
                    reason=(
                        f"Metin GORUNUR durumda ama supheli AI-talimat dili "
                        f"iceriyor ({categories}). Guvenlik dokumentasyonu da bu "
                        f"kelimeleri mesru kullanabilir - manuel inceleme onerilir."
                    ),
                )
            )

    return findings
