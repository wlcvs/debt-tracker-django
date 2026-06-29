"""
Bradesco bank statement parser (text-based).

O extrato do Bradesco Celular usa texto estruturado em grupos:
  TIPO_TRANSACAO               (ex: PIX ENVIADO, TED-TRANSF ELET DISPON)
  DD/MM/YYYY doc valor saldo   (linha de data + dados)
  doc valor saldo              (linha de dados sem data, mesma data anterior)
  DES: Descrição DD/MM         (descrição opcional do PIX)
  REMET.Nome do remetente      (remetente opcional de TED)

O valor usado é sempre o primeiro valor da linha de dados.
Valores < R$ 0,05 (juros/rendimento) são ignorados.
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

    # Cada item é um dict para permitir atualização da descrição após DES:/REMET.
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

                # DES:/REM: → atualiza descrição da última transação
                if line.startswith('DES:') or line.startswith('REM:'):
                    extra = re.sub(r'\s+\d{2}/\d{2}$', '', line[4:]).strip()
                    if txns and extra:
                        base = txns[-1]['base']
                        txns[-1]['desc'] = f"{base} - {extra}" if base else extra
                    continue

                # REMET. → remetente de TED, atualiza última transação
                if line.startswith('REMET.'):
                    if txns:
                        base = txns[-1]['base']
                        txns[-1]['desc'] = f"{base} - {line[6:].strip()}" if base else line
                    continue

                # Linha com data: DD/MM/YYYY ...
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
                        # Extrai descrição textual do resto (remove valores e números de doc)
                        rest_desc = AMOUNT_RE.sub('', rest).strip()
                        rest_desc = re.sub(r'\b\d+\b', '', rest_desc).strip(' *')
                        if rest_desc:
                            pending_type = rest_desc
                        _add(txns, current_date, pending_type, amount)
                    continue

                # Linha de dados sem data: doc valor saldo
                amounts = AMOUNT_RE.findall(line)
                if len(amounts) >= 2 and re.match(r'^\d+\s', line):
                    if current_date:
                        _add(txns, current_date, pending_type, parse_br_amount(amounts[0]))
                    continue

                # Linha de tipo para a próxima transação
                pending_type = line

    return [Transaction(t['date'], t['desc'], t['amount']) for t in txns]


def _add(txns: list[dict], txn_date: Date, pending_type: str, amount: Decimal | None) -> None:
    if amount is None or amount < Decimal('0.05'):
        return
    label = pending_type or 'Transação'
    txns.append({'date': txn_date, 'desc': label, 'base': label, 'amount': amount})
