"""
Extrai linhas brutas de um PDF e classifica cada uma com o algoritmo
existente E com o modelo ML, retornando ambos os resultados.

Formato de saída de cada lista:
  {
    "index": int,
    "date":  "YYYY-MM-DD",
    "description": str,
    "amount": str,         # Decimal como string
    "line_raw": str,       # linha original do PDF (para treinamento)
    "confidence": float,   # probabilidade do modelo (0–1)
  }
"""
from __future__ import annotations

import io
from datetime import date as Date

from tracker.importers import detect_and_parse
from tracker.importers.base import extract_text_pages, AMOUNT_RE, parse_br_amount
from tracker.ml import predict, is_trained


def run_algorithm(pdf_bytes: bytes, bank_hint: str = "") -> tuple[str, list[dict]]:
    """Roda o parser existente e retorna (banco, transações)."""
    f = io.BytesIO(pdf_bytes)
    bank, txns = detect_and_parse(f)
    results = [
        {
            "index": i,
            "date": t.date.isoformat(),
            "description": t.description,
            "amount": str(t.amount),
            "line_raw": "",   # parser não expõe a linha original
            "confidence": 1.0,
        }
        for i, t in enumerate(txns)
    ]
    return bank, results


def run_model(pdf_bytes: bytes, bank: str) -> list[dict]:
    """
    Passa cada linha do PDF pelo modelo ML e retorna as que o modelo
    acredita serem transações (confiança >= 0.5).

    Cada resultado inclui a linha bruta e o que foi possível extrair
    com regex simples (data DD/MM, primeiro valor BR).
    """
    import re
    from datetime import date as Date

    pages_text = extract_text_pages(io.BytesIO(pdf_bytes))

    _date_re = re.compile(r"\b(\d{2})/(\d{2})(?:/(\d{4}))?\b")
    year = Date.today().year
    for page in pages_text:
        m = re.search(r"\b(20\d{2})\b", page)
        if m:
            year = int(m.group(1))
            break

    results = []
    seen = set()

    for page in pages_text:
        for line in page.splitlines():
            line = line.strip()
            if not line or len(line) < 5:
                continue

            # Evita duplicatas exatas
            if line in seen:
                continue
            seen.add(line)

            confidence = predict(line, bank)
            if confidence < 0.5:
                continue

            # Extrai campos básicos via regex
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

            # Descrição: tudo antes do primeiro valor
            first_amount_pos = line.index(amounts[0])
            desc = line[:first_amount_pos].strip(" -")
            # Remove a data da descrição
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
