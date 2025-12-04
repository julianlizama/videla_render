# videla/settings.py
import os
from pathlib import Path
import dj_database_url  # Para manejar DATABASE_URL (PostgreSQL en Render)

# RUTA BASE DEL PROYECTO
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================
# AUTENTICACIÓN / LOGIN
# ==========================
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "caja:caja_panel"
LOGOUT_REDIRECT_URL = "index"  # volver al inicio público

# ==========================
# SEGURIDAD / DEBUG
# ==========================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "*").split(",")
    if h.strip()
]

# Si quieres, puedes agregar explícitamente tu dominio de Render:
# CSRF_TRUSTED_ORIGINS = [
#     "https://videla-web.onrender.com",
# ]

# ==========================
# APLICACIONES INSTALADAS
# ==========================
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps del proyecto
    "menu",
    "caja",
]

# ==========================
# MIDDLEWARE
# ==========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise para servir estáticos en producción
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ==========================
# URLs / TEMPLATES / WSGI
# ==========================
ROOT_URLCONF = "videla.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "menu" / "templates",
            BASE_DIR / "caja" / "templates",
        ],
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

WSGI_APPLICATION = "videla.wsgi.application"

# ==========================
# BASE DE DATOS
# ==========================
# En local (sin DATABASE_URL) → SQLite
# En Render (con DATABASE_URL) → PostgreSQL
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv(
            "DATABASE_URL",
            f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        ),
        conn_max_age=600,  # Mantiene conexiones abiertas (bueno para prod)
    )
}

# ==========================
# PASSWORDS / VALIDADORES
# ==========================
AUTH_PASSWORD_VALIDATORS = []  # Puedes agregar validadores si quieres

# ==========================
# IDIOMA / ZONA HORARIA
# ==========================
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Punta_Arenas"
USE_I18N = True
USE_TZ = True

# ==========================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ==========================
STATIC_URL = "/static/"

# Archivos estáticos del proyecto (CSS, JS, imágenes públicas)
STATICFILES_DIRS = [
    BASE_DIR / "menu" / "static",
]

# Carpeta donde collectstatic deja los archivos para producción
STATIC_ROOT = BASE_DIR / "staticfiles"

# Django 4.2+ usa STORAGES en lugar de STATICFILES_STORAGE
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # WhiteNoise con compresión y manifest
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Archivos subidos por usuarios
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==========================
# CONFIG GENERAL
# ==========================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==========================
# VARIABLES PERSONALIZADAS
# ==========================
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")

# ==========================
# JAZZMIN (Panel Admin)
# ==========================
JAZZMIN_SETTINGS = {
    "site_title": "Panel Quincho Videla",
    "site_header": "Quincho Videla",
    "site_brand": "Quincho Videla",
    "welcome_sign": "Bienvenido al panel de administración",
    "copyright": "Quincho Videla",
    # "site_logo": "logo.png",  # cuando tengas un logo en /static
}

JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",          # Tema oscuro
    "navbar": "navbar-dark",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "body_small_text": False,
}
