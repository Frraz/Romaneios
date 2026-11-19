# Desenvolvimento

Como montar o ambiente local, rodar os testes e as convenções de código do projeto. Publicação e servidor estão em [operacao.md](operacao.md).

## Ambiente

Requisitos:

- Python 3.12. É a versão da produção; o Django 4.2 não suporta Python 3.13 ou mais recente.
- PostgreSQL, só para rodar o servidor local. Os testes não precisam dele.
- Para gerar PDF: bibliotecas nativas do WeasyPrint (Cairo, Pango, GDK-Pixbuf). No Ubuntu ou Debian:

  ```bash
  sudo apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi8 shared-mime-info fonts-dejavu-core fontconfig
  ```

  No Windows, use o WSL.

Criação do ambiente virtual (a pasta `venv/` está no `.gitignore`):

```bash
python3.12 -m venv venv          # ou: uv venv --python 3.12 venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env             # ajuste banco e chave
```

## Banco local

`config/settings.py` só fala com PostgreSQL. O padrão é `localhost`, porta **5433** (não a 5432). Ajuste `DB_PORT` no `.env` se o seu PostgreSQL usa a porta padrão.

```bash
sudo -u postgres createuser --pwprompt romaneios
sudo -u postgres createdb -O romaneios romaneios
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

A aplicação fica em `http://127.0.0.1:8000/`. Com `DEBUG=True`, o Django serve `/static/` e `/media/` (o logo da tela de login).

E-mail em desenvolvimento: use `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` para ver o link de redefinição de senha no terminal.

### Dados de exemplo

```bash
python manage.py mock_dados
```

Cria 60 tipos de madeira, 60 clientes, 60 motoristas, 60 usuários staff (`user_teste1`…`user_teste60`, sem senha utilizável), 200 romaneios e 200 pagamentos aleatórios. Os romaneios são criados **sem itens** e com totais aleatórios, o que contradiz a regra de totais derivados: servem para olhar telas e relatórios, não para conferir cálculos. **Nunca rode em produção** (DT-15).

## Testes

Os testes não carregam sozinhos as configurações de teste: passe `DJANGO_SETTINGS_MODULE` sempre.

```bash
# Suíte completa (SQLite em memória, sem PostgreSQL)
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test -v 2

# Uma app, um módulo, uma classe, um teste
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test apps.romaneio
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test apps.romaneio.tests.test_romaneio_models
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test apps.romaneio.tests.test_romaneio_models.RomaneioTotaisTests
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test apps.romaneio.tests.test_romaneio_models.RomaneioTotaisTests.test_item_delete_recalcula_totais_romaneio

# Verificações sem banco real
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py check
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py makemigrations --check --dry-run
```

### Estado da suíte

Medido em 2026-11-19 com Python 3.12.14 e as versões de `requirements.txt`:

- 112 testes executados, **3 falhas**, nenhum erro. As 3 falhas são testes desatualizados em relação ao código (DT-10):
  - `UsuarioViewsPermissionTests.test_usuario_list_requires_staff` e `SmokeCadastrosUrlsTests.test_cadastros_pages_load_logged_in` esperam 403. O `StaffRequiredMixin` redireciona (302) de propósito.
  - `PagamentoListViewTests.test_list_view_defaults_to_current_month_year` espera que a lista de pagamentos abra no mês atual. Ela abre com todo o histórico (pendência P-03).
- 3 testes não rodam: `apps/tests/test_requirements.py` define a classe `RequirementsImportTests` duas vezes, e a segunda substitui a primeira (DT-11).
- `check` sem problemas. `makemigrations --check` sem migrações pendentes.

Atualize esta seção quando a suíte mudar. O número de testes só aparece aqui.

### Onde ficam

| Pasta | Cobre |
|---|---|
| `apps/<app>/tests/` | Modelos e views de cada app |
| `apps/tests/` | Testes de projeto (URLs, settings, dependências) e as fábricas |

Fábricas em `apps/tests/factories.py`: `create_user`, `create_cliente`, `create_tipo_madeira`, `create_motorista`, `create_romaneiador`, `create_romaneio`, `create_item_romaneio`, `create_unidade_romaneio`, `create_pagamento`. O projeto usa `django.test.TestCase`; não usa pytest nem factory_boy (o `.vscode/settings.json` aponta para pytest, mas ele não está instalado; DT-17).

Os POSTs de criação e edição de romaneio precisam incluir o formulário de gerenciamento de cada formset de unidades (`unidades-<i>-TOTAL_FORMS` etc.), mesmo no `SIMPLES`. Veja os auxiliares em `apps/romaneio/tests/test_romaneio_views.py`.

`apps/tests/test_requirements.py` importa o `weasyprint`: sem as bibliotecas nativas, esse teste falha.

## Convenções

- **Dinheiro e m³ em `Decimal`**, com `ROUND_HALF_UP` e as constantes `VALOR_STEP` (`0.01`) e `QTD_M3_STEP` (`0.001`) de `apps/romaneio/models.py`. Nada de `float` no cálculo de totais ou saldo. (As exportações em CSV convertem para `float` só para formatar o texto.)
- **Totais pelo ORM.** Salve e exclua itens e unidades com `save()`/`delete()` de cada objeto, para a cascata de totais rodar. Veja [arquitetura.md](arquitetura.md#cascata-dos-totais).
- **Saldo sempre por `Cliente.saldo_atual`** ou pela mesma fórmula em agregação. `Cliente.atualizar_saldo()` é legado.
- **Datas:** `timezone.localdate()` e `timezone.localtime()` (`USE_TZ=True`, fuso `America/Sao_Paulo`).
- **Nomes em português** nos modelos, campos, URLs e templates. Textos da interface em português do Brasil.
- **Views** baseadas em classe, com `LoginRequiredMixin` em toda tela nova. Mensagens ao usuário pelo framework de mensagens (classes do Bootstrap mapeadas em `MESSAGE_TAGS`).
- **Formulários** aplicam classes do Bootstrap nos widgets; nomes de cadastro em maiúsculas no `clean_nome()`.
- **Relatório novo:** siga o roteiro em [relatorios.md](relatorios.md#como-acrescentar-um-relatório).
- **Migração nova:** gere com `makemigrations`, revise o arquivo e rode `migrate` localmente antes do push. O deploy aplica `migrate` sozinho em produção.

## Antes de publicar

1. Suíte de testes rodada, sem falhas novas além das listadas acima.
2. `makemigrations --check --dry-run` sem pendências.
3. Documentação atualizada no mesmo commit (veja [Como manter](README.md#como-manter)).
4. Lembre que o push na `main` publica em produção na hora ([operacao.md](operacao.md)).
