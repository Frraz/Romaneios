# CLAUDE.md

Instruções para trabalhar neste repositório. O que o sistema é e como funciona está em `docs/`; aqui fica só o que não dá para descobrir lendo o código.

## Antes de tudo

- **O sistema está em produção.** Todo push na `main` publica na hora (`.github/workflows/deploy.yml`: `git pull`, `pip install`, `migrate`, `collectstatic`, restart do `gunicorn_romaneios`), inclusive commit só de documentação. Nunca faça commit nem push sem pedido explícito. Trabalhe fora da `main` quando possível.
- O deploy não roda testes. Rode-os você antes de dizer que algo está pronto.

## Comandos

Ambiente: Python **3.12** (o Django 4.2 não roda no 3.14 do sistema). O `venv/` local fica fora do Git.

```bash
source venv/bin/activate
# se não existir: uv venv --python 3.12 venv && VIRTUAL_ENV=venv uv pip install -r requirements.txt

# Testes: sempre com as settings de teste (SQLite em memória). Sem isso, tenta conectar no PostgreSQL.
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test -v 2
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test apps.romaneio
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test apps.romaneio.tests.test_romaneio_models.RomaneioTotaisTests.test_item_delete_recalcula_totais_romaneio

# Verificações
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py check
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py makemigrations --check --dry-run

# Servidor local (precisa de PostgreSQL; porta padrão do projeto: 5433)
python manage.py runserver
```

Não há linter nem formatador configurados.

## Regras que não podem ser quebradas

- Dinheiro e m³ em `Decimal`, quantizados com `VALOR_STEP`/`QTD_M3_STEP` e `ROUND_HALF_UP` (`apps/romaneio/models.py`). Nada de `float` em totais ou saldo.
- `Romaneio.m3_total`, `valor_bruto`, `valor_total` e `ItemRomaneio.valor_total` são derivados. Nunca os atribua à mão.
- Itens e unidades se salvam e excluem pelo `save()`/`delete()` de cada objeto. `update()`, `bulk_create()` e exclusão em massa pulam a cascata de totais.
- O saldo do cliente nunca é gravado nem ajustado à mão: é `Cliente.saldo_atual` (pagamentos − `valor_total` dos romaneios).
- Não altere nem reverta migrações já aplicadas. A `romaneio/0005` é migração de dados sem volta.
- Nunca rode `mock_dados` contra o banco de produção.
- Dados reais de ambiente (domínio, caminhos, usuário do banco) não entram em arquivo versionado. Use exemplos (`app.exemplo.com.br`, `/srv/romaneios`).

## Armadilhas conhecidas

- A fórmula do m³ da unidade existe em dois lugares: `UnidadeRomaneio.calcular_m3_detalhado()` e `calcularM3Unidade()` em `apps/romaneio/templates/romaneio/romaneio_form.html`. Mude os dois juntos.
- O POST de criar/editar romaneio sempre leva o management form de unidades por item (`unidades-<i>-TOTAL_FORMS`…), mesmo no SIMPLES. Veja os auxiliares em `apps/romaneio/tests/test_romaneio_views.py`.
- Na edição de romaneio, as unidades são casadas com os itens pelo índice do retorno de `formset.save()`, que só traz itens alterados. Isso perde alterações (DT-01 no `ROADMAP.md`). Não copie esse padrão.
- `DeleteView` do Django 4.2 não chama `delete()` no POST: mensagem ou lógica posta ali não roda. Use `form_valid()`.
- `TipoMadeira` e `Cliente` são `PROTECT`. Exclusão de madeira em uso hoje estoura `ProtectedError` (DT-07). `ClienteDeleteView` mostra como tratar.
- `StaffRequiredMixin` redireciona (302) para o dashboard com mensagem, não devolve 403.
- Período nos relatórios: use `parse_mes_ano()` de `apps/relatorios/utils.py`. Parâmetro ausente = mês atual; vazio = "Todos" (`None`). A lista de pagamentos é a exceção: sem filtro mostra tudo.
- Ordenar pelo nº do romaneio exige o `RawSQL` com `CASE` de `views_ficha_romaneio.py` (regex no PostgreSQL, `GLOB` no SQLite). `Cast` direto quebra com números como `3107.1`.
- PDF: `weasyprint` é importado dentro da view. `reportlab` está no `requirements.txt` mas não é usado.
- `apps/core/views.py` tem um dashboard antigo e público em `/core/`; o dashboard real é `apps/relatorios/views.py`. `BaseModel` e `ConfiguracaoGeral` não são usados.
- `apps/relatorios/views.py` só reexporta: edite os módulos `views_*.py`.
- A suíte tem falhas conhecidas (testes desatualizados) e testes ocultos por classe duplicada, listados em `docs/desenvolvimento.md`. Não esconda falhas novas atrás delas.
- Item de menu novo entra duas vezes em `templates/base.html`: barra do desktop e menu offcanvas do celular.

## Definição de pronto

1. Testes novos ou ajustados para a mudança; a suíte roda sem falhas além das conhecidas.
2. `makemigrations --check --dry-run` limpo, ou migração nova revisada.
3. Documentação atualizada no mesmo commit (tabela "Como manter" em `docs/README.md`), incluindo `CHANGELOG.md` em `[Não lançado]` e o `ROADMAP.md` se um `DT`/`P` foi resolvido.
4. Nenhum dado real de ambiente em arquivo versionado.

## O que ler antes de cada tarefa

| Tarefa | Leia |
|---|---|
| Cálculo de totais, saldo, validações, permissões | `docs/regras-de-negocio.md` |
| Relatório, filtro ou exportação | `docs/relatorios.md` |
| Modelo, rota, app nova | `docs/arquitetura.md` |
| Deploy, servidor, variáveis de ambiente | `docs/operacao.md`, `.env.example` |
| Tela, CSS, componentes | `docs/design.md` |
| Corrigir um defeito conhecido | `ROADMAP.md` (débitos `DT-xx`) |
| Entender uma escolha antiga | `docs/decisoes.md` |

Dados reais do ambiente de produção, quando existirem nesta máquina, estão em `docs/ambiente.local.md` (fora do Git).
