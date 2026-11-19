# Roteiro

Onde o projeto está e o que falta. Revisado em 2026-11-19.

**Legenda:** `[x]` feito e verificado · `[~]` em andamento ou parcial · `[ ]` a fazer

## Feito

- [x] Cadastros de clientes, tipos de madeira e motoristas; romaneios, pagamentos, saldo do cliente, dashboard, relatórios, login e deploy automático (2026-01-31)
- [x] Cadastro de operadores com acesso restrito a staff (2026-01-31; restrição em 2026-02-10)
- [x] Romaneio detalhado, unificado ao romaneio simples pelo campo `modalidade` (2026-02-03 a 2026-02-05)
- [x] Recuperação de senha por e-mail (2026-02-05)
- [x] Medidas por tora (unidades) no romaneio detalhado (2026-02-06)
- [x] Exportações em Excel e PDF dos relatórios e PDF/Excel de cada romaneio (2026-02-08 a 2026-02-09)
- [x] Valor bruto e líquido no romaneio (2026-02-09)
- [x] Login por usuário ou e-mail (2026-02-12)
- [x] Romaneiadores: cadastro, campo no romaneio e filtro na Ficha de Romaneios (2026-06-12 a 2026-06-13)
- [x] Filtros de período coerentes em todas as telas, com opção "Todos" e saldo anterior no fluxo financeiro (2026-06-08 a 2026-07-12)
- [x] Exportação em Excel e PDF do relatório de saldo de clientes (2026-07-12)

O detalhe de cada entrega está no [registro de mudanças](CHANGELOG.md).

## Em andamento

Nenhum item em andamento em 2026-11-19.

## Próximo

Ordem sugerida, pelo risco para os dados e para a segurança:

- [ ] Corrigir a perda de alterações nas unidades ao editar romaneio detalhado (DT-01)
- [ ] Criar rotina de backup automático do banco, guardado fora da VPS (DT-02)
- [ ] Fechar as brechas de acesso: `/core/` público, staff editando superusuário, senha inicial fixa (DT-03, DT-04, DT-05)
- [ ] Atualizar o Django para 5.2 LTS (DT-08)
- [ ] Decidir o destino do desconto percentual do romaneio (P-01, DT-06)
- [ ] Deixar a suíte de testes verde e rodá-la no workflow antes do deploy (DT-10, DT-11, DT-14)

## Ideias sem compromisso

- Comissão por romaneiador. O modelo `Romaneiador` foi criado como "base para comissão" (`apps/cadastros/models.py`), mas não há cálculo de comissão.
- Exibir no dashboard as vendas do mês por tipo de madeira (a view já calcula `vendas_por_madeira`) e gráficos.
- Exclusão ou desativação de operadores pela interface.
- Tela de troca de senha para o próprio operador.

## Débitos técnicos

Defeitos e riscos encontrados no código. Ao resolver, marque `[x]` com a data e mantenha o item: outros documentos citam estes números.

| ID | Problema | Onde | Gravidade |
|---|---|---|---|
| DT-01 | Ao editar um romaneio **detalhado** com duas ou mais madeiras, a alteração nas unidades de uma madeira se perde em silêncio quando alguma madeira anterior na lista não mudou. A tela mostra "atualizado com sucesso". A view associa as unidades pela posição na lista de itens **alterados** (`formset.save()`), não pela posição no formulário. Reproduzido em 2026-11-19 | `_save_unidades_for_itens` em `apps/romaneio/views.py` | Alta: afeta valores cobrados |
| DT-02 | Não existe backup automático do PostgreSQL de produção | Servidor | Alta |
| DT-03 | `/core/` abre sem login e mostra faturamento do mês e total a receber. Um teste (`test_core_dashboard_currently_public`) confirma o comportamento | `apps/core/views.py`, `apps/core/urls.py` | Alta: segurança |
| DT-04 | Um staff consegue editar um superusuário pela URL `/cadastros/usuarios/<id>/editar/` (nome, e-mail, ativo). Trocando o e-mail e usando "Esqueci minha senha", toma a conta. Todo operador criado pela tela é staff. Reproduzido em 2026-11-19 | `UsuarioUpdateView` em `apps/cadastros/views.py` | Alta: segurança |
| DT-05 | Operador criado pela tela recebe a senha `123456` e sempre `is_staff=True`, e não há tela de troca de senha | `UsuarioCreateView` em `apps/cadastros/views.py` | Alta: segurança |
| DT-06 | O desconto percentual do romaneio entra no cálculo e aparece nas telas, mas o formulário não tem o campo desde 2026-02-06: romaneios novos ficam com 0%. Depende de P-01 | `RomaneioForm` em `apps/romaneio/forms.py` | A confirmar |
| DT-07 | Excluir um tipo de madeira usado em romaneio dá erro 500 (`ProtectedError` sem tratamento). Reproduzido em 2026-11-19 | `TipoMadeiraDeleteView` em `apps/cadastros/views.py` | Média |
| DT-08 | Django 4.2 LTS sem correções de segurança desde abril de 2026. A atualização para 5.2 LTS também exige revisar `USE_L10N` (removido no Django 5) | `requirements.txt`, `config/settings.py` | Média |
| DT-09 | As mensagens de sucesso na exclusão de romaneio, pagamento, tipo de madeira, motorista e romaneiador não aparecem: as views sobrescrevem `delete()`, que o `DeleteView` do Django 4 não chama mais. A exclusão funciona. Reproduzido em 2026-11-19 | `apps/*/views.py` | Baixa |
| DT-10 | Testes que falham por estarem desatualizados em relação ao código (detalhes em [desenvolvimento.md](docs/desenvolvimento.md#estado-da-suíte)) | `apps/cadastros/tests/`, `apps/financeiro/tests/`, `apps/tests/` | Média |
| DT-11 | `RequirementsImportTests` é declarada duas vezes, e 3 testes nunca rodam | `apps/tests/test_requirements.py` | Baixa |
| DT-12 | O PDF de um romaneio recalcula e grava os totais numa requisição GET | `romaneio_export_pdf` em `apps/relatorios/views_ficha_romaneio.py` | Baixa |
| DT-13 | No detalhado, a regra "cada madeira tem pelo menos uma unidade" só é validada na criação; na edição, remover todas as unidades salva o item com 0 m³ e o romaneio com R$ 0,00. Reproduzido em 2026-11-19 | `RomaneioUpdateView` em `apps/romaneio/views.py` | Média |
| DT-14 | O workflow publica sem rodar testes, desliga a verificação da chave do servidor (`StrictHostKeyChecking=no`) e usa `--break-system-packages` dentro do venv. O Gunicorn, usado em produção, não está em `requirements.txt` | `.github/workflows/deploy.yml` | Média |
| DT-15 | `mock_dados` cria romaneios sem itens com totais aleatórios e 60 usuários staff; nada impede rodá-lo em produção | `apps/cadastros/management/commands/mock_dados.py` | Média |
| DT-16 | Código sem uso: dashboard do `core`, `BaseModel`, `ConfiguracaoGeral`, `Cliente.atualizar_saldo()`, `apps/tests/test_data.py` vazio, `reportlab` em `requirements.txt` (citado como alternativa de PDF, mas nunca importado), `vendas_por_madeira` calculado e não exibido, exportação CSV sem botão | Vários | Baixa |
| DT-17 | `/admin/` ativo sem nenhum modelo registrado; `.vscode/settings.json` configura pytest, que o projeto não usa | `config/urls.py`, `.vscode/settings.json` | Baixa |
| DT-18 | O saldo é calculado em Python, com duas consultas por cliente, no dashboard (duas vezes por cliente) e no relatório de saldo. Aceitável no volume atual; cresce com o número de clientes | `apps/relatorios/views.py`, `views_saldo_cliente.py` | Baixa |
| DT-19 | Se dois usuários têm o mesmo e-mail, o login por esse e-mail dá erro 500 (`MultipleObjectsReturned`). Reproduzido em 2026-11-19 | `apps/core/auth_backends.py` | Baixa |
| DT-20 | O logo da tela de login (`/media/image.png`) só é servido pelo Django com `DEBUG=True`; em produção depende do Nginx | `templates/registration/login.html` | A confirmar (P-02) |

## Pendências que dependem de decisão

| ID | Pergunta | De quem | Desde |
|---|---|---|---|
| P-01 | O desconto percentual do romaneio deve voltar ao formulário ou foi aposentado? | Autor / cliente | 2026-11-19 |
| P-02 | Como o Nginx de produção serve `/static/` e `/media/`, e onde ficam os logs? | Autor | 2026-11-19 |
| P-03 | A lista de pagamentos deve abrir no mês atual, como a de romaneios, ou com todo o histórico, como hoje? | Autor / cliente | 2026-11-19 |
| P-04 | Os operadores informam o comprimento da tora em metros (como diz a tela) ou em centímetros? Com a fórmula atual, só centímetros dão volumes realistas ([regras de negócio](docs/regras-de-negocio.md#volume-de-uma-unidade-modalidade-detalhada)) | Cliente | 2026-11-19 |
| P-05 | Qual é a licença do código? Hoje não há arquivo `LICENSE` | Autor | 2026-11-19 |
