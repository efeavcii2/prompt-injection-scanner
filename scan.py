#!/usr/bin/env python3
"""Prompt injection tarama araci - giris noktasi.

Kullanim: python scan.py <url_veya_dosya_yolu>
"""

from __future__ import annotations

import sys

from scanner.combine import analyze_nodes
from scanner.parsing import load_source, parse_html
from scanner.report import render_report
from scanner.scoring import compute_risk_score


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Kullanim: python scan.py <url_veya_dosya_yolu>")
        return 1

    source = argv[1]
    html = load_source(source)
    nodes = parse_html(html)
    findings = analyze_nodes(nodes)
    risk = compute_risk_score(findings)

    print(render_report(source, findings, risk))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
