"""
Nubank credit card statement (fatura) parser.

Nubank PDFs typically have transactions listed as:
  DD MMM   Descrição                        R$ X.XXX,XX

Some versions use a table, others use free text.
The parser tries table extraction first, then falls back to text parsing.
"""
import re
from datetime import date
from decimal import Decimal

from .base import (
    Transaction, AMOUNT_RE, DATE_PT_RE, MONTHS_PT,
    parse_br_amount, parse_br_date,
    extract_text_pages, extract_tables,
)

# Nubank sometimes formats dates as "10 JAN" or "10/01"
DATE_NUBANK_RE = re.compile(
    r"\b(\d{1,2})\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\b",
    re.IGNORECASE,
)
DATE_SLASH_RE = re.compile(r"\b(\d{2})/(\d{2})(?:/(\d{2,4}))?\b")


def parse(pdf_file) -> list[Transaction]:
    # Try table-based extraction first
    transactions = _parse_tables(pdf_file)
    if transactions:
        return transactions

    # Fallback: text-based line parsing
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
    """Try to extract a Transaction from a table row."""
    raw = " ".join(row)

    amounts = AMOUNT_RE.findall(raw)
    if not amounts:
        return None

    # Last amount column is typically the charge amount
    amount = parse_br_amount(amounts[-1])
    if amount is None or amount <= 0:
        return None

    txn_date = _find_date(raw)
    if txn_date is None:
        return None

    # Description: everything that's not a date or amount
    desc = _clean_description(raw, amounts)
    if not desc:
        return None

    return Transaction(date=txn_date, description=desc, amount=amount)


def _parse_text(pdf_file) -> list[Transaction]:
    """Line-by-line text parsing for Nubank PDFs."""
    import pdfplumber
    transactions = []
    current_date = None

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            i = 0
            while i < len(lines):
                line = lines[i]

                date_match = DATE_NUBANK_RE.search(line) or DATE_SLASH_RE.search(line)
                if date_match:
                    current_date = _find_date(line)

                amounts = AMOUNT_RE.findall(line)
                if amounts and current_date:
                    amount = parse_br_amount(amounts[-1])
                    if amount and amount > 0:
                        desc = _clean_description(line, amounts)
                        if desc:
                            transactions.append(Transaction(
                                date=current_date,
                                description=desc,
                                amount=amount,
                            ))
                i += 1

    return transactions


def _find_date(text: str) -> date | None:
    m = DATE_NUBANK_RE.search(text)
    if m:
        day = int(m.group(1))
        month = MONTHS_PT.get(m.group(2).upper(), 0)
        if month:
            return parse_br_date(day, month)

    m = DATE_SLASH_RE.search(text)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else None
        if 1 <= day <= 31 and 1 <= month <= 12:
            return parse_br_date(day, month, year)

    return None


def _clean_description(text: str, amounts: list[str]) -> str:
    cleaned = text
    for amt in amounts:
        cleaned = cleaned.replace(amt, "")
    cleaned = re.sub(r"R\$", "", cleaned)
    cleaned = DATE_NUBANK_RE.sub("", cleaned)
    cleaned = DATE_SLASH_RE.sub("", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned
