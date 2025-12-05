# videla/settings.py
import os
from pathlib import Path
import dj_database_url  # Para manejar DATABASE_URL (PostgreSQL en Render)

# Cloudinary
import cloudinary
import cloudinary.uploader
import cloudinary.api


# ==========================
# RUTA BASE DEL PROYECTO
# ==========================
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

    # Cloudinary
    "cloudinary",
    "cloudinary_storage",
]


# ==========================
# MIDDLEWARE
# ==========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise para producción
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==========================
# URLS / TEMPLATES / WSGI
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
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
    )
}


# ==========================
# PASSWORDS
# ==========================
AUTH_PASSWORD_VALIDATORS = []


# ==========================
# IDIOMA / HORARIO
# ==========================
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Punta_Arenas"
USE_I18N = True
USE_TZ = True


# ==========================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ==========================
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "menu" / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# ⚡ SISTEMA MODERNO DE DJANGO 4.2 (STORAGES)
STORAGES = {
    # ---------------------------
    # Almacenamiento de MEDIA → Cloudinary
    # ---------------------------
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },

    # ---------------------------
    # Archivos estáticos → WhiteNoise
    # ---------------------------
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Aunque Django ya no usa MEDIA_ROOT con Cloudinary, no molesta dejarlo
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ==========================
# CLOUDINARY CONFIG
# ==========================
# Valores base para Cloudinary (pueden venir de entorno o ir fijos)
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "dlnjnqqtx")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "449198878636936")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "mtFqu2l3C2-nLMLiFtkZ6CqWVd0")

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
    "API_KEY": CLOUDINARY_API_KEY,
    "API_SECRET": CLOUDINARY_API_SECRET,
}

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)


# ==========================
# CONFIG GENERAL
# ==========================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")


# ==========================
# JAZZMIN
# ==========================
JAZZMIN_SETTINGS = {
    "site_title": "Panel Quincho Videla",
    "site_header": "Quincho Videla",
    "site_brand": "Quincho Videla",
    "welcome_sign": "Bienvenido al panel de administración",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",
    "navbar": "navbar-dark",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "body_small_text": False,
}

WHATSAPP_NUMERO = os.getenv("WHATSAPP_NUMERO", "56997121129")
