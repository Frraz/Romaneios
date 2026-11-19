# Regras de negócio

Termos, fórmulas e validações que o sistema aplica hoje. Como as telas de relatório usam essas regras está em [relatorios.md](relatorios.md); onde cada regra mora no código está em [arquitetura.md](arquitetura.md).

## Vocabulário

| Termo | Significado no sistema |
|---|---|
| **Romaneio** | Documento de uma venda de madeira a um cliente, identificado por um número único (`numero_romaneio`, texto livre, ex.: `11613` ou `3107.1`). Modelo `Romaneio`. |
| **Item** | Uma espécie de madeira dentro do romaneio, com quantidade em m³ e valor por m³. Cada tipo de madeira aparece uma vez por romaneio. Modelo `ItemRomaneio`. |
| **Unidade** (tora) | Uma peça medida individualmente num romaneio detalhado: comprimento, rôdo e dois descontos. Modelo `UnidadeRomaneio`. |
| **Rôdo** | Medida da circunferência da tora, informada em centímetros. |
| **Modalidade** | `SIMPLES`: o operador informa o m³ total de cada item. `DETALHADO`: o m³ do item é a soma das unidades. |
| **Tipo de romaneio** | `NORMAL` ou `COM_FRETE`. Define qual dos dois preços do tipo de madeira é usado. |
| **Tipo de madeira** | Espécie vendida, com dois preços por m³: `preco_normal` e `preco_com_frete`. |
| **Motorista** | Quem transporta a carga. Opcional no romaneio. |
| **Romaneiador** | Pessoa responsável por medir e emitir o romaneio. Opcional no romaneio. |
| **Pagamento** (adiantamento) | Valor recebido de um cliente, em uma data, por um meio (dinheiro, PIX, transferência, cheque, depósito, outros). Modelo `Pagamento`. |
| **Valor bruto** | Soma dos itens do romaneio, antes do desconto percentual. |
| **Valor líquido** (`valor_total`) | Valor bruto após o desconto percentual do romaneio. É o valor que entra no saldo do cliente. |
| **Saldo do cliente** | Pagamentos menos vendas. Negativo: o cliente deve. Zero: quitado. Positivo: crédito. |
| **Operador** | Usuário do sistema (`django.contrib.auth.User`). |

## Romaneio e seus totais

### Preço do item

Ao escolher a madeira, o formulário preenche o valor por m³ com o preço do tipo de romaneio (`TipoMadeira.get_preco()`). O campo é somente leitura na tela. Trocar o tipo de romaneio atualiza o preço de todos os itens.

Se um item chegar ao banco com valor unitário vazio ou zero, `ItemRomaneio.save()` aplica o mesmo preço automaticamente.

O preço fica gravado no item: mudar o preço do tipo de madeira depois não altera romaneios já salvos.

### Volume de uma unidade (modalidade detalhada)

```
m³ = ( (rôdo ÷ 4)² × comprimento  −  desconto_1 × desconto_2 × comprimento ) ÷ 1.000.000
```

Arredondado para 3 casas, meio para cima. A mesma fórmula está em `UnidadeRomaneio.calcular_m3_detalhado()` (`apps/romaneio/models.py`) e no JavaScript `calcularM3Unidade()` de `apps/romaneio/templates/romaneio/romaneio_form.html`. As duas precisam mudar juntas.

- O formulário calcula o m³ enquanto o operador digita, mas o campo continua editável: o valor digitado é o que vale.
- No servidor, a fórmula só é aplicada quando o m³ da unidade chega vazio ou zero.
- A tela rotula o comprimento em metros. Com a divisão por 1.000.000, porém, só resultam volumes realistas com o comprimento em centímetros: 300 cm e rôdo de 150 cm dão 0,422 m³, enquanto 3 m dão 0,004 m³. Como os operadores preenchem esse campo está em aberto: pendência P-04 do [roteiro](../ROADMAP.md).

### Totais do item

| Modalidade | m³ do item | Valor do item |
|---|---|---|
| `SIMPLES` | Informado pelo operador | m³ × valor unitário |
| `DETALHADO` | Soma do m³ das unidades | m³ × valor unitário |

Valores em reais com 2 casas e m³ com 3 casas, sempre com arredondamento meio para cima (`ROUND_HALF_UP`).

### Totais do romaneio

```
valor_bruto = Σ valor dos itens
valor_total = valor_bruto × (100 − desconto%) ÷ 100
m3_total    = Σ m³ dos itens
```

- Os três campos são derivados e nunca editados à mão. São recalculados sempre que um item ou unidade é salvo ou excluído pelo ORM.
- O desconto percentual vai de 0 a 100. **O formulário atual não tem campo para o desconto**: todo romaneio criado pela tela fica com 0%. Romaneios que já tinham desconto continuam com ele, e a listagem e o detalhe o exibem. Débito DT-06 do [roteiro](../ROADMAP.md).

### Validações do romaneio

- Número do romaneio único no sistema.
- Pelo menos um item. A mesma madeira não pode aparecer duas vezes no mesmo romaneio.
- Valor unitário maior que zero. m³ do item não negativo.
- No detalhado: cada unidade precisa de comprimento e rôdo maiores que zero e de m³ maior que zero. Na **criação**, cada item precisa ter ao menos uma unidade. Na edição, essa regra não é verificada (DT-13).
- Cliente, motorista, romaneiador e madeira só aparecem para seleção se estiverem ativos.

## Saldo do cliente

```
saldo = Σ pagamentos do cliente − Σ valor_total dos romaneios do cliente
```

- Calculado na hora (`Cliente.saldo_atual`), nunca gravado no banco.
- Não existe ajuste manual de saldo. Para corrigir um saldo, corrige-se o romaneio ou o pagamento que o originou. Isso mantém cada centavo rastreável a um documento.
- Usa o valor líquido do romaneio, com o desconto aplicado.

## Pagamentos

- Valor maior que zero.
- A data não pode ser futura (`timezone.localdate()`, fuso `America/Sao_Paulo`). A validação está no próprio modelo (`Pagamento.save()` chama `full_clean()`), então vale também fora das telas.
- Só clientes ativos aparecem no formulário.
- O usuário que registrou o pagamento é gravado em `usuario_cadastro`.

## Cadastros

- Nomes de cliente, tipo de madeira, motorista e romaneiador são únicos e gravados em maiúsculas.
- CPF/CNPJ do cliente é opcional. Quando preenchido, é validado pelos dígitos verificadores, conforme o tipo de pessoa escolhido (física: CPF; jurídica: CNPJ).
- Cadastro inativo some das listas de seleção, mas continua nos relatórios e no histórico.
- Excluir um cliente com romaneios ou pagamentos é bloqueado, com mensagem dizendo quantos vínculos existem.
- Excluir motorista ou romaneiador deixa o campo vazio nos romaneios em que aparecia.
- Excluir um tipo de madeira usado em algum romaneio é bloqueado pelo banco. Hoje isso aparece como erro 500 em vez de mensagem (DT-07).
- Excluir um romaneio exclui junto os itens e as unidades dele.

## Operadores e permissões

| Ação | Quem pode |
|---|---|
| Usar cadastros, romaneios, pagamentos e relatórios | Qualquer usuário autenticado |
| Listar, criar e editar operadores | Usuário `is_staff` |
| Ver superusuários na lista de operadores | Só superusuário |
| Marcar alguém como superusuário | Só superusuário (o formulário do staff não tem o campo) |
| Excluir operador | Ninguém pela interface (não há tela) |

- Sem permissão, o operador volta ao dashboard com a mensagem "Você não tem permissão para acessar esta área."
- A lista esconde os superusuários de quem não é superusuário, mas a tela de edição não: um staff que abre `/cadastros/usuarios/<id>/editar/` com o id de um superusuário consegue alterar o nome de usuário, o e-mail e o status ativo dele. Débito DT-04.
- Operador criado pela tela recebe a senha inicial `123456` e sempre fica `is_staff`. Não há tela de troca de senha: a troca é feita por "Esqueci minha senha", que exige e-mail cadastrado. Débito DT-05.
- O login aceita usuário ou e-mail, sem diferenciar maiúsculas e minúsculas. Se dois usuários tiverem o mesmo e-mail, o login por esse e-mail dá erro 500 (DT-19).

## Períodos nas listas e relatórios

Duas convenções coexistem:

| Tela | Sem filtro na URL (primeira visita) | Mês ou ano em branco |
|---|---|---|
| Dashboard | Mês atual | Mês atual (não há "Todos") |
| Relatórios (fichas, fluxo) | Mês atual | "Todos": sem restrição naquele campo |
| Lista de romaneios | Mês atual | Sem restrição naquele campo |
| Lista de pagamentos | **Todo o histórico** | Sem restrição naquele campo |

Mês e ano filtram de forma independente: escolher só o ano mostra o ano inteiro; escolher só o mês mostra aquele mês em todos os anos. A lista de pagamentos abrir com todo o histórico, ao contrário das demais, é o comportamento atual; um teste espera o mês atual (pendência P-03).
