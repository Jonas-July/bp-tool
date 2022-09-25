"""
Django settings for bptool project.

Generated by 'django-admin startproject' using Django 3.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

from split_settings.tools import optional, include

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%76k-4a8a(43h#c)b7p)z$imf4!(47f@7f^5pru3#yh+p95-!)'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap4',
    'fontawesome_5',
    'debug_toolbar',
    'lti_provider',
    'bp',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bptool.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'bptool.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTHENTICATION_BACKENDS = [
  'django.contrib.auth.backends.ModelBackend',
  'lti_provider.auth.LTIBackend',
]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'de-DE'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

# Settings for Bootstrap
BOOTSTRAP4 = {
    # Use custom CSS
    "css_url": {
        "href": STATIC_URL + "bp/css/bootstrap.css",
    },
    "javascript_url": {
        "url": STATIC_URL + "bp/vendor/bootstrap/bootstrap-4.3.1.min.js",
    },
    "jquery_slim_url": {
        "url": STATIC_URL + "bp/vendor/jquery/jquery-3.3.1.slim.min.js",
    },
    "popper_url": {
        "url": STATIC_URL + "bp/vendor/popper/popper-1.14.7.min.js",
    },
}

# Settings for FontAwesome
FONTAWESOME_5_CSS_URL = STATIC_URL + "bp/vendor/fontawesome-5/all.min.css"
FONTAWESOME_5_PREFIX = "fa"

# Used for Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]

LTI_TOOL_CONFIGURATION = {
    'title': 'BP Tool',
    'description': 'BP Organization Support Tool',
    'launch_url': 'lti/',
    # 'embed_url': '<the view endpoint for an embed tool>' or '',
    # 'embed_icon_url': '<the icon url to use for an embed tool>' or '',
    # 'embed_tool_id': '<the embed tool id>' or '',
    'landing_url': '/log/',
    # 'course_aware': True,
    # 'course_navigation': True,
    # 'new_tab': <True or False>,
    # 'frame_width': <width in pixels>,
    # 'frame_height': <height in pixels>,
    # 'custom_fields': <dictionary>,
    # 'allow_ta_access': <True or False>,
    'course_aware': False,
    'assignments': {
        'log': 'log/',
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = True

PRETIX_BASE_URL = "https://<your-hostname>/"
PRETIX_ORGANIZER = "<organizer>"
PRETIX_API_BASE_URL = f"{PRETIX_BASE_URL}api/v1/"
PRETIX_API_ORGANIZER = PRETIX_ORGANIZER
PRETIX_API_TOKEN = "<secret-api-token>"

SEND_MAILS = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LOG_REMIND_PERIOD_DAYS = 7

LOGIN_URL = '/login/'

include(optional("settings/*.py"))
