"""
Extracts raw lines from a PDF and classifies each one using both the
existing algorithm and the ML model, returning both result sets.

Each item in a result list:
  {
    "index":       int,
    "date":        "YYYY-MM-DD",
    "description": str,
    "amount":      str,         # Decimal as string
    "line_raw":    str,         # original PDF line (used for training)
    "confidence":  float,       # model probability (0–1)
  }
"""
from __future__ import annotations

import io
from datetime import date as Date

from tracker.importers import detect_and_parse
from tracker.importers.base import extract_text_pages, AMOUNT_RE, parse_br_amount
from tracker.ml import predict, is_trained


def run_algorithm(pdf_bytes: bytes, bank_hint: str = "") -> tuple[str, list[dict]]:
    """Run the existing parser and return (bank, transactions)."""
    f = io.BytesIO(pdf_bytes)
    bank, txns = detect_and_parse(f)
    results = [
        {
            "index": i,
            "date": t.date.isoformat(),
            "description": t.description,
            "amount": str(t.amount),
            "line_raw": "",   # parsers don't expose the raw source line
            "confidence": 1.0,
        }
        for i, t in enumerate(txns)
    ]
    return bank, results


def run_model(pdf_bytes: bytes, bank: str) -> list[dict]:
    """
    Score each PDF line with the ML model and return lines the model
    believes are transactions (confidence >= 0.5).

    Each result includes the raw line and regex-extracted fields
    (DD/MM date and first BR amount).
    """
    import re

    pages_text = extract_text_pages(io.BytesIO(pdf_bytes))

    _date_re = re.compile(r"\b(\d{2})/(\d{2})(?:/(\d{4}))?\b")
    year = Date.today().year
    for page in pages_text:
        m = re.search(r"\b(20\d{2})\b", page)
        if m:
            year = int(m.group(1))
            break

    results = []
    seen: set[str] = set()

    for page in pages_text:
        for line in page.splitlines():
            line = line.strip()
            if not line or len(line) < 5:
                continue

            if line in seen:
                continue
            seen.add(line)

            confidence = predict(line, bank)
            if confidence < 0.5:
                continue

            date_m = _date_re.search(line)
            amounts = AMOUNT_RE.findall(line)

            if not date_m or not amounts:
                continue

            try:
                y = int(date_m.group(3)) if date_m.group(3) else year
                txn_date = Date(y, int(date_m.group(2)), int(date_m.group(1)))
            except ValueError:
                continue

            amount = parse_br_amount(amounts[0])
            if not amount or amount <= 0:
                continue

            # Description: everything before the first amount, date stripped
            first_amount_pos = line.index(amounts[0])
            desc = line[:first_amount_pos].strip(" -")
            desc = _date_re.sub("", desc).strip(" -")

            results.append({
                "index": len(results),
                "date": txn_date.isoformat(),
                "description": desc or line[:60],
                "amount": str(amount),
                "line_raw": line,
                "confidence": round(confidence, 3),
            })

    return results
