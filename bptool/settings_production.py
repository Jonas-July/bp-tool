"""
This is the settings file used in production.
First, it imports all default settings, then overrides respective ones.
Secrets are stored in and imported from an additional file, not set under version control.
"""

import bptool.settings_secrets as secrets

# noinspection PyUnresolvedReferences
from bptool.settings import *

STATIC_ROOT = secrets.STATIC_ROOT

### SECURITY ###

DEBUG = False

ALLOWED_HOSTS = secrets.HOSTS

SECRET_KEY = secrets.SECRET_KEY

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

### DATABASE ###

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': getattr(secrets, "DB_HOST", "localhost"),
        'PORT': getattr(secrets, "DB_PORT", "5432"),
        'NAME': secrets.DB_NAME,
        'USER': secrets.DB_USER,
        'PASSWORD': secrets.DB_PASSWORD,
    }
}

### MAIL

SEND_MAILS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = secrets.EMAIL_HOST
EMAIL_PORT = secrets.EMAIL_PORT
EMAIL_USE_TLS = secrets.EMAIL_USE_TLS
EMAIL_HOST_USER = secrets.EMAIL_HOST_USER
