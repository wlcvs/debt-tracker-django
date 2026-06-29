"""
Itaú bank statement (extrato) parser.

Itaú PDFs typically have a tabular format:
  Data        Histórico                      Docto     Valor
  10/01/2024  PIX Enviado - Nome             123456    1.234,56 D

'D' = débito (saída), 'C' = crédito (entrada).
We include both; the admin decides what's relevant.
"""
import re
from datetime import date

from .base import (
    Transaction, AMOUNT_RE, DATE_SLASH_RE,
    parse_br_amount, parse_br_date,
    extract_tables,
)

DEBIT_CREDIT_RE = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*([DC])\b")


def parse(pdf_file) -> list[Transaction]:
    # Fatura do Itaú (boleto/resumo) não contém transações individuais listadas.
    # O texto fica comprimido (sem espaços) e não há tabela de lançamentos.
    from .base import extract_text_pages
    pages_text = extract_text_pages(pdf_file)
    full = ''.join(pages_text)
    if 'Totaldestafatura' in full or 'ResumodafaturaemR$' in full:
        return []

    pdf_file.seek(0)
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
        txn_date = parse_br_date(int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None)
    except Exception:
        return None

    m_amt = DEBIT_CREDIT_RE.search(raw)
    if m_amt:
        amount = parse_br_amount(m_amt.group(1))
    else:
        amounts = AMOUNT_RE.findall(raw)
        amount = parse_br_amount(amounts[-1]) if amounts else None

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
                m = DATE_SLASH_RE.search(line)
                if not m:
                    continue
                try:
                    txn_date = parse_br_date(int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None)
                except Exception:
                    continue

                m_amt = DEBIT_CREDIT_RE.search(line)
                if m_amt:
                    amount = parse_br_amount(m_amt.group(1))
                else:
                    amounts = AMOUNT_RE.findall(line)
                    amount = parse_br_amount(amounts[-1]) if amounts else None

                if not amount or amount <= 0:
                    continue

                desc = _clean_description(line)
                if desc:
                    transactions.append(Transaction(date=txn_date, description=desc, amount=amount))

    return transactions


def _clean_description(text: str) -> str:
    cleaned = re.sub(DATE_SLASH_RE, "", text)
    cleaned = re.sub(DEBIT_CREDIT_RE, "", cleaned)
    cleaned = re.sub(AMOUNT_RE, "", cleaned)
    cleaned = re.sub(r"\b[DC]\b", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ·-")
    return cleaned
