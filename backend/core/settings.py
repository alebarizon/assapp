"""
Configurações Django — AssApp (PIPE FAPESP Fase 1)
Multi-tenancy via django-tenants, JWT, apps de mandatos/memoria/eventos.
"""

import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "assapp-dev-secret-change-in-production")
DEBUG = os.environ.get("DEBUG", "False") == "True"

_allowed_hosts_env = os.environ.get("ALLOWED_HOSTS", "")
_base_domain = os.environ.get("BASE_DOMAIN", "assapp.local")
ALLOWED_HOSTS = (
    [h.strip() for h in _allowed_hosts_env.split(",") if h.strip()]
    if _allowed_hosts_env
    else ["localhost", "127.0.0.1", "sistema.localhost", _base_domain]
)

SHARED_APPS = (
    "django_tenants",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "core",
    "tenants",
    "accounts",
    "support",
)

TENANT_APPS = (
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "accounts",
    "mandatos",
    "memoria",
    "eventos",
    "membros",
    "finance",
    "documents",
    "ecommerce",
    "website",
    "courses",
    "formularios",
    "contatos",
    "mensagens",
    "payments",
    "publicacoes",
    "governanca",
    "newsletter",
)

INSTALLED_APPS = list(dict.fromkeys(SHARED_APPS + TENANT_APPS))

MIDDLEWARE = [
    "core.middleware.TenantPathMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.TenantUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": os.environ.get("DB_NAME", "assapp_db"),
        "USER": os.environ.get("DB_USER", "assapp_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "assapp_dev_password"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"
PUBLIC_SCHEMA_NAME = "public"
SYSTEM_TENANT_SCHEMA = "sistema"
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True
BASE_DOMAIN = os.environ.get("BASE_DOMAIN", "assapp.local")

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
# Produto só em português: o LocaleMiddleware não troca para inglês pelo Accept-Language do navegador
LANGUAGES = [("pt-br", "Português (Brasil)")]
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.authentication.TenantAwareJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_RATES": {
        "formularios_public": "60/min",
        "contatos_public": "10/hour",
        "certificados_public": "30/min",
        "senha_public": "10/hour",
    },
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 60))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.environ.get("JWT_REFRESH_TOKEN_LIFETIME_DAYS", 7))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = (
    os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")
    if not DEBUG
    else []
)
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ["Content-Disposition"]
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://localhost:5173",
).split(",")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "DEBUG" if DEBUG else "INFO"},
}

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@assapp.local")
NEWSLETTER_POR_MINUTO = int(os.environ.get("NEWSLETTER_POR_MINUTO", "30"))
# Base dos links enviados por e-mail (convites, certificados, portal)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5174")

# Sem gateway configurado na associação, permite cobranças fictícias (dev/demo).
PAGAMENTO_SIMULADO = os.environ.get("PAGAMENTO_SIMULADO", str(DEBUG)) == "True"
# Caixa da equipe Gesttora que recebe avisos de chamados de suporte (vazio = sem aviso)
SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "")
