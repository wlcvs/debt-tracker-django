"""
Bradesco bank statement parser (text-based).

The Bradesco Celular export uses structured text groups:
  TRANSACTION_TYPE             (e.g. PIX ENVIADO, TED-TRANSF ELET DISPON)
  DD/MM/YYYY doc amount bal    (date + data line)
  doc amount bal               (data line without date, same date as previous)
  DES: Description DD/MM       (optional PIX description)
  REMET. Sender name           (optional TED sender)

The first amount on the data line is always used.
Amounts < R$0.05 (interest/rounding) are ignored.
"""
import re
from datetime import date as Date
from decimal import Decimal

from .base import Transaction, AMOUNT_RE, parse_br_amount

_DATE_LINE_RE = re.compile(r'^(\d{2}/\d{2}/\d{4})(.*)')

_SKIP_STARTS = ('Bradesco ', 'Data Histórico', 'Nome:', 'Total ', 'Extrato de:', 'Data:')
_SKIP_CONTAINS = ('Movimentação entre',)
_DETAIL_STARTS = ('CONTR ', 'Folha:')


def parse(pdf_file) -> list[Transaction]:
    return _parse_text(pdf_file)


def _parse_text(pdf_file) -> list[Transaction]:
    import pdfplumber

    # Mutable dicts so DES:/REMET. lines can update the description post-hoc
    txns: list[dict] = []
    current_date = None
    pending_type = ''

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''

            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                if any(line.startswith(s) for s in _SKIP_STARTS):
                    continue
                if any(s in line for s in _SKIP_CONTAINS):
                    continue
                if any(line.startswith(s) for s in _DETAIL_STARTS):
                    continue

                # DES:/REM: — update the last transaction's description
                if line.startswith('DES:') or line.startswith('REM:'):
                    extra = re.sub(r'\s+\d{2}/\d{2}$', '', line[4:]).strip()
                    if txns and extra:
                        base = txns[-1]['base']
                        txns[-1]['desc'] = f"{base} - {extra}" if base else extra
                    continue

                # REMET. — TED sender, update the last transaction
                if line.startswith('REMET.'):
                    if txns:
                        base = txns[-1]['base']
                        txns[-1]['desc'] = f"{base} - {line[6:].strip()}" if base else line
                    continue

                # Date line: DD/MM/YYYY ...
                date_m = _DATE_LINE_RE.match(line)
                if date_m:
                    d, m, y = date_m.group(1).split('/')
                    try:
                        current_date = Date(int(y), int(m), int(d))
                    except ValueError:
                        continue

                    rest = date_m.group(2).strip()
                    amounts = AMOUNT_RE.findall(rest)
                    if len(amounts) >= 2:
                        amount = parse_br_amount(amounts[0])
                        # Extract text description (strip amounts and doc numbers)
                        rest_desc = AMOUNT_RE.sub('', rest).strip()
                        rest_desc = re.sub(r'\b\d+\b', '', rest_desc).strip(' *')
                        if rest_desc:
                            pending_type = rest_desc
                        _add(txns, current_date, pending_type, amount)
                    continue

                # Data line without date: doc amount balance
                amounts = AMOUNT_RE.findall(line)
                if len(amounts) >= 2 and re.match(r'^\d+\s', line):
                    if current_date:
                        _add(txns, current_date, pending_type, parse_br_amount(amounts[0]))
                    continue

                # Otherwise: type label for the next transaction
                pending_type = line

    return [Transaction(t['date'], t['desc'], t['amount']) for t in txns]


def _add(txns: list[dict], txn_date: Date, pending_type: str, amount: Decimal | None) -> None:
    if amount is None or amount < Decimal('0.05'):
        return
    label = pending_type or 'Transaction'
    txns.append({'date': txn_date, 'desc': label, 'base': label, 'amount': amount})
