"""Bulgulari okunabilir bir terminal raporuna donusturur."""

from __future__ import annotations

from scanner.combine import Finding, Severity
from scanner.scoring import RiskScore

_SEVERITY_ORDER = {
    Severity.HIGH: 0,
    Severity.MEDIUM: 1,
    Severity.LOW: 2,
    Severity.INFO: 3,
}


def render_report(source: str, findings: list[Finding], risk: RiskScore) -> str:
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("PROMPT INJECTION TARAMA RAPORU")
    lines.append("=" * 60)
    lines.append(f"Kaynak: {source}")
    lines.append(f"RISK SEVIYESI: {risk.level} (puan: {risk.score})")
    lines.append("")

    sorted_findings = sorted(findings, key=lambda f: _SEVERITY_ORDER.get(f.severity, 99))

    lines.append("-" * 60)
    lines.append(f"BULGULAR ({len(sorted_findings)})")
    lines.append("-" * 60)
    if not sorted_findings:
        lines.append("  Supheli bir bulgu tespit edilmedi.")
    for f in sorted_findings:
        preview = f.text if len(f.text) <= 100 else f.text[:100] + "..."
        lines.append(f'  [{f.severity.value:<6}] "{preview}"')
        lines.append(f"           {f.reason}")
    lines.append("")

    counts: dict[Severity, int] = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    summary = ", ".join(
        f"{sev.value}: {cnt}"
        for sev, cnt in sorted(counts.items(), key=lambda kv: _SEVERITY_ORDER.get(kv[0], 99))
    )
    lines.append(f"Ozet: {summary or 'bulgu yok'}")
    lines.append("=" * 60)

    return "\n".join(lines)
