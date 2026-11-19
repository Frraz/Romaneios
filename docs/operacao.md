# Operação

Como o sistema roda em produção, como publicar, reverter, consultar logs e fazer backup. Os valores reais do servidor (domínio, caminhos, usuário do banco) ficam num arquivo local não versionado; aqui usamos exemplos: `app.exemplo.com.br`, `/srv/romaneios`, banco `romaneios`.

## Ambiente de produção

| Peça | Como é | Onde está definido |
|---|---|---|
| Servidor | VPS Ubuntu | Fora do repositório |
| Python | 3.12, em `venv/` dentro da pasta do projeto | Criado à mão na primeira instalação |
| Aplicação | Gunicorn como serviço systemd `gunicorn_romaneios`, carregando `config.wsgi`. O Gunicorn não consta em `requirements.txt`: foi instalado à parte no `venv/` | Unidade systemd fora do repositório (a confirmar) |
| Proxy e HTTPS | Nginx na frente do Gunicorn | Fora do repositório (a confirmar, P-02) |
| Banco | PostgreSQL, porta 5433 por padrão | `.env` do servidor |
| Estáticos | `collectstatic` grava em `staticfiles/` | `STATIC_ROOT` em `config/settings.py` |
| E-mail | SMTP (padrão `smtp.gmail.com:587`, TLS) | `.env` do servidor |

Com `DEBUG=False`, o Django não serve `/static/` nem `/media/`. O Nginx precisa servir `staticfiles/` em `/static/` e `media/` em `/media/`; o logo da tela de login é `/media/image.png` (DT-20).

## Deploy automático

Todo push na branch `main` dispara `.github/workflows/deploy.yml`, que entra na VPS por SSH e executa, na pasta do projeto:

1. `git pull`
2. Confere se `venv/` existe (se não existir, o deploy falha)
3. `pip install -r requirements.txt --break-system-packages`
4. `python manage.py migrate --noinput`
5. `python manage.py collectstatic --noinput`
6. `sudo systemctl restart gunicorn_romaneios`

Segredos do repositório no GitHub (Settings → Secrets and variables → Actions):

| Segredo | Conteúdo |
|---|---|
| `VPS_SSH_PRIVATE_KEY` | Chave privada com acesso SSH à VPS |
| `VPS_USER` | Usuário SSH (precisa de `sudo` sem senha para o `systemctl restart`) |
| `VPS_HOST` | Endereço da VPS |

Cuidados:

- **Qualquer push na `main` publica e reinicia o serviço**, inclusive um commit só de documentação. Trabalhe em outra branch e faça o merge quando quiser publicar.
- O workflow **não roda os testes** antes de publicar (DT-14). Rode-os localmente antes do push ([desenvolvimento.md](desenvolvimento.md#testes)).
- Migrações são aplicadas automaticamente. Migração que altera ou remove dados exige backup antes do push.

Acompanhe a execução na aba **Actions** do repositório.

## Primeira instalação

Passos para montar um servidor novo, deduzidos do workflow e das configurações. A configuração exata do Nginx e do systemd não está no repositório.

1. Instale as dependências do sistema: Python 3.12 com `venv`, PostgreSQL, Nginx e as bibliotecas do WeasyPrint (lista no topo de `requirements.txt`).
2. Crie o banco e o usuário:

   ```bash
   sudo -u postgres createuser --pwprompt romaneios
   sudo -u postgres createdb -O romaneios romaneios
   ```

3. Clone o repositório e crie o ambiente:

   ```bash
   git clone <url-do-repositorio> /srv/romaneios
   cd /srv/romaneios
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn            # não está no requirements.txt
   ```

4. Crie o `.env` a partir do `.env.example`, com os valores de produção:

   ```env
   SECRET_KEY=<chave longa e aleatória>
   DEBUG=False
   ALLOWED_HOSTS=app.exemplo.com.br,www.app.exemplo.com.br
   CSRF_TRUSTED_ORIGINS=https://app.exemplo.com.br,https://www.app.exemplo.com.br
   SITE_DOMAIN=app.exemplo.com.br
   SITE_PROTOCOL=https
   SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
   ```

   Mais as variáveis de banco e de SMTP. Para gerar a chave: `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`.

5. Prepare o banco e os estáticos:

   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   python manage.py check --deploy
   ```

6. Configure a unidade systemd `gunicorn_romaneios` (Gunicorn com `config.wsgi:application`) e o site no Nginx (proxy para o Gunicorn, `/static/` e `/media/`, HTTPS, cabeçalhos `X-Forwarded-Proto`, `X-Forwarded-For` e `Host`).
7. Cadastre os três segredos no GitHub para ativar o deploy automático.

Confirme acessando `https://app.exemplo.com.br/`: a tela de login deve aparecer com o logo.

`SECURE_PROXY_SSL_HEADER` recebe o nome do cabeçalho como o Django o vê no `request.META` (`HTTP_X_FORWARDED_PROTO`) e o valor esperado, separados por vírgula. O exemplo no comentário de `config/settings.py` (`X-Forwarded-Proto,https`) não funciona, porque o Django não encontra essa chave. Sem a variável correta, atrás do Nginx, `SECURE_SSL_REDIRECT` pode causar redirecionamento infinito.

## Atualizar manualmente

Se o GitHub Actions estiver indisponível, rode na VPS os mesmos passos do workflow:

```bash
cd /srv/romaneios
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn_romaneios
```

## Reverter uma publicação

Para desfazer um commit que quebrou a produção, sem reescrever o histórico:

```bash
git revert <hash-do-commit>
git push origin main        # o deploy automático publica a reversão
```

Se o commit tinha migração, o `revert` não desfaz o banco. Antes de reverter o código, volte a migração na VPS:

```bash
python manage.py migrate <app> <migração-anterior>
```

Migrações de dados, como a `romaneio/0005`, não têm volta segura: restaure o backup.

Confirme com `sudo systemctl status gunicorn_romaneios` e abrindo o sistema.

## Logs

O Django escreve no console (`LOGGING` em `config/settings.py`, nível `INFO` em produção), e o systemd guarda:

```bash
sudo journalctl -u gunicorn_romaneios -n 200 --no-pager
sudo journalctl -u gunicorn_romaneios -f
```

Logs do Nginx costumam ficar em `/var/log/nginx/` (a confirmar). Não há envio de e-mail de erro para administradores: `ADMINS` não está configurado.

## Backup e restauração

**Não existe rotina de backup automática hoje** (DT-02). Até ela existir, faça um backup manual antes de toda publicação com migração.

Backup:

```bash
pg_dump -h localhost -p 5433 -U romaneios -Fc romaneios > romaneios_$(date +%F).dump
```

Guarde o arquivo **fora da VPS**. Junto com ele, guarde o `.env` de produção (tem a `SECRET_KEY`).

Restauração, num banco vazio:

```bash
sudo systemctl stop gunicorn_romaneios
sudo -u postgres dropdb romaneios
sudo -u postgres createdb -O romaneios romaneios
pg_restore -h localhost -p 5433 -U romaneios -d romaneios --no-owner romaneios_AAAA-MM-DD.dump
sudo systemctl start gunicorn_romaneios
```

Confirme abrindo o dashboard e conferindo o saldo de um cliente conhecido.

A pasta `media/` só contém o logo, que está no repositório; não precisa de backup próprio.

## Problemas conhecidos

| Sintoma | Causa e solução |
|---|---|
| PDF responde "Falha ao gerar PDF" ou "WeasyPrint não está disponível" | Faltam as bibliotecas nativas do WeasyPrint no servidor. Instale-as (topo de `requirements.txt`) e reinicie o serviço. O resto do sistema segue funcionando |
| Erro 403 "CSRF verification failed" ao enviar formulários | O domínio não está em `CSRF_TRUSTED_ORIGINS` (com `https://`). Sem a variável, o sistema usa só `https://<SITE_DOMAIN>`; o endereço com `www` precisa ser declarado |
| Redirecionamento infinito para HTTPS | `SECURE_PROXY_SSL_HEADER` ausente ou o Nginx não envia `X-Forwarded-Proto` |
| Link do e-mail de redefinição aponta para endereço errado | Ajuste `SITE_DOMAIN` e `SITE_PROTOCOL` no `.env` |
| Logo some da tela de login | `/media/` não é servido pelo Nginx (DT-20). A tela continua funcionando: a imagem se esconde se não carregar |
| Erro 500 ao excluir tipo de madeira | A madeira está em algum romaneio (DT-07). Marque-a como inativa em vez de excluir |
| Deploy falha com "Virtualenv não existe" | Crie o `venv/` na pasta do projeto na VPS (primeira instalação, passo 3) |
| Deploy falha no `sudo systemctl restart` | O usuário SSH precisa de `sudo` sem senha para esse comando |

## Nunca em produção

- `python manage.py mock_dados`: cria centenas de registros fictícios e 60 usuários staff.
- `QuerySet.update()` ou SQL direto em itens e unidades: deixa os totais dos romaneios errados.
- `DEBUG=True`: expõe detalhes internos nas páginas de erro.
