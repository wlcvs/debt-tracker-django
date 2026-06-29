"""
Mercado Pago statement parser.

Mercado Pago PDFs typically show:
  DD/MM/YYYY HH:MM   Descrição   +R$ X.XXX,XX  or  -R$ X.XXX,XX

Or in table form with columns for date, description, type, amount.
We capture the absolute amount; direction (+ / -) is informational.
"""
import re
from datetime import date

from .base import (
    Transaction, AMOUNT_RE, DATE_SLASH_RE,
    parse_br_amount, parse_br_date,
)

DATETIME_RE = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\s+\d{2}:\d{2}\b")
SIGNED_AMOUNT_RE = re.compile(r"[+\-−]?\s*R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})")


def parse(pdf_file) -> list[Transaction]:
    transactions = _parse_tables(pdf_file)
    if transactions:
        return transactions

    pdf_file.seek(0)
    return _parse_text(pdf_file)


def _parse_tables(pdf_file) -> list[Transaction]:
    import pdfplumber
    transactions = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    row = [str(c or "").strip() for c in row]
                    txn = _row_to_transaction(row)
                    if txn:
                        transactions.append(txn)
    return transactions


def _row_to_transaction(row: list[str]) -> Transaction | None:
    raw = " ".join(row)

    txn_date = _find_date(raw)
    if txn_date is None:
        return None

    m_amt = SIGNED_AMOUNT_RE.search(raw)
    if not m_amt:
        return None
    amount = parse_br_amount(m_amt.group(1))
    if not amount or amount <= 0:
        return None

    desc = _clean_description(raw)
    if not desc:
        return None

    return Transaction(date=txn_date, description=desc, amount=amount)


def _parse_text(pdf_file) -> list[Transaction]:
    import pdfplumber
    transactions = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                txn_date = _find_date(line)
                if not txn_date:
                    continue
                m_amt = SIGNED_AMOUNT_RE.search(line)
                if not m_amt:
                    continue
                amount = parse_br_amount(m_amt.group(1))
                if not amount or amount <= 0:
                    continue
                desc = _clean_description(line)
                if desc:
                    transactions.append(Transaction(date=txn_date, description=desc, amount=amount))
    return transactions


def _find_date(text: str) -> date | None:
    m = DATETIME_RE.search(text)
    if m:
        try:
            return parse_br_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass
    m = DATE_SLASH_RE.search(text)
    if m:
        try:
            return parse_br_date(int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None)
        except Exception:
            pass
    return None


def _clean_description(text: str) -> str:
    cleaned = re.sub(DATETIME_RE, "", text)
    cleaned = re.sub(DATE_SLASH_RE, "", cleaned)
    cleaned = re.sub(SIGNED_AMOUNT_RE, "", cleaned)
    cleaned = re.sub(r"R\$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ·+-")
    return cleaned
