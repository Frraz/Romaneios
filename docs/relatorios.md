# Relatórios e exportações

O que cada tela de relatório mostra, quais filtros aceita e o que cada exportação gera. As fórmulas de saldo e totais estão em [regras-de-negocio.md](regras-de-negocio.md). Todas as telas exigem login.

## Visão geral

| Tela | Rota | Linha da tabela | Exportações |
|---|---|---|---|
| Dashboard | `/` | — | — |
| Ficha de Romaneios | `/ficha-romaneios/` | Um romaneio | Excel, PDF, CSV (sem botão na tela) e Excel/PDF de cada romaneio |
| Ficha de Madeiras | `/ficha-madeiras/` | Um item (madeira de um romaneio) | Excel, PDF |
| Fluxo Financeiro | `/fluxo-financeiro/` | Uma venda ou um pagamento | Excel, PDF |
| Saldo de Clientes | `/saldo-clientes/` | Um cliente | Excel, PDF |

Toda exportação usa os mesmos filtros e a mesma ordenação da tela: o botão repassa a querystring atual.

## Filtro de período

Todas as telas, menos o dashboard e o saldo de clientes, leem `mes` e `ano` por `parse_mes_ano()` (`apps/relatorios/utils.py`):

| Valor na URL | Resultado |
|---|---|
| Parâmetro ausente (primeira visita) | Mês ou ano atual |
| Vazio (`mes=`), opção "Todos" | Sem restrição naquele campo |
| Inválido ou fora da faixa (mês 1–12, ano 1900–2500) | Mês ou ano atual |

Mês e ano são independentes: `mes=&ano=2026` é o ano inteiro; `mes=7&ano=` é julho de todos os anos. O título dos PDFs e o nome dos arquivos seguem o período (`07/2026`, `Todos os meses / 2026`, `todos`).

O filtro de cliente aceita tanto `cliente` quanto `cliente_id` na URL, para que links antigos continuem funcionando.

## Dashboard

Sempre de um único mês: não tem a opção "Todos" (padrão: mês atual).

- Indicadores do mês: m³ vendidos, faturamento (soma do valor líquido), quantidade de romaneios.
- Saldo a receber: soma dos saldos negativos de **todos** os clientes, independente do mês.
- Cinco maiores devedores (saldo atual, independente do mês).
- Cinco clientes que mais compraram no mês.

A view também calcula as vendas por tipo de madeira no mês, mas o template não exibe esse bloco.

## Ficha de Romaneios

Filtros: período, cliente, romaneiador, nº do romaneio (exato) e tipo de madeira (romaneios com pelo menos um item daquela madeira).

Colunas: cliente, nº, data, tipo, m³, total e ações (PDF e Excel do romaneio). Os totais do período (m³, bruto e líquido) consideram todos os filtros. Paginação de 50.

Ordenação por cliente, nº, data, m³ ou total (`sort` e `dir`). O nº é ordenado como número quando só tem dígitos; números com ponto ou letras (`3107.1`) vão para o fim da ordem crescente. A expressão SQL muda conforme o banco: regex no PostgreSQL, `GLOB` no SQLite dos testes.

Exportações:

| Rota | Formato | Conteúdo |
|---|---|---|
| `/ficha-romaneios/export/excel/` | `.xlsx` | Um romaneio por linha, com filtros e ordenação da tela |
| `/ficha-romaneios/export/pdf/` | PDF | Idem |
| `/ficha-romaneios/export/` | CSV (`;`) | Um **item** por linha, com totais. Ignora o romaneio e a ordenação. Não há botão na tela |
| `/romaneios/<id>/export/pdf/` | PDF | O romaneio completo, com itens e unidades, para impressão |
| `/romaneios/<id>/export/excel/` | `.xlsx` | Idem |

O PDF individual recalcula e grava os totais do romaneio antes de gerar o arquivo (DT-12).

## Ficha de Madeiras

Uma linha por item. Filtros: período, cliente, nº do romaneio, tipo de romaneio (`NORMAL`/`COM_FRETE`) e tipo de madeira. Ordenação por data, nº, madeira, tipo, valor unitário, m³ ou total. Totais de m³ e valor dos itens filtrados. Sem paginação.

## Fluxo Financeiro

Uma tabela única com vendas (romaneios) e pagamentos do período, em ordem cronológica crescente.

Colunas: data, nº do romaneio, cliente, m³, total (venda), crédito (pagamento) e saldo atual do cliente depois daquela linha.

Filtros: período, cliente, nº do romaneio e tipo de madeira. Com nº ou madeira preenchidos, os pagamentos se limitam aos clientes das vendas encontradas.

Indicadores: vendas, recebimentos e saldo do período (recebido − vendido).

**Saldo anterior.** Quando o período tem um início definido (há ano selecionado), o saldo de cada linha parte do saldo do cliente **antes** do período, e não de zero. Com um cliente selecionado, a tela mostra também o saldo anterior e o saldo final (anterior + recebido − vendido). Com "Todos os períodos", o saldo da última linha de cada cliente bate com o saldo atual dele.

**Saldo parcial.** Com filtro de nº ou de madeira, a lista não traz todas as movimentações. Nesse caso o saldo por linha volta a partir de zero, e a tela avisa que é parcial. O saldo anterior ignora esses filtros: saldo é sempre do cliente inteiro.

## Saldo de Clientes

Um cliente por linha: nome, telefone, CPF/CNPJ, saldo e situação. Inclui clientes inativos.

Filtros: tipo de saldo (`todos`, `negativos`, `positivos`, `zerados`) e busca (`q`) por nome, telefone ou CPF/CNPJ. Ordenação fixa: do mais devedor para o maior crédito; empate por nome. Totais: quantidade de clientes, total a receber (soma dos negativos) e total de créditos. Paginação de 100.

Não tem filtro de período: é a foto do saldo atual.

## Geração dos arquivos

- **Excel:** `openpyxl`, montado em memória e baixado como anexo.
- **PDF:** a view renderiza um template HTML (`*_pdf.html`) e o converte com `weasyprint.HTML(...).write_pdf()`. O import é feito dentro da view. Se o WeasyPrint ou as bibliotecas nativas dele faltarem, a resposta é HTTP 500 com a mensagem do erro em texto; o restante do sistema continua funcionando. O PDF abre no navegador (`inline`).
- **Nomes de arquivo:** passam por `safe_filename()` e levam o período, por exemplo `ficha_romaneios_07_2026.pdf` e `romaneio_11613.pdf`.

## Como acrescentar um relatório

1. Crie `apps/relatorios/views_<nome>.py` com uma função que monta o queryset a partir do `request` (filtros e ordenação). Tela e exportações usam a mesma função.
2. Use `parse_mes_ano`, `apply_periodo`, `get_cliente_id`, `periodo_label`, `periodo_slug` e `safe_filename` de `apps/relatorios/utils.py`.
3. Crie a view da tela (`LoginRequiredMixin`) e as funções de exportação (`@login_required`), com o template de tela e o `*_pdf.html`.
4. Reexporte em `apps/relatorios/views.py` e registre a rota em `apps/relatorios/urls.py`.
5. Acrescente o item ao menu em `templates/base.html` (barra do desktop e menu lateral do celular).
6. Escreva os testes em `apps/relatorios/tests/test_relatorios_views.py`, incluindo o caso "Todos".
