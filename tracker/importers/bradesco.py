"""
Bradesco bank statement (extrato) parser.

Bradesco PDFs typically have:
  DD/MM   Histórico                  Docto       Débito      Crédito     Saldo
  10/01   PIX João Silva             123456      1.234,56                 999,00

We capture the absolute amount from either the debit or credit column.
"""
import re
from datetime import date

from .base import (
    Transaction, AMOUNT_RE, DATE_SLASH_RE,
    parse_br_amount, parse_br_date,
)


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

    m = DATE_SLASH_RE.search(raw)
    if not m:
        return None
    try:
        # Bradesco often omits the year in the date column
        txn_date = parse_br_date(int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None)
    except Exception:
        return None

    amounts = AMOUNT_RE.findall(raw)
    if not amounts:
        return None

    # In Bradesco extracts the first amount (not the balance) is usually the transaction
    amount = parse_br_amount(amounts[0])
    if not amount or amount <= 0:
        return None

    desc = _clean_description(raw, amounts)
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
                m = DATE_SLASH_RE.search(line)
                if not m:
                    continue
                try:
                    txn_date = parse_br_date(int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None)
                except Exception:
                    continue

                amounts = AMOUNT_RE.findall(line)
                if not amounts:
                    continue

                amount = parse_br_amount(amounts[0])
                if not amount or amount <= 0:
                    continue

                desc = _clean_description(line, amounts)
                if desc:
                    transactions.append(Transaction(date=txn_date, description=desc, amount=amount))

    return transactions


def _clean_description(text: str, amounts: list[str]) -> str:
    cleaned = re.sub(DATE_SLASH_RE, "", text)
    for amt in amounts:
        cleaned = cleaned.replace(amt, "", 1)
    cleaned = re.sub(r"\b\d{5,}\b", "", cleaned)  # strip doc numbers
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ·-")
    return cleaned
