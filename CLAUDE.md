# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Django web app (MadeireiraJD) for managing timber sales ("romaneios"): clients, drivers, wood types, payments, client balances, and reports. UI is in Brazilian Portuguese; code, models, and DB fields use Portuguese names. Bootstrap 5 templates, Class-Based Views, PostgreSQL in production.

## Commands

The repo ships a `venv/` — activate it first: `source venv/bin/activate`.

```sh
# Run dev server (uses config.settings, reads .env)
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Tests — ALWAYS use the test settings (SQLite in-memory, fast hashers, locmem email)
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test -v 2

# Run a single app / module / test
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test apps.romaneio
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test apps.romaneio.tests.test_romaneio_models
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test apps.romaneio.tests.test_romaneio_models.ClassName.test_method

# Seed sample data
python manage.py mock_dados

# Production checks
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Default `config.settings` connects to PostgreSQL (default port **5433**, not 5432). Without a database, only `config.settings_test` will run. Tests do not auto-load test settings — you must pass `DJANGO_SETTINGS_MODULE=config.settings_test` explicitly.

## Architecture

Five apps under `apps/`, each a standard Django app with its own `models.py`, `views.py`, `urls.py`, `forms.py`, `templates/`, and `tests/`:

- **cadastros** — master data: `Cliente`, `TipoMadeira`, `Motorista`, plus operator user management.
- **romaneio** — the core sales document and its line items.
- **financeiro** — `Pagamento` (payments/advances).
- **relatorios** — dashboard + reports + exports; mounted at the site root (`/`).
- **core** — custom auth backend, password-reset views, abstract `BaseModel`, `ConfiguracaoGeral` key/value config.

URLs are namespaced (`relatorios:`, `cadastros:`, `romaneio:`, `financeiro:`, `core:`) and wired in [config/urls.py](config/urls.py). Auth (login/logout/password reset) lives at the project level under `/accounts/`.

### Romaneio totals (the central money logic)

Lives in [apps/romaneio/models.py](apps/romaneio/models.py). A `Romaneio` has `ItemRomaneio` line items; in DETALHADO mode each item also has `UnidadeRomaneio` rows.

- **Two modalidades**: `SIMPLES` (user enters `quantidade_m3_total` directly per item) and `DETALHADO` (item m³ is summed from `UnidadeRomaneio`, each computed from `comprimento`/`rodo`/descontos via `calcular_m3_detalhado()`).
- **Two tipo_romaneio**: `NORMAL` / `COM_FRETE` — selects which price (`preco_normal` vs `preco_com_frete`) `TipoMadeira.get_preco()` returns.
- Totals cascade upward via `atualizar_totais()`: `UnidadeRomaneio.save/delete` → `ItemRomaneio.atualizar_totais()` → `Romaneio.atualizar_totais()`. The `save()`/`delete()` overrides keep these in sync, so prefer the ORM save/delete path over bulk operations that bypass them.
- `valor_bruto` = sum of items; `valor_total` = net after the romaneio's `desconto` percentage; `m3_total` = sum of item m³. These three fields are `editable=False` and always derived — never set them by hand.
- All money/m³ math uses `Decimal` with `ROUND_HALF_UP` and fixed quantization steps (`VALOR_STEP` = 0.01, `QTD_M3_STEP` = 0.001).

### Client balance (saldo)

`Cliente.saldo_atual` (property in [apps/cadastros/models.py](apps/cadastros/models.py)) = total payments − total sales (`valor_total`). **Never persisted** — always computed live. Negative = client owes money. There is no manual balance adjustment; this is a deliberate rule for traceability. The `atualizar_saldo()` method is legacy — use `saldo_atual`.

### Reports & exports

[apps/relatorios/views.py](apps/relatorios/views.py) re-exports the four report views/exports from split modules (`views_ficha_romaneio.py`, `views_ficha_madeira.py`, `views_fluxo_financeiro.py`, `views_saldo_cliente.py`) — edit the per-report module, not the aggregator. Shared filter helpers (`parse_mes_ano`, `apply_mes_ano_filter`, `get_periodo_filtro`, `safe_filename`) are in [apps/relatorios/utils.py](apps/relatorios/utils.py); reports filter by month/year (+ optional client).

- **Excel** exports use `openpyxl`. **PDF** exports render an HTML template then `weasyprint.HTML(...).write_pdf()` (imported lazily inside the view; `reportlab` is a fallback). WeasyPrint needs native system libs (cairo/pango/etc. — see `requirements.txt` header); PDF views degrade gracefully if it's unavailable.

### Auth

`apps.core.auth_backends.UsernameOrEmailBackend` lets users log in with username **or** email. Password reset is the standard Django flow with custom templates in `templates/registration/` and `SITE_DOMAIN`/`SITE_PROTOCOL` from `.env` for building email links.

## Conventions

- Keep money/m³ in `Decimal`, quantize with the existing `*_STEP` constants and `ROUND_HALF_UP`; don't introduce floats into the totals/saldo path.
- Use `timezone.localdate()` (settings are `USE_TZ=True`, `TIME_ZONE=America/Sao_Paulo`); date locale formatting relies on `USE_L10N` + pt-BR separators.
- New reports follow the existing `views_*.py` + template + Excel/PDF export pattern and reuse the `utils.py` filter helpers.
- Tests use plain `unittest`-style Django `TestCase` with factory helpers in [apps/tests/factories.py](apps/tests/factories.py) (`create_cliente`, `create_romaneio`, etc.) — no factory_boy/pytest.

## Deployment

Push to `main` triggers [.github/workflows/deploy.yml](.github/workflows/deploy.yml): SSH to the VPS, `git pull`, install requirements into the existing `venv`, `migrate`, `collectstatic`, and restart the `gunicorn_romaneios` systemd service. The venv must already exist on the server.
