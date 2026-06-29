"""
HTTP client for the external LLM extraction server.

Configure LLM_BASE_URL in .env (e.g. http://localhost:8001 or an Ngrok URL).
If not set or the server is unreachable, all calls return empty results silently.
"""
import json
import urllib.request
import urllib.error
from django.conf import settings


def _base_url() -> str:
    return getattr(settings, "LLM_BASE_URL", "").rstrip("/")


def health_check() -> bool:
    url = _base_url()
    if not url:
        return False
    try:
        with urllib.request.urlopen(f"{url}/health", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def extract(pages_text: list[str], bank: str) -> list[dict]:
    """
    Send PDF text to the LLM server and return extracted transactions.

    Each returned dict matches the Transaction.to_dict() format:
      {"date": "YYYY-MM-DD", "description": str, "amount": str}
    """
    url = _base_url()
    if not url:
        return []

    payload = json.dumps({"text": "\n\n".join(pages_text), "bank": bank}).encode()
    req = urllib.request.Request(
        f"{url}/extract",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            txns = data.get("transactions", [])
            return [{"index": i, **t} for i, t in enumerate(txns)]
    except Exception:
        return []
