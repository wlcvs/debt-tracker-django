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

# Tests
pytest
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
/public/                   → debtor access: enter UUID code
/public/<uuid>/            → read-only public view for a debtor
/dashboard/                → admin dashboard
/dashboard/person/<uuid>/  → person detail
/dashboard/person/<uuid>/edit|delete/
/dashboard/person/<uuid>/debt/add/
/dashboard/person/<uuid>/debt/<id>/edit|delete/
/dashboard/person/<uuid>/payment/add/
/dashboard/person/<uuid>/payment/<id>/edit|delete/
/dashboard/credit-card/add|edit|delete/
```

## Models

```
User       — Django built-in
Person     — id (UUID, serves as access code), name, user FK
CreditCard — label, user FK
Debt       — amount (Decimal 10,2), description, date, credit_card FK (nullable), method (PIX|CASH, optional)
Payment    — amount (Decimal 10,2), date, method (PIX|CASH, required)
```

## Rules

- **Never persist derived data** — balances are always computed at runtime.
- **`method` on Debt** is optional (not every debt is PIX/CASH — it may be on a card).
- **`method` on Payment** is PIX or CASH, always required.
- **Credit cards with linked debts cannot be deleted.**
- **Design:** HUD/monochromatic (grayscale, no accent colors). Light background `#f0f0f4`. Dark/light toggle. **UI in pt-BR.**
- **Commits:** Conventional Commits in English (`feat:`, `fix:`, `chore:`…).
- **Simple** — single-admin app, no overengineering.
- **Alpine.js patterns:** interactive state (inline edits, add forms, modal) uses `x-data` per component. Global state lives in `Alpine.store('theme')` and `Alpine.store('modal')`. All directives require an `x-data` ancestor. Form reset on close via `$watch('open', v => !v && $refs.form.reset())`. Focus trap in modal via `x-trap.inert.noscroll` from `@alpinejs/focus`.

## References

- Original repository (Next.js): https://github.com/wlcvs/debt-tracker
- GitHub Project (rewrite kanban): see the **Projects** tab on this repository
