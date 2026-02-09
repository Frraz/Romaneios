# Sistema de Romaneio de Madeiras (MadeireiraJD)

Sistema web em **Django** para gestão de vendas (romaneios) de madeira, controle de clientes, saldos, recebimentos e relatórios.  
O objetivo é substituir planilhas por uma solução **centralizada, rastreável e segura**.

---

## Visão geral

### Principais recursos
- Cadastro e gestão de **Clientes**, **Motoristas**, **Tipos de Madeira** e **Usuários (operadores)**
- Registro de **Romaneios (vendas)** com cálculo automático de totais
- Registro de **Pagamentos/Adiantamentos** vinculados ao cliente
- **Saldo automático por cliente** (devedor, zerado ou com crédito)
- **Dashboard** com indicadores do mês
- **Relatórios** com filtros (mês/ano/cliente/tipo de madeira)
- Autenticação com **login/logout** e **recuperação de senha por e-mail**

---

## Regras de negócio (resumo)

- **Venda (romaneio)** aumenta o valor devido pelo cliente
- **Pagamento** reduz o valor devido
- **Saldo do cliente**:
  - **Negativo** → cliente está devendo
  - **Zero** → quitado
  - **Positivo** → cliente com crédito

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
- Tipos de madeira
- Motoristas
- Usuários (operadores)

### 3) Romaneios (Vendas)
Cadastro de romaneios com:
- Data e número
- Cliente e motorista
- Tipo de romaneio (ex.: **normal** / **com frete**)
- Modalidade (**simples** ou **detalhado**, quando aplicável)
- Itens por tipo de madeira, com:
  - quantidade (m³)
  - preço unitário
  - total calculado automaticamente

### 4) Pagamentos (Adiantamentos)
Registro de recebimentos por cliente com:
- Data, cliente, valor, tipo e descrição
- Impacto automático no saldo do cliente

### 5) Relatórios
- Ficha de Romaneios
- Ficha por Tipo de Madeira
- Fluxo Financeiro
- Saldo de Clientes
- Exportação (CSV/XLSX e PDF quando disponível)

---

## Stack

- **Python:** 3.10+ (recomendado 3.11+)
- **Django:** 4.2+
- **Banco:** PostgreSQL (produção)
- Templates com **Bootstrap 5**
- Views com **Class-Based Views (CBVs)**

---

## Estrutura do projeto

- `apps/cadastros/` — clientes, motoristas, tipos, usuários
- `apps/romaneio/` — romaneios (vendas)
- `apps/financeiro/` — pagamentos
- `apps/relatorios/` — dashboard e relatórios (inclui exports)
- `apps/core/` — utilitários e autenticação custom (ex.: password reset)
- `templates/` — templates globais (base e auth)
- `static/` — CSS e assets
- `config/` — settings/urls/wsgi

---

## Pré-requisitos

- Python 3.10+
- PostgreSQL (produção)
- (Opcional) Docker
- (Produção) Servidor SMTP e Nginx (ou proxy) com HTTPS

> **Observação sobre PDF (WeasyPrint):** para exportação em PDF em Linux, podem ser necessárias bibliotecas do sistema (dependendo da distro). Em Windows, é comum precisar rodar via WSL para evitar problemas com dependências nativas.

---

## Instalação (desenvolvimento)

### 1) Clonar e criar ambiente virtual
```sh
git clone https://github.com/<owner>/<repo>.git
cd <repo>

python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1
```

### 2) Instalar dependências
```sh
pip install -r requirements.txt
```

### 3) Configurar variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto (veja o exemplo abaixo).

### 4) Migrar e criar usuário admin
```sh
python manage.py migrate
python manage.py createsuperuser
```

### 5) Executar
```sh
python manage.py runserver
```

Acesse:
- http://127.0.0.1:8000/

---

## Configuração do `.env` (exemplo)

Crie o arquivo `.env` na raiz do projeto:

```env
# Django
SECRET_KEY=sua-chave-super-segura
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Banco (produção)
DB_NAME=madereira_jd
DB_USER=parica
DB_PASSWORD=senha
DB_HOST=localhost
DB_PORT=5433
DB_CONN_MAX_AGE=600

# Links de recuperação de senha
SITE_DOMAIN=127.0.0.1:8000
SITE_PROTOCOL=http

# Email
# (Desenvolvimento: console backend; produção: SMTP)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=Romaneio de Madeiras <no-reply@localhost>
```

### Produção (lembretes)
- `DEBUG=False`
- `ALLOWED_HOSTS=seu-dominio.com.br,www.seu-dominio.com.br`
- `CSRF_TRUSTED_ORIGINS=https://seu-dominio.com.br,https://www.seu-dominio.com.br`
- `SITE_DOMAIN=seu-dominio.com.br`
- `SITE_PROTOCOL=https`
- Configure SMTP real (ex.: Gmail com **senha de app**)

---

## Recuperação de senha por e-mail

O sistema usa o fluxo padrão do Django com templates customizados em:

- `templates/registration/password_reset_form.html`
- `templates/registration/password_reset_done.html`
- `templates/registration/password_reset_confirm.html`
- `templates/registration/password_reset_complete.html`
- `templates/registration/password_reset_email.html`
- `templates/registration/password_reset_subject.txt`

Requisito: o usuário precisa ter **e-mail cadastrado** no perfil.

---

## Testes

### Rodar testes
```sh
python manage.py test -v 2
```

### Settings de teste (recomendado)
Se você tiver um settings dedicado para testes (ex.: `config.settings_test` usando SQLite), rode assim:

```sh
# Linux/macOS
DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test -v 2

# Windows PowerShell
$env:DJANGO_SETTINGS_MODULE="config.settings_test"
python manage.py test -v 2
```

> Para validar exportação PDF em CI/Linux, garanta que o ambiente tenha as dependências nativas do WeasyPrint instaladas.

---

## Deploy (produção) – checklist rápido

1. Ajustar `.env`:
   - `DEBUG=False`
   - `ALLOWED_HOSTS=...`
   - `CSRF_TRUSTED_ORIGINS=...`
   - `SITE_DOMAIN=...`
   - `SITE_PROTOCOL=https`
   - SMTP configurado

2. Coletar estáticos:
```sh
python manage.py collectstatic --noinput
```

3. Rodar check de segurança:
```sh
python manage.py check --deploy
```

4. Proxy/HTTPS (Nginx/Traefik)
Garanta headers e configurações de proxy conforme seu ambiente, por exemplo:
- `X-Forwarded-Proto`
- `X-Real-IP`
- `X-Forwarded-For`

---

## Contribuição (padrões)

- Use ORM e mantenha a separação por apps
- Evite “saldo manual”: saldo sempre derivado de vendas e pagamentos
- Relatórios novos: siga o padrão em `apps/relatorios/`
- Novas features: escreva/atualize testes junto com a implementação

---

## Licença

Projeto livre para uso acadêmico e comercial. Se existir um arquivo `LICENSE`, ele define os termos oficiais.