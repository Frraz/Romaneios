# Registro de mudanças

Mudanças que quem usa ou mantém o sistema percebe, da mais recente para a mais antiga. A aplicação não tem número de versão: cada entrada leva a data da publicação.

As entradas até 2026-07-12 foram reconstituídas em 2026-11-19 a partir do histórico do Git e das migrações. Cada uma agrupa os commits do dia.

## [Não lançado]

### Adicionado

- Documentação em `docs/` (arquitetura, regras de negócio, relatórios, desenvolvimento, operação, decisões e interface), roteiro (`ROADMAP.md`), este registro e `.env.example`.

### Alterado

- `README.md` reescrito para descrever o sistema como ele funciona hoje.

## 2026-07-12

### Adicionado

- Exportação em Excel e PDF do relatório de Saldo de Clientes.
- Fluxo Financeiro com saldo anterior ao período: o saldo de cada linha parte do saldo do cliente antes do período. Com um cliente selecionado, a tela mostra o saldo anterior e o saldo final.
- Aviso de saldo parcial no Fluxo Financeiro quando há filtro de nº de romaneio ou de madeira.

### Alterado

- Convenção única de período em todos os relatórios: sem filtro, mês atual; mês ou ano em branco, "Todos". As exportações seguem o mesmo filtro da tela.

## 2026-06-13

### Adicionado

- Filtro por romaneiador na Ficha de Romaneios e no PDF dela.

## 2026-06-12

### Adicionado

- Cadastro de romaneiadores e campo "romaneiador" (opcional) no romaneio.

### Ação necessária na atualização

- `python manage.py migrate` (migrações `cadastros/0005` e `romaneio/0010`; o deploy automático já executa).

## 2026-06-08

### Adicionado

- Busca na lista de motoristas por nome, CPF, telefone ou placa.
- Seleção de mês e ano no dashboard.

### Alterado

- Lista de romaneios: mês e ano filtram de forma independente.
- Ajustes visuais na folha de estilos.

## 2026-06-05

### Corrigido

- Ordenação por nº do romaneio não quebra mais quando o número tem ponto ou letras (ex.: `3107.1`).

## 2026-03-24

### Alterado

- Ajustes no Fluxo Financeiro e na lista de tipos de madeira.

## 2026-02-12

### Adicionado

- Login com nome de usuário ou e-mail.
- Logo na tela de login.
- Comando `mock_dados` para gerar dados de exemplo em desenvolvimento.

### Corrigido

- Paginação e filtros de mês e ano nas listas.

## 2026-02-10

### Adicionado

- Exclusão de pagamentos com tela de confirmação.
- A confirmação de exclusão de cliente mostra os romaneios e pagamentos vinculados; com vínculos, a exclusão é bloqueada com mensagem.

### Alterado

- Tela de operadores restrita a usuários staff.
- Ordem de exibição do Fluxo Financeiro.

## 2026-02-09

### Adicionado

- Desconto percentual no romaneio, com valor bruto e valor líquido.
- Exclusão de romaneios, clientes e motoristas com tela de confirmação.
- Exportação em Excel e PDF da Ficha de Romaneios e do Fluxo Financeiro.
- Valores no formato brasileiro (milhar com ponto, decimal com vírgula).

### Corrigido

- PDF dos romaneios simples e da Ficha de Romaneios.
- Salvamento de romaneio simples.
- Totais bruto e líquido nos romaneios simples e detalhados.

### Ação necessária na atualização

- `python manage.py migrate` (migrações `cadastros/0004` e `romaneio/0009`).

## 2026-02-08

### Adicionado

- PDF e Excel de cada romaneio, para impressão.
- Exportação em Excel e PDF da Ficha de Madeiras.

## 2026-02-06

### Alterado

- Romaneio detalhado passa a registrar cada tora (unidade) com comprimento, rôdo e dois descontos; o m³ do item é a soma das toras.

### Removido

- Campo de desconto percentual no formulário de romaneio.

### Ação necessária na atualização

- `python manage.py migrate` (migrações `romaneio/0007` e `romaneio/0008`).

## 2026-02-05

### Adicionado

- Recuperação de senha por e-mail.
- Tela de confirmação para excluir tipo de madeira.

### Alterado

- Romaneio simples e detalhado unificados num único cadastro, com o campo "modalidade". Os romaneios detalhados existentes foram copiados para o modelo único.

### Ação necessária na atualização

- Backup do banco antes de atualizar.
- `python manage.py migrate` (migrações `cadastros/0003` e `romaneio/0004` a `0006`, que incluem migração de dados).

## 2026-02-03

### Adicionado

- Romaneio detalhado, com telas próprias (unificado ao romaneio simples em 2026-02-05).

### Alterado

- CPF/CNPJ do cliente passa a ser opcional.

### Ação necessária na atualização

- `python manage.py migrate` (migrações `cadastros/0002`, `romaneio/0002` e `romaneio/0003`).

## 2026-01-31

### Adicionado

- Primeira versão: cadastros de clientes, tipos de madeira e motoristas; romaneios com itens; pagamentos; saldo do cliente; dashboard; Ficha de Romaneios, Ficha de Madeiras, Fluxo Financeiro e Saldo de Clientes; login; cadastro de operadores; deploy automático na VPS.
