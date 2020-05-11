"""
Django settings for wordknow project.

Generated by 'django-admin startproject' using Django 2.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
from datetime import timedelta

import enchant
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# environments in main directory
env_file_path = os.path.join(BASE_DIR, '../.env')
if os.path.exists(env_file_path):
    load_dotenv(dotenv_path=env_file_path, verbose=True)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '@zh4@xgoscsx)20c-(k#)h%@$40p#rzrx&mg$p)^4c17_9omsd'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'app',
    'telegram',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME', 'wordknow_db'),
        'USER': os.getenv('DB_USER', 'wordknow'),
        'PASSWORD': os.getenv('DB_PASSWORD', '123'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'
DEFAULT_TIMEZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_FILES_BASE_DIR = os.environ.get('STATIC_FILES_BASE_DIR', '/app_static_files/')
STATIC_ROOT = os.path.join(STATIC_FILES_BASE_DIR, 'static/')
LOGS_PATH = os.environ.get('LOGS_PATH', 'logs')
if not os.path.exists(LOGS_PATH):
    os.mkdir(LOGS_PATH)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'api_verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple' if DEBUG else 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_PATH, 'base_debug.log'),
            'formatter': 'verbose',
        },
        'telegram': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_PATH, 'telegram.log'),
            'formatter': 'verbose',
        },
        'telegram_tasks': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_PATH, 'telegram_tasks.log'),
            'formatter': 'verbose',
        },
        'telegram_handlers': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_PATH, 'telegram_handlers.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'app': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'telegram': {
            'handlers': ['console', 'telegram'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'telegram_tasks': {
            'handlers': ['console', 'telegram_tasks'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'telegram_handlers': {
            'handlers': ['console', 'telegram_handlers'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
    },
}

REPETITION_TIMES = {
    1: timedelta(hours=1),
    2: timedelta(hours=6),
    3: timedelta(days=1),
    4: timedelta(days=3),
}

# retry connect to db
COUNT_TRIES_CONNECT = 100
SLEEP_TIME = 1

# -------- telegram ----------
TELEGRAM_BOT_KEY = os.environ.get('TELEGRAM_BOT_KEY', '')
TELEGRAM_BOT_NAME = os.environ.get('TELEGRAM_BOT_NAME', '')
TELEGRAM_DEBUG = os.environ.get('TELEGRAM_DEBUG', 'false').lower() == 'true'

BOT_SITE_URL = os.environ.get('BOT_SITE_URL', 'http://localhost:8000')

# for using EN dict, we must install aspell-en and enchant
LANG_DICT = {
    'en': enchant.Dict("en_US"),
}
