import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-insecure-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    "https://*.replit.dev",
    "https://*.repl.co",
    "https://*.replit.app",
    "https://*.kirk.replit.dev",
    "https://*.picard.replit.dev",
    "https://*.janeway.replit.dev",
    "https://*.spock.replit.dev",
    "https://*.riker.replit.dev",
    "https://*.worf.replit.dev",
    "http://localhost",
    "http://127.0.0.1",
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "widget_tweaks",
    "core",
    "customers",
    "inventory",
    "jobcards",
    "billing",
    "reminders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "autoservice.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.app_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "autoservice.wsgi.application"

import pymysql
pymysql.install_as_MySQLdb()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("MYSQL_DB", "autocare"),
        "USER": os.environ.get("MYSQL_USER", "root"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD", "123456"),
        "HOST": os.environ.get("MYSQL_HOST", "localhost"),
        "PORT": os.environ.get("MYSQL_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

GST_RATE = float(os.environ.get("GST_RATE", "18"))
SHOP_NAME = os.environ.get("SHOP_NAME", "SANJAY AUTOWORKS")
SHOP_ADDRESS = os.environ.get("SHOP_ADDRESS", "OPP. KMF, LAKAMANAHALLI, P.B. ROAD, DHARWAD - 580008")
SHOP_PHONE = os.environ.get("SHOP_PHONE", "9448235700")
SHOP_GSTIN = os.environ.get("SHOP_GSTIN", "29AQZPS4215N1ZR")
SHOP_EMAIL = os.environ.get("SHOP_EMAIL", "sanjayautoworks@gmail.com")

# Twilio messaging (SMS + WhatsApp)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")

# SMS — set TWILIO_SMS_FROM to your Twilio phone number e.g. +14155238886
SMS_ENABLED = os.environ.get("SMS_ENABLED", "0") == "1"
TWILIO_SMS_FROM = os.environ.get("TWILIO_SMS_FROM", "")

# WhatsApp — set TWILIO_WHATSAPP_FROM to e.g. whatsapp:+14155238886
WHATSAPP_ENABLED = os.environ.get("WHATSAPP_ENABLED", "0") == "1"
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "")
WHATSAPP_COUNTRY_CODE = os.environ.get("WHATSAPP_COUNTRY_CODE", "+91")
