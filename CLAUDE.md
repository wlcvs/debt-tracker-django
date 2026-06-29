# CLAUDE.md

## Context

Django rewrite of [debt-tracker](https://github.com/wlcvs/debt-tracker) (Next.js).
Check the **GitHub Project** tab on this repository before starting any session to see the current work state.

## What the app does

Personal debt tracker. The admin (Wallacy) registers debtors and records debts and payments. Each debtor has a UUID `id` that serves as an access code for a read-only public view at `/public/<id>/`.

## Stack

| Layer | Technology |
|---|---|
| Framework | Django 5 (Python 3.12+) |
| Database | PostgreSQL — Docker locally / Neon in production |
| Auth | Django built-in (session + `django.contrib.auth`) |
| Styles | Tailwind CSS 4 (via CDN) |
| JS | Alpine.js 3 + @alpinejs/focus (via CDN) |
| Templates | Django templates |
| Tests | pytest + pytest-django |

## Commands

```bash
# Virtual environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# DB
docker compose up -d
python manage.py migrate
python manage.py seed   # creates superuser from ADMIN_EMAIL / ADMIN_PASSWORD in .env

# Dev
python manage.py runserver
python manage.py runserver 0.0.0.0:8000   # accessible on local network (mobile testing)

# Tests
pytest tracker/tests/ -q   # use explicit path to avoid conflict with tracker/tests.py stub
```

## Project structure

```
debt_tracker/         # Django config (settings, urls, wsgi)
tracker/              # Main app
  models.py           # Person, CreditCard, Debt, Payment
  views.py
  urls.py
  forms.py
  templates/tracker/
  tests/
manage.py
requirements.txt
docker-compose.yml
```

## URL structure

```
/                          → redirects to /public/
/login/                    → login (redirects to /dashboard/ if already logged in)
/logout/
/public/                   → debtor access: enter UUID code ("Consultar dívida")
/public/<uuid>/            → read-only public view for a debtor ("Minha Dívida")
/dashboard/                → admin dashboard
/dashboard/person/<uuid>/  → person detail
/dashboard/person/<uuid>/edit|delete/
/dashboard/person/<uuid>/debt/add/
/dashboard/person/<uuid>/debt/<id>/edit|delete|toggle-paid/
/dashboard/person/<uuid>/payment/add/
/dashboard/person/<uuid>/payment/<id>/edit|delete/
/dashboard/credit-card/add|edit|delete/
/dashboard/import/         → POST PDF → returns bank + transactions JSON
/dashboard/import/save/    → POST selected items → creates Debt/Payment records
```

## Models

```
User       — Django built-in
Person     — id (UUID, serves as access code), name, user FK
CreditCard — label, user FK
Debt       — amount (Decimal 10,2), title (required), description (optional), date, credit_card FK (nullable), method (PIX|CASH, optional), paid (bool, default False)
Payment    — amount (Decimal 10,2), description (optional), date, method (PIX|CASH, required)
```

## Rules

- **Never persist derived data** — balances are always computed at runtime.
- **`method` on Debt** is optional (not every debt is PIX/CASH — it may be on a card).
- **`method` on Payment** is PIX or CASH, always required.
- **`title` on Debt** is required (CharField max_length=255).
- **`paid` on Debt** toggles whether the debt counts toward the balance (excluded from sum when True).
- **`description` on both Debt and Payment** is optional (blank=True, default="").
- **Credit cards with linked debts cannot be deleted.**
- **Design:** HUD/monochromatic (grayscale, no accent colors). Light background `#f0f0f4`. Dark/light toggle. **UI in pt-BR.**
- **Commits:** Conventional Commits in English (`feat:`, `fix:`, `chore:`…).
- **Simple** — single-admin app, no overengineering.

## Template architecture

- `base.html` — root HTML shell. Defines `{% block header %}` (default: Debt Tracker + theme toggle), `{% block body %}`, Alpine stores (`theme`, `modal`), and custom form validation.
- `app_base.html` — extends `base.html`. Overrides `{% block header %}` with nav (back link + logout). Contains `{% block content %}` inside a `<main>` and the global delete confirmation modal.
- Page templates extend either `app_base.html` (dashboard pages) or `base.html` (login, public, 404).

## Alpine.js patterns

- Interactive state (inline edits, add forms, modals) uses `x-data` per component.
- Global state: `Alpine.store('theme')` and `Alpine.store('modal')`.
- All directives require an `x-data` ancestor.
- Form reset on close: `$watch('open', v => { if (!v) reset(); })` with a `reset()` method.
- Focus trap in modals: `x-trap.inert.noscroll` from `@alpinejs/focus`.
- Detail modals via `x-teleport="body"` — escapes parent stacking contexts while keeping Alpine data scope.
- Custom select: hidden `<input type="hidden" :value="method">` + Alpine dropdown + `@submit` validation (required because hidden inputs don't trigger native `required`).
- Modals are always centered (`items-center p-4`), on all screen sizes.
- Share button: `navigator.share()` on HTTPS, `document.execCommand('copy')` fallback for HTTP.
- Collapsible filter panels: put `@click.outside` and `@keydown.escape.window` on a **wrapper div** that contains both the toggle button and the panel — never on the panel alone, or the toggle click immediately re-closes it.
- Incremental filtering with `x-show`: pass reactive state variables as explicit arguments to the filter function so Alpine tracks them as dependencies. Accessing them only inside the function body via `this.x` is not reliable.
- Number filters: when the user omits a decimal point, compare by `Math.floor(amount)` to avoid excluding e.g. `222.70` when the input is `222`.
- **Embedding JSON in `x-data`**: never put raw Django JSON directly in an HTML attribute. Use `{{ var|json_script:"element-id" }}` to output a `<script type="application/json">` tag, then read it in JS with `JSON.parse(document.getElementById('element-id').textContent)`. Raw JSON breaks the attribute because its `"` characters terminate the attribute string.
- **Triggering modals across Alpine scope boundaries**: use plain `onclick="window.dispatchEvent(new CustomEvent('event-name'))"` on the trigger button and `@event-name.window="open = true"` on the modal component. Avoids dependency on Alpine context in the trigger.

## Bank statement import

PDF upload feature at `/dashboard/import/`. Logic lives in `tracker/importers/`:
- `base.py` — `Transaction` dataclass, BR amount/date parsers, pdfplumber utils
- `nubank.py`, `itau.py`, `mercadopago.py`, `bradesco.py` — bank-specific parsers (table-first, text fallback)
- `__init__.py` — `detect_and_parse(pdf_file)` auto-detects bank from PDF content

Store local PDFs in `extratos/` (gitignored for `*.pdf` / `*.PDF`). Parsers may need adjustment per actual PDF format — test by dropping a PDF in `extratos/` and hitting the upload UI.

## References

- Original repository (Next.js): https://github.com/wlcvs/debt-tracker
- GitHub Project (rewrite kanban): see the **Projects** tab on this repository
