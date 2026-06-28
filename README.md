# debt-tracker-django

A personal debt tracker — Django rewrite of the [original Next.js app](https://github.com/wlcvs/debt-tracker).

The admin registers debtors, logs debts and payments. Each debtor gets a UUID that doubles as a shareable, read-only public link at `/public/<uuid>/`.

## Stack

| Layer | Technology |
|---|---|
| Framework | Django 5 (Python 3.12+) |
| Database | PostgreSQL — Docker locally / Neon in production |
| Auth | Django built-in sessions (`django.contrib.auth`) |
| Styles | Tailwind CSS 4 via CDN |
| Templates | Django templates |
| Tests | pytest + pytest-django |

## Getting started

```bash
# Virtual environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env   # or create .env manually (see below)

# Start the database
docker compose up -d

# Run migrations and create the admin user
python manage.py migrate
python manage.py seed   # creates superuser from ADMIN_EMAIL / ADMIN_PASSWORD in .env

# Start the dev server
python manage.py runserver
```

### Required `.env` variables

```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgres://debt_tracker:debt_tracker_dev@localhost:5432/debt_tracker
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=yourpassword
```

## Running tests

```bash
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

## Data model

```
Person     — id (UUID, public access code), name, user FK
CreditCard — label, user FK
Debt       — amount (Decimal), description, date, credit_card FK (nullable), method (PIX|CASH, optional)
Payment    — amount (Decimal), date, method (PIX|CASH, required)
```

Balances are always computed at runtime — no derived data is persisted.
