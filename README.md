# Sistema de Romaneio de Madeiras

Sistema web em **Django + PostgreSQL** para gestão de vendas de madeira e controle de clientes, saldos, recebimentos e relatórios. O objetivo é substituir planilhas por uma solução **centralizada, rastreável e segura**.

---

## Visão geral

**Principais recursos:**
- Cadastro e gestão de **Clientes**, **Motoristas**, **Tipos de Madeira** e **Operadores**
- Registro de **Romaneios (vendas)** com cálculo automático de totais
- Registro de **Pagamentos/Adiantamentos** vinculados ao cliente
- **Saldo automático por cliente** (dívida, zerado ou crédito)
- **Dashboard** com indicadores do mês
- **Relatórios** com filtros (mês/ano/cliente)
- Autenticação com **login/logout** e **recuperação de senha por e-mail**

---

## Regras de negócio (resumo)

- **Venda (romaneio)** aumenta o valor devido pelo cliente  
- **Pagamento** reduz o valor devido  
- **Saldo do cliente**:
  - **Negativo** → cliente está devendo
  - **Zero** → quitado
  - **Positivo** → crédito

> O saldo é **calculado automaticamente** com base no histórico (vendas e pagamentos).  
> Não existe ajuste manual de saldo para garantir rastreabilidade.

---

## Módulos do sistema

### 1) Dashboard
Resumo mensal com indicadores como:
- Total vendido (m³)
- Faturamento total
- Saldo a receber
- Quantidade de romaneios no mês

### 2) Cadastros
CRUD de:
- Clientes
- Tipos de Madeira
- Motoristas
- Operadores (usuários do sistema)

### 3) Romaneios (Vendas)
Cadastro de romaneios com:
- Data e número
- Cliente, tipo de madeira, motorista
- Quantidade (m³)
- Tipo de venda (normal / com frete)
- Preço unitário sugerido (quando aplicável)
- Total calculado automaticamente

### 4) Pagamentos (Adiantamentos)
Registro de recebimentos por cliente com:
- Data, cliente, valor e descrição
- Impacto automático no saldo do cliente

### 5) Relatórios
- Ficha de Romaneios
- Por Tipo de Madeira
- Fluxo Financeiro
- Saldo de Clientes

---

## Stack

- **Python:** 3.10+ (recomendado 3.11+)
- **Django:** 4.2+
- **PostgreSQL**
- Templates com **Bootstrap 5**
- Views com **Class-Based Views (CBVs)**

---

## Estrutura do projeto

- `apps/cadastros` — clientes, motoristas, tipos, operadores
- `apps/romaneio` — vendas/romaneios
- `apps/financeiro` — pagamentos
- `apps/relatorios` — dashboard e relatórios
- `apps/core` — utilitários e autenticação custom (ex.: password reset)
- `templates/` — templates globais (base e auth)
- `static/` — CSS e assets

---

## Pré-requisitos

- Python 3.10+
- PostgreSQL
- (Opcional) Docker
- (Produção) Servidor SMTP (ex.: Gmail com senha de app) e Nginx com HTTPS

---

## Instalação (desenvolvimento)

```sh
git clone https://github.com/seu-usuario/seu-repo-romaneio.git
cd seu-repo-romaneio

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Crie e configure o .env
# (veja o exemplo abaixo)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse:
- http://127.0.0.1:8000/

---

## Configuração do .env (exemplo)

Crie um arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=sua-chave-super-segura
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=madereira_jd
DB_USER=parica
DB_PASSWORD=senha
DB_HOST=localhost
DB_PORT=5433

# Email (desenvolvimento: console backend; produção: SMTP)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL="Romaneio de Madeiras <no-reply@localhost>"

# Links de recuperação de senha
SITE_DOMAIN=127.0.0.1:8000
SITE_PROTOCOL=http
```

> Em produção, use `DEBUG=False`, configure `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` e SMTP real.

---

## Recuperação de senha por e-mail

O sistema utiliza o fluxo padrão do Django com templates customizados em:
- `templates/registration/password_reset_form.html`
- `templates/registration/password_reset_done.html`
- `templates/registration/password_reset_confirm.html`
- `templates/registration/password_reset_complete.html`
- `templates/registration/password_reset_email.html`
- `templates/registration/password_reset_subject.txt`

Requisito: o usuário precisa ter **e-mail cadastrado** no perfil.

---

## Deploy (produção) - checklist rápido

1. Ajustar `.env`:
   - `DEBUG=False`
   - `ALLOWED_HOSTS=madereirajd.ferzion.com.br,...`
   - `CSRF_TRUSTED_ORIGINS=https://madereirajd.ferzion.com.br,...`
   - `SITE_DOMAIN=madereirajd.ferzion.com.br`
   - `SITE_PROTOCOL=https`
   - SMTP configurado (Gmail: **senha de app**)

2. Coletar estáticos:
```sh
python manage.py collectstatic --noinput
```

3. Rodar check de segurança:
```sh
python manage.py check --deploy
```

4. Nginx com HTTPS e headers:
- `X-Forwarded-Proto`
- `X-Real-IP`
- `X-Forwarded-For`

---

## Contribuição (padrões)

- Use ORM e siga a separação por apps
- Evite “saldo manual”: saldo sempre derivado de vendas e pagamentos
- Relatórios novos: siga o padrão em `apps/relatorios/`
- Para rodar testes:
```sh
python manage.py test
```

---

## Licença

Projeto livre para uso acadêmico e comercial. Veja o arquivo `LICENSE` para detalhes.