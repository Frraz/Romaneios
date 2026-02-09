from __future__ import annotations

from .settings import *  # noqa: F403, F401


# Testes devem ser determinísticos e sem dependência de infra externa
DEBUG = False

# SQLite em memória (rápido) — para suite grande pode trocar para arquivo em BASE_DIR / "test_db.sqlite3"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Segurança: durante testes não precisa forçar HTTPS redirect
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False