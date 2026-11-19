# Decisões

Escolhas que alguém perguntaria "por que foi feito assim?". As datas vêm do histórico do Git; decisões anteriores ao primeiro commit (2026-01-31) levam essa data. Decisão não é apagada: quando muda, a nova entrada aponta a anterior como substituída.

| Data | Decisão | Motivo | Reversível? |
|---|---|---|---|
| 2026-01-31 | Django com templates renderizados no servidor e Class-Based Views, sem front-end separado | Sistema interno de poucos operadores; um único projeto para manter e publicar (a confirmar) | Caro |
| 2026-01-31 | PostgreSQL em produção; SQLite em memória só nos testes | Testes rápidos sem infraestrutura (`config/settings_test.py`); motivo da escolha do PostgreSQL a confirmar | Com migração de dados |
| 2026-01-31 | Saldo do cliente calculado na hora, nunca gravado, e sem ajuste manual | Rastreabilidade: todo valor do saldo vem de um romaneio ou de um pagamento, e não há saldo dessincronizado | Sim, mas contraria a regra de negócio |
| 2026-01-31 | Totais do romaneio (`m3_total`, `valor_bruto`, `valor_total`) gravados, mas sempre derivados pelos `save()`/`delete()` dos modelos | Relatórios e saldo somam direto no banco, sem recalcular itens (efeito do código; motivo a confirmar) | Sim |
| 2026-01-31 | Dinheiro e m³ em `Decimal` com `ROUND_HALF_UP` (2 e 3 casas) | Evita erro de arredondamento de ponto flutuante em valores cobrados | Não recomendado |
| 2026-01-31 | Deploy por GitHub Actions a cada push na `main`, por SSH na VPS | Publicação sem passos manuais num único servidor | Sim |
| 2026-01-31 | Dois preços por madeira (normal e com frete), escolhidos pelo tipo do romaneio | O preço com frete é uma tabela própria, não um acréscimo sobre o normal (a confirmar) | Com migração |
| 2026-01-31 | Preço gravado no item no momento da venda | Mudar a tabela de preços não altera vendas já registradas (efeito do código; motivo a confirmar) | Não recomendado |
| 2026-02-05 | Romaneio simples e detalhado unificados num modelo só, com o campo `modalidade` (substitui o `RomaneioDetalhado` de 2026-02-03) | Duas tabelas duplicavam telas, relatórios e o cálculo do saldo (a confirmar) | Não: houve migração de dados (`romaneio/0005`) |
| 2026-02-05 | Links de redefinição de senha montados com `SITE_DOMAIN` e `SITE_PROTOCOL`, não com o host da requisição | Atrás do proxy, o host da requisição pode ser o interno | Sim |
| 2026-02-06 | Medidas por tora (`UnidadeRomaneio`) em vez de medidas no item | O romaneio detalhado mede cada tora; o item passa a ser a soma das toras | Não: migração `romaneio/0007` |
| 2026-02-06 | m³ da unidade calculado pela fórmula, mas editável, e o servidor só calcula quando chega vazio | Permite ao operador ajustar o m³ calculado (motivo a confirmar) | Sim |
| 2026-02-08 | PDF com WeasyPrint a partir de templates HTML, importado dentro das views | Reaproveita HTML e CSS na impressão; se a biblioteca nativa faltar, só a exportação falha | Sim |
| 2026-02-09 | Desconto percentual no romaneio, sobre o valor bruto, guardando bruto e líquido | Exibir o valor antes e depois do desconto. O formulário não tem o campo desde 2026-02-06 (P-01) | Sim |
| 2026-02-10 | Acesso sem permissão de staff redireciona ao dashboard com mensagem, em vez de erro 403 | Mensagem amigável para o operador | Sim |
| 2026-02-12 | Login por nome de usuário ou e-mail no mesmo campo | A confirmar | Sim |
| 2026-06-05 | Ordenar o nº do romaneio como número só quando ele tem apenas dígitos; os demais vão para o fim | Números como `3107.1` quebravam a conversão para inteiro no PostgreSQL | Sim |
| 2026-07-12 | Convenção única de período nos relatórios: parâmetro ausente é o mês atual; vazio é "Todos" | Antes, "Todos" num dos campos anulava o filtro inteiro, e cada tela tratava de um jeito | Sim |
| 2026-07-12 | Fluxo financeiro com saldo anterior ao período, e saldo corrido zerado quando a lista é parcial (filtro de nº ou de madeira) | O saldo de cada linha tem que bater com o saldo real do cliente; numa lista incompleta, um saldo corrido enganaria | Sim |
