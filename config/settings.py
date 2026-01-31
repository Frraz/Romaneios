import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do .env local e garante que sejam vistas
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------
# Segurança
# -------------
# Garanta que a SECRET_KEY real esteja no .env em produção!
SECRET_KEY = os.getenv('SECRET_KEY', 'troque-esta-chave-supersegura')
DEBUG = os.getenv('DEBUG', 'False').strip().lower() in ('true', '1', 'sim', 'yes')

# Suporta vírgula, espaço e mix para hosts. Adicione o domínio real no .env!
ALLOWED_HOSTS = [
    host for host in os.getenv('ALLOWED_HOSTS', 'localhost 127.0.0.1').replace(',', ' ').split()
    if host
]

LOGIN_URL = '/accounts/login/'  # Login padrão do Django

# -------------
# Apps instalados
# -------------
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Seus apps
    'apps.cadastros',
    'apps.romaneio',
    'apps.financeiro',
    'apps.relatorios',
    'apps.core',
]

# -------------
# Middleware
# -------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# -------------
# Templates
# -------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# -------------
# Banco de dados (PostgreSQL)
# -------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'madereira_jd'),
        'USER': os.getenv('DB_USER', 'parica'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'lorak'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5433'),
    }
}

# -------------
# Validação de senha
# -------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------
# Internacionalização
# -------------
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True  # Django 4+: deprecated, mas mantém para compatibilidade
USE_TZ = True

# -------------
# Arquivos estáticos e de mídia
# -------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# -------------
# Auto campo padrão
# -------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------
# Django messages adaptado ao Bootstrap
# -------------
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# -------------
# Produção: recomendações extras
# -------------
# Faça upload de estáticos com python manage.py collectstatic --noinput
# Configure staticfiles/ e media/ com Nginx para servir em produção

# Para e-mails de erro admins (opcional)
# ADMINS = [('Seu Nome', 'seuemail@dominio.com.br')]
# SERVER_EMAIL = 'erro@madereirajd.ferzion.com.br'
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS, EMAIL_USE_SSL...

# -------------
# Debug helpers
# -------------
if DEBUG:
    print("DEBUG = True | Django rodando em ambiente de desenvolvimento!")
    print("ALLOWED_HOSTS:", ALLOWED_HOSTS)
else:
    # Segurança extra em produção
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # SECURE_SSL_REDIRECT = True  # descomente se for só https (com certbot)
    # X_FRAME_OPTIONS = 'DENY'
    # LOGGING = {...}  # recomende configurar logging para erros graves

# -------------
# Espaço para futuras integrações
# -------------
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# REST_FRAMEWORK = {}
# CACHES = {}
# CELERY_BROKER_URL = ''
