"""
HTTP client for the external LLM extraction server.

Configure LLM_BASE_URL in .env (e.g. http://localhost:8001 or an Ngrok URL).
If not set or the server is unreachable, all calls return empty results silently.
"""
import io
import json
import uuid
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


def extract(pdf_bytes: bytes, bank_hint: str = "") -> list[dict]:
    """
    Send raw PDF bytes to the LLM server and return extracted transactions.
    The server handles text extraction and LLM inference internally.

    Returns a list of dicts with keys: date, description, amount.
    """
    url = _base_url()
    if not url:
        return []

    body, content_type = _encode_multipart(
        fields={"bank": bank_hint},
        files={"pdf": ("statement.pdf", pdf_bytes, "application/pdf")},
    )
    req = urllib.request.Request(
        f"{url}/extract",
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read())
            txns = data.get("transactions", [])
            return [{"index": i, **t} for i, t in enumerate(txns)]
    except Exception:
        return []


def _encode_multipart(
    fields: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    body = io.BytesIO()

    for name, value in fields.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.write(value.encode())
        body.write(b"\r\n")

    for name, (filename, data, mime) in files.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        body.write(f"Content-Type: {mime}\r\n\r\n".encode())
        body.write(data)
        body.write(b"\r\n")

    body.write(f"--{boundary}--\r\n".encode())
    return body.getvalue(), f"multipart/form-data; boundary={boundary}"
