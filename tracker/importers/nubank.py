"""
Nubank parser — two distinct formats:
- Current account (extrato): text with "DD MMM YYYY Total de..." day sections
- Credit card (fatura): single-column table, one row per transaction
"""
import re
from datetime import date as Date
from decimal import Decimal

from .base import Transaction, MONTHS_PT, parse_br_amount, extract_text_pages, extract_tables

# Current account
_DATE_HEADER_RE = re.compile(r'^(\d{2}) ([A-Z]{3}) (\d{4})')
_LINE_END_AMOUNT_RE = re.compile(r'\s(\d{1,3}(?:\.\d{3})*,\d{2})$')

_CC_SKIP = (
    'Saldo inicial', 'Saldo final', 'Rendimento', 'Total de', 'Movimentações',
    'Tem alguma dúvida', 'Caso a solução', 'Extrato gerado', 'Nu Financeira',
    'Nu Pagamentos', 'CNPJ:', 'CPF', 'O saldo', 'Não nos responsabilizamos',
    'Asseguramos', 'Wallacy Vieira da Silva', 'Agência 0001',
)

# Card: "04 MAI •••• 8119 Description [- Parcela X/Y] R$ 68,59"
_CARD_TX_RE = re.compile(r'^(\d{2} [A-Z]{3})\s+[•]+\s+\d+\s+(.+?)\s+R\$\s+([\d.,]+)')


def parse(pdf_file) -> list[Transaction]:
    pages_text = extract_text_pages(pdf_file)
    if 'Movimentações' in '\n'.join(pages_text):
        return _parse_conta_corrente(pages_text)
    pdf_file.seek(0)
    return _parse_cartao(pdf_file, pages_text)


# ── Current account ────────────────────────────────────────────────────────────

def _parse_conta_corrente(pages_text: list[str]) -> list[Transaction]:
    transactions = []
    current_date = None

    for page in pages_text:
        for line in page.splitlines():
            line = line.strip()
            if not line:
                continue

            # "01 MAI 2026 Total de saídas - 92,49" — day section header
            m = _DATE_HEADER_RE.match(line)
            if m and 'Total de' in line:
                month = MONTHS_PT.get(m.group(2))
                if month:
                    try:
                        current_date = Date(int(m.group(3)), month, int(m.group(1)))
                    except ValueError:
                        pass
                continue

            if any(line.startswith(s) for s in _CC_SKIP):
                continue

            # Transaction line ends with a BR amount
            am = _LINE_END_AMOUNT_RE.search(line)
            if am and current_date:
                amount = parse_br_amount(am.group(1))
                if amount and amount >= Decimal('0.01'):
                    desc = _clean_cc_desc(line[:am.start()].strip())
                    if desc:
                        transactions.append(Transaction(current_date, desc, amount))

    return transactions


def _clean_cc_desc(text: str) -> str:
    text = re.sub(r'\s*-\s*•+\.\d+\.\d+-••', '', text)                    # CPF mask
    text = re.sub(r'\s*-\s*\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', '', text)   # CNPJ
    text = re.sub(r'\s+-\s+[A-Z]{2}[\w\s.]+\(\d+\).*$', '', text)         # bank routing info
    text = re.sub(r'\s+-\s+[A-Z]+$', '', text)                             # trailing bank code
    return text.strip(' -•')


# ── Credit card ────────────────────────────────────────────────────────────────

def _parse_cartao(pdf_file, pages_text: list[str]) -> list[Transaction]:
    year = Date.today().year
    for page in pages_text[:3]:
        m = re.search(r'\b(20\d{2})\b', page)
        if m:
            year = int(m.group(1))
            break

    transactions = []
    tables = extract_tables(pdf_file)

    for table in tables:
        for row in table:
            if not row or not row[0]:
                continue
            cell = str(row[0]).split('\n')[0].strip()
            if 'IOF de' in cell:
                continue
            m = _CARD_TX_RE.match(cell)
            if not m:
                continue
            txn_date = _parse_short_date(m.group(1), year)
            if not txn_date:
                continue
            amount = parse_br_amount(m.group(3))
            if amount and amount > 0:
                transactions.append(Transaction(txn_date, m.group(2).strip(), amount))

    return transactions


def _parse_short_date(date_str: str, year: int) -> Date | None:
    parts = date_str.strip().split()
    if len(parts) < 2:
        return None
    try:
        month = MONTHS_PT.get(parts[1].upper()[:3])
        if not month:
            return None
        return Date(year, month, int(parts[0]))
    except (ValueError, TypeError):
        return None
