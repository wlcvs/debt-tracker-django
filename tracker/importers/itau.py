"""
Itaú parser — suporta dois formatos:
- Extrato de conta corrente: tabela com colunas Data / Histórico / Valor D/C
- Fatura de cartão: texto com seção "DATA ESTABELECIMENTO VALOREMR$"

Nota: faturas têm layout de duas colunas mescladas pelo pdfplumber;
a transação real fica na coluna esquerda, encargos na direita.
"""
import re
from datetime import date as Date

from .base import (
    Transaction, AMOUNT_RE, DATE_SLASH_RE,
    parse_br_amount, parse_br_date,
    extract_tables, extract_text_pages,
)

DEBIT_CREDIT_RE = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*([DC])\b")
_TX_START_RE = re.compile(r"^(\d{2}/\d{2})\s+(.+)")


def parse(pdf_file) -> list[Transaction]:
    pages_text = extract_text_pages(pdf_file)
    full = "\n".join(pages_text)

    # Fatura de cartão: tem seção "DATA ESTABELECIMENTO"
    if "DATA" in full and "ESTABELECIMENTO" in full:
        return _parse_fatura(pages_text)

    pdf_file.seek(0)
    transactions = _parse_tables(pdf_file)
    if transactions:
        return transactions

    pdf_file.seek(0)
    return _parse_text(pdf_file)


def _parse_fatura(pages_text: list[str]) -> list[Transaction]:
    """Extrai lançamentos da seção de compras/saques da fatura Itaú."""
    transactions = []
    year = Date.today().year

    for page in pages_text:
        # Tenta capturar o ano da página
        y_m = re.search(r"\b(20\d{2})\b", page)
        if y_m:
            year = int(y_m.group(1))

        in_tx_section = False
        pending_date = None
        pending_desc = ""
        pending_amount = None

        for line in page.splitlines():
            line = line.strip()
            if not line:
                continue

            # Início da seção de lançamentos
            if "DATA" in line and "ESTABELECIMENTO" in line:
                in_tx_section = True
                continue

            # Fim da seção (subtotais)
            if in_tx_section and re.search(r"Totalandos|Lançamentosno|LTotaldos|Totaldoslançamentos", line):
                _flush(transactions, pending_date, pending_desc, pending_amount)
                pending_date = pending_desc = None
                pending_amount = None
                in_tx_section = False
                continue

            if not in_tx_section:
                continue

            m = _TX_START_RE.match(line)
            if m:
                # Salva transação anterior
                _flush(transactions, pending_date, pending_desc, pending_amount)

                date_str, rest = m.group(1), m.group(2)
                amounts = AMOUNT_RE.findall(rest)
                if amounts:
                    pending_amount = parse_br_amount(amounts[0])
                    # Descrição é tudo antes do primeiro valor
                    cut = rest.index(amounts[0])
                    pending_desc = rest[:cut].strip()
                else:
                    pending_desc = rest.strip()
                    pending_amount = None

                dd, mm = date_str.split("/")
                try:
                    pending_date = Date(year, int(mm), int(dd))
                except ValueError:
                    pending_date = None

            elif pending_date:
                # Linha de continuação: pega só as palavras em CAIXA ALTA antes
                # do primeiro token com letras minúsculas (coluna direita comprimida)
                # ex: "MORADIA.FRANCODAROC ETotaldeencargosemR$ 322,59"
                #      → "MORADIA.FRANCODAROC"
                clean_words = []
                for w in line.split():
                    if AMOUNT_RE.fullmatch(w):
                        break  # valor → coluna direita
                    if re.search(r"[a-z]", w):
                        break  # texto comprimido (camelCase) → coluna direita
                    clean_words.append(w)
                if clean_words:
                    pending_desc = (pending_desc + " " + " ".join(clean_words)).strip()

        _flush(transactions, pending_date, pending_desc, pending_amount)

    return transactions


def _flush(transactions, date, desc, amount):
    if date and amount and amount > 0:
        desc = (desc or "Transação").strip(" -•")
        transactions.append(Transaction(date=date, description=desc, amount=amount))


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
    return Transaction(date=txn_date, description=desc, amount=amount) if desc else None


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
