"""
Mercado Pago credit card statement parser.

PDF format (text, page 2):
  22/04 MP*CARLOSJORGEMA Parcela 2 de 3 R$ 111,23
  08/06 SUPERMERCADO PORTO SEG R$ 195,23

Payment lines ("Pagamento da fatura...") are skipped.
"""
import re
from datetime import date as Date

from .base import Transaction, parse_br_amount, extract_text_pages

_TX_RE = re.compile(r'^(\d{2}/\d{2})\s+(.+?)\s+R\$\s+([\d.,]+)$')
_YEAR_RE = re.compile(r'(?:Emitida em|Vence em|Vencimento)[:\s]+\d{2}/\d{2}/(\d{4})')

_SKIP = (
    'Pagamento da fatura',
    'Data Movimentações',
    'Movimentações na fatura',
    'Detalhes de consumo',
    'Total R$',
    'Cartão Visa',
    'Cartão Mastercard',
    'Cartão Elo',
)


def parse(pdf_file) -> list[Transaction]:
    pages_text = extract_text_pages(pdf_file)
    year = _detect_year(pages_text)
    return _parse_text(pages_text, year)


def _detect_year(pages_text: list[str]) -> int:
    for page in pages_text:
        m = _YEAR_RE.search(page)
        if m:
            return int(m.group(1))
    return Date.today().year


def _parse_text(pages_text: list[str], year: int) -> list[Transaction]:
    transactions = []

    for page in pages_text:
        for line in page.splitlines():
            line = line.strip()
            if not line:
                continue
            if any(s in line for s in _SKIP):
                continue

            m = _TX_RE.match(line)
            if not m:
                continue

            dd, mm = m.group(1).split('/')
            desc = m.group(2).strip()
            amount = parse_br_amount(m.group(3))

            if amount and amount > 0:
                try:
                    transactions.append(Transaction(
                        date=Date(year, int(mm), int(dd)),
                        description=desc,
                        amount=amount,
                    ))
                except ValueError:
                    pass

    return transactions
