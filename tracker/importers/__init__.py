"""
Bank statement importers.

detect_and_parse(pdf_file) → (bank_name, [Transaction])

Detects the bank from the PDF text and delegates to the appropriate parser.
Falls back to a generic pattern-based parser if the bank is unrecognised.
"""
from .base import Transaction, extract_text_pages
from . import nubank, itau, mercadopago, bradesco


def detect_and_parse(pdf_file) -> tuple[str, list[Transaction]]:
    pages = extract_text_pages(pdf_file)
    full_text = "\n".join(pages).lower()

    pdf_file.seek(0)

    # Nubank antes do Bradesco: extratos Nubank mencionam "BCO BRADESCO S.A."
    # nas transferências, o que causaria falsa detecção se Bradesco viesse primeiro
    if "nubank" in full_text or "nu pagamentos" in full_text:
        return "Nubank", nubank.parse(pdf_file)

    # "bradesco celular" é específico do app do Bradesco; "bradesco" sozinho
    # pode aparecer como referência em extratos de outros bancos
    if "bradesco celular" in full_text or "banco bradesco" in full_text:
        return "Bradesco", bradesco.parse(pdf_file)

    if "itaú" in full_text or "itau" in full_text or "banco itaú" in full_text:
        return "Itaú", itau.parse(pdf_file)

    if "mercado pago" in full_text or "mercadopago" in full_text:
        return "Mercado Pago", mercadopago.parse(pdf_file)

    # Último recurso para Bradesco sem o cabeçalho "Celular"
    if "bradesco" in full_text:
        return "Bradesco", bradesco.parse(pdf_file)

    # Generic fallback — tries all parsers and returns the most results
    pdf_file.seek(0)
    results = []
    for name, module in [("Nubank", nubank), ("Itaú", itau), ("Mercado Pago", mercadopago), ("Bradesco", bradesco)]:
        pdf_file.seek(0)
        try:
            txns = module.parse(pdf_file)
            results.append((name, txns))
        except Exception:
            pass

    if results:
        best = max(results, key=lambda x: len(x[1]))
        if best[1]:
            return best[0] + " (detectado)", best[1]

    return "Desconhecido", []
