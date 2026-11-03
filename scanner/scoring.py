"""Bulgulara agirlik verip toplam bir risk skoru/seviyesi uretir."""

from __future__ import annotations

from dataclasses import dataclass

from scanner.combine import Finding, Severity

_WEIGHTS = {
    Severity.HIGH: 10,
    Severity.MEDIUM: 4,
    Severity.LOW: 1,
    Severity.INFO: 0,
}


@dataclass
class RiskScore:
    score: int
    level: str  # "DUSUK" | "ORTA" | "YUKSEK"


def compute_risk_score(findings: list[Finding]) -> RiskScore:
    """Her bulgunun siddetine agirlik vererek toplam skoru ve seviyeyi hesaplar.

    Esikler: 0 puan -> DUSUK, 1-9 puan -> ORTA, 10+ puan -> YUKSEK.
    Tek bir HIGH bulgu (gizli+supheli kesisimi) bu esigi hemen gecer.
    """
    score = sum(_WEIGHTS.get(f.severity, 0) for f in findings)

    if score == 0:
        level = "DUSUK"
    elif score < 10:
        level = "ORTA"
    else:
        level = "YUKSEK"

    return RiskScore(score=score, level=level)
