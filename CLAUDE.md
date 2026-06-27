# CLAUDE.md

## Contexto

Reescrita do [debt-tracker](https://github.com/wlcvs/debt-tracker) (Next.js) em Django.
O plano de trabalho completo está no **GitHub Project** deste repositório — abra lá para ver o estado atual antes de começar qualquer sessão.

## O que o app faz

Rastreador pessoal de dívidas. O admin (Wallacy) cadastra devedores e registra dívidas e pagamentos. Cada devedor tem um `id` que serve como código de acesso para uma view pública read-only em `/public/<id>/`.

## Stack

| Camada | Tecnologia |
|---|---|
| Framework | Django 5 (Python 3.12+) |
| Banco | PostgreSQL — Docker localmente / Neon em produção |
| Auth | Django built-in (session + `django.contrib.auth`) |
| Estilos | Tailwind CSS 4 (via CDN ou Vite) |
| Templates | Django templates |
| Testes | pytest + pytest-django |

## Comandos

```bash
# Ambiente virtual
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# DB
docker compose up -d
python manage.py migrate
python manage.py createsuperuser   # ou: python manage.py seed

# Dev
python manage.py runserver

# Testes
pytest
```

## Estrutura do projeto

```
debt_tracker/         # config Django (settings, urls, wsgi)
tracker/              # app principal
  models.py           # Person, CreditCard, Debt, Payment
  views.py            # dashboard, person_detail, public_view, login
  urls.py
  forms.py
  templates/tracker/
  tests/
manage.py
requirements.txt
docker-compose.yml
```

## Modelos (equivalentes ao Prisma original)

```
User       — Django built-in (AbstractUser ou default User)
Person     — id (UUID, serve como access code), name, user FK
CreditCard — label, user FK
Debt       — amount (Decimal 10,2), description, date, credit_card FK?, method (PIX|CASH)?
Payment    — amount (Decimal 10,2), date, method (PIX|CASH)
```

## Regras

- **Nunca persistir dados derivados** — saldos sempre calculados em runtime.
- **`method` em Debt** é opcional (nem toda dívida é pix/dinheiro — pode ser no cartão).
- **`method` em Payment** é PIX ou CASH, sempre obrigatório.
- **Design:** HUD/monocromático (escala de cinza, sem cores de destaque). Fundo claro `#e8e8ed`. Toggle dark/light. **UI em pt-BR.**
- **Commits:** Conventional Commits em inglês (`feat:`, `fix:`, `chore:`…).
- **Nunca fazer deploy** sem Wallacy revisar a feature primeiro.
- **Simples** — app de admin único, sem overengineering.

## Referências

- Repositório original (Next.js): https://github.com/wlcvs/debt-tracker
- GitHub Project (kanban do rewrite): veja a aba **Projects** neste repositório
