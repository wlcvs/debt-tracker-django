"""
Feature extraction for bank PDF text lines.

Each line is converted to a numeric vector used by the classifier
to decide whether it represents a financial transaction.
"""
import re

_AMOUNT_RE = re.compile(r"\d{1,3}(?:\.\d{3})*,\d{2}")
_DATE_SLASH_RE = re.compile(r"\b\d{2}/\d{2}(?:/\d{4})?\b")
_DATE_SPACE_RE = re.compile(r"\b\d{2}\s+[A-Z]{3}\b")

_SKIP_WORDS = [
    "total", "saldo", "limite", "pagamento", "rendimento",
    "juros", "encargo", "tarifa", "iof", "vencimento", "emitida",
    "fatura", "extrato", "histórico", "resumo", "data",
]

FEATURE_NAMES = [
    "has_date_slash",
    "has_date_space",
    "starts_with_date_slash",
    "has_amount",
    "num_amounts",
    "line_length",
    "num_digits",
    "ratio_digits",
    "num_words",
    "has_skip_word",
    "has_r_dollar",
    "all_upper",
    "mixed_case",
    "starts_digit",
    "bank_nubank",
    "bank_bradesco",
    "bank_itau",
    "bank_mp",
]


def extract(line: str, bank: str = "") -> list[float]:
    ll = line.lower()
    amounts = _AMOUNT_RE.findall(line)
    words = line.split()

    has_date_slash = int(bool(_DATE_SLASH_RE.search(line)))
    has_date_space = int(bool(_DATE_SPACE_RE.search(line)))
    starts_with_date = int(bool(re.match(r"^\d{2}/\d{2}", line)))
    has_amount = int(bool(amounts))
    num_amounts = len(amounts)
    length = len(line)
    num_digits = sum(c.isdigit() for c in line)
    ratio_digits = num_digits / max(length, 1)
    num_words = len(words)
    has_skip = int(any(w in ll for w in _SKIP_WORDS))
    has_rdollar = int("R$" in line)
    all_upper = int(bool(words) and all(w.isupper() or not w.isalpha() for w in words))
    mixed_case = int(bool(re.search(r"[A-Z][a-z]", line)))
    starts_digit = int(bool(re.match(r"^\d", line)))

    bank_l = bank.lower()
    return [
        has_date_slash,
        has_date_space,
        starts_with_date,
        has_amount,
        num_amounts,
        length,
        num_digits,
        ratio_digits,
        num_words,
        has_skip,
        has_rdollar,
        all_upper,
        mixed_case,
        starts_digit,
        int("nubank" in bank_l or "nu pag" in bank_l),
        int("bradesco" in bank_l),
        int("itaú" in bank_l or "itau" in bank_l),
        int("mercado" in bank_l),
    ]
