"""
Django settings for Office Smart Appointments Management System.
"""

import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-dev-key-change-in-production'

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
    'django.contrib.postgres',
    'rest_framework',
    'drf_spectacular',
    'apps.core',
    'apps.notify',  # Sistem de notificări prin email
]

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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Director pentru template-uri globale
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


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Database configuration - folosește variabile de mediu pentru Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'office_appointments'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Autentificare: JWT Token
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # Permisiuni: implicit trebuie să fii autentificat
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Office Smart Appointments API',
    'DESCRIPTION': 'Molson Coors – Smart Appointments (Rooms, Items, Requests, Appointments).',
    'VERSION': '0.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': 'Rooms', 'description': 'Camere rezervabile'},
        {'name': 'ItemCategories', 'description': 'Categorii de inventar'},
        {'name': 'Items', 'description': 'Inventar pe camere'},
        {'name': 'Requests', 'description': 'Cereri de rezervare pe camere'},
        {'name': 'Appointments', 'description': 'Programări pe item'},
        {'name': 'Users', 'description': 'Utilizatori'},
        {'name': 'Auth', 'description': 'Autentificare și profil'},
    ],
}

# JWT Settings (Simple JWT)
SIMPLE_JWT = {
    # Token-ul expiră după 1 oră (poți ajusta)
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    # Refresh token-ul expiră după 7 zile
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    # Token-ul se reînnoiește automat la fiecare request
    'ROTATE_REFRESH_TOKENS': True,
    # Când se reînnoiește, vechiul token devine invalid
    'BLACKLIST_AFTER_ROTATION': True,
}

# Email Settings
# Pentru development, folosim console backend (email-urile se afișează în consolă)
# Pentru producție, configurează SMTP sau un serviciu extern (SendGrid, AWS SES, etc.)
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'  # Development: afișează în consolă
)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@molsoncoors.com')

# Pentru producție, configurează SMTP:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@example.com'
# EMAIL_HOST_PASSWORD = 'your-password'

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minute
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minute
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True

# Celery Beat Schedule (task-uri periodice)
CELERY_BEAT_SCHEDULE = {
    'process-email-queue': {
        'task': 'notify.process_email_queue',
        'schedule': 60.0,  # Rulează la fiecare 60 de secunde (1 minut)
        'options': {
            'expires': 30.0,  # Task-ul expiră după 30 de secunde dacă nu e preluat
        }
    },
}

