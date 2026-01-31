# Sistema de Romaneio de Madeiras

Sistema web em **Django + PostgreSQL** para gestão de vendas de madeiras e controle fácil de clientes, saldos, recebimentos e relatórios, substituindo planilhas Excel por uma solução eficiente, automatizada e segura.

---

## 📌 Sobre o sistema

- Controle de vendas de madeira em metros cúbicos (m³)
- Gestão de clientes, motoristas, tipos de madeira e operadores
- Geração automática de **romaneios** e **adiantamentos** (pagamentos)
- Cálculo automático do saldo de cada cliente (dívida ou crédito)
- Painel com os principais indicadores do mês
- Relatórios mensais detalhados com filtros

---

## 📂 Estrutura funcional

### 1️⃣ **Dashboard**
- Tela inicial com resumo mensal:
  - Total vendido (m³)
  - Faturamento total
  - Saldo a receber
  - Qtd. de romaneios/vendas no mês

### 2️⃣ **Cadastros**
CRUD para:
- Clientes
- Tipos de Madeira
- Motoristas
- Operadores (usuários do sistema)

### 3️⃣ **Romaneio (Vendas)**
- Registro detalhado de vendas, com:
  - Data e Nº do Romaneio
  - Cliente, Tipo de Madeira, Motorista
  - Quantidade em m³
  - Tipo de venda (Normal / Com frete)
  - Preço unitário sugerido automaticamente
  - Total calculado
- **Regra:** Salva venda → saldo do cliente diminui (fica negativo/mais negativo)

### 4️⃣ **Adiantamentos (Gestão de Pagamentos)**
- Registro de pagamentos por cliente, com:
  - Data, Cliente, Valor, Descrição
- **Regra:** Pagamento recebido abate do saldo devedor. Saldo pode zerar ou ficar positivo (crédito para compras futuras).

### 5️⃣ **Relatórios mensais**
- **Ficha de Romaneios:** vendas no período
- **Ficha por Tipo de Madeira:** total por espécie/tipo
- **Fluxo Financeiro:** extrato de entradas (pagamentos) e saídas (romaneios)
- **Saldo de Clientes:** situação de cada cliente (devedor/credor)
- Todos com filtros por mês, ano e cliente.

---

## 📊 Lógica e Regras de Negócio

- **Saldo do Cliente**:  
  - Toda venda = saldo negativo (deve)
  - Todo pagamento = reduz saldo negativo
  - Cliente pode ter saldo:  
    - Negativo (devendo)  
    - Zerado  
    - Positivo (crédito)
- Saldo **sempre calculado automaticamente**, nunca ajustado manualmente.
- Relatórios garantem rastreabilidade total dos negócios.

---

## 🛠️ Stack e Boas Práticas

- **Backend:** Python 3.10+, Django 4.x
- **Banco:** PostgreSQL
- **Arquitetura por apps:**
  - `cadastros`, `romaneio`, `financeiro`, `relatorios`
- ORM e migrations Django
- Views baseadas em classes (CBV)
- Templates responsivos (Bootstrap 5)
- Uso opcional do **Django Admin**
- Código limpo, com docstrings e validado por PEP8

---

## 📦 Recursos da entrega

- Modelos Django completos (`Cliente`, `TipoMadeira`, `Motorista`, `Romaneio`, `ItemRomaneio`, `Pagamento`)
- Relacionamentos corretos (chaves estrangeiras, ligando vendas e pagamentos ao cliente)
- Lógica de saldo e validação nas views e models
- Estrutura organizada para fácil expansão futura
- Exemplos de código disponíveis nos diretórios dos apps
- Instalação simples e documentação para uso e manutenção do sistema

---

## 🚀 Instalação rápida

```sh
git clone https://github.com/seu-usuario/seu-repo-romaneio.git
cd seu-repo-romaneio
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Configure DATABASES no settings.py para seu Postgres
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Acesse: http://localhost:8000

---

## 🧑‍💻 Para Desenvolvedores

- Siga a separação de apps e use sempre o ORM.
- **Nunca atualize o saldo manualmente:** ele é derivado do histórico de vendas e pagamentos.
- Novos relatórios? Siga o padrão dos existentes em `apps/relatorios/views.py`.
- Testes: use `python manage.py test`.

---

## 📄 Licença

Projeto livre para uso acadêmico e comercial. Veja o arquivo LICENSE para detalhes.
