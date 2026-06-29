from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import re

MONTHS_PT = {
    "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12,
}

AMOUNT_RE = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})")
DATE_SLASH_RE = re.compile(r"\b(\d{2})/(\d{2})(?:/(\d{2,4}))?\b")
DATE_PT_RE = re.compile(r"\b(\d{1,2})\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\b", re.IGNORECASE)


@dataclass
class Transaction:
    date: date
    description: str
    amount: Decimal

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "description": self.description,
            "amount": str(self.amount),
        }


def parse_br_amount(s: str) -> Decimal | None:
    """'1.234,56' → Decimal('1234.56')"""
    try:
        normalized = s.replace(".", "").replace(",", ".")
        return Decimal(normalized)
    except InvalidOperation:
        return None


def parse_br_date(day: int, month: int, year: int | None = None) -> date:
    if year is None:
        year = date.today().year
    if year < 100:
        year += 2000
    return date(year, month, day)


def extract_text_pages(pdf_path) -> list[str]:
    """Return list of page texts from a PDF file-like object."""
    import pdfplumber
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return pages


def extract_tables(pdf_path) -> list[list[list[str]]]:
    """Return all tables from a PDF file-like object."""
    import pdfplumber
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                all_tables.extend(tables)
    return all_tables
