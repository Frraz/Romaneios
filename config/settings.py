import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do .env local (caminho padrão: BASE_DIR/.env)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# -------------
# Segurança
# -------------
SECRET_KEY = os.getenv('SECRET_KEY', 'troque-esta-chave-supersegura')
DEBUG = os.getenv('DEBUG', '').strip().lower() in ('true', '1', 'yes', 'sim')

ALLOWED_HOSTS = [
    host.strip() for host in os.getenv('ALLOWED_HOSTS', 'localhost 127.0.0.1').replace(',', ' ').split()
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    "https://madereirajd.ferzion.com.br"
]

LOGIN_URL = '/accounts/login/'

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
    'widget_tweaks',

    # Apps do projeto
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
        'DIRS': [BASE_DIR / "templates"],  # Templates globais
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
        # 'CONN_MAX_AGE': 600, # Opcional: persistência de conexões p/ produção
    }
}

# -------------
# Validação de senha
# -------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------
# Internacionalização
# -------------
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True  # Suporte para formatação local de dados
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
# Campo padrão para modelos
# -------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------
# Django messages & Bootstrap
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
# Segurança extra para produção
# -------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'  # Protege contra clickjacking
    # Lembre de configurar HTTPS no servidor e remover da lista de hosts o "localhost" em prod
    # LOGGING = {...}  # Adicione logging detalhado de erros/falhas para produção

# -------------
# Email (Password reset / notificações)
# -------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").strip().lower() in ("true", "1", "yes", "sim")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").strip().lower() in ("true", "1", "yes", "sim")

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@localhost")

# Domínio/protocolo para links no e-mail de reset
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "127.0.0.1:8000")
SITE_PROTOCOL = os.getenv("SITE_PROTOCOL", "http")

# -------------
# Debug helpers
# -------------
if DEBUG:
    print("DEBUG = True | Django rodando em ambiente de desenvolvimento!")
    print("ALLOWED_HOSTS:", ALLOWED_HOSTS)

# -------------
# Integrações futuras (REST, cache, etc)
# -------------
# REST_FRAMEWORK = {}
# CACHES = {}
# CELERY_BROKER_URL = ''