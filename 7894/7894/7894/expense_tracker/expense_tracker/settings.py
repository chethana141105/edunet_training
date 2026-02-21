import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from decouple import config

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tracker',
    'chatbot',
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

ROOT_URLCONF = 'expense_tracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'expense_tracker.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

EXPENSE_CATEGORIES = [
    ('Food', 'Food & Dining'),
    ('Travel', 'Travel'),
    ('Rent', 'Rent & Housing'),
    ('Shopping', 'Shopping'),
    ('Entertainment', 'Entertainment'),
    ('Utilities', 'Utilities'),
    ('Healthcare', 'Healthcare'),
    ('Education', 'Education'),
    ('Insurance', 'Insurance'),
    ('Other', 'Other'),
]

MOOD_CHOICES = [
    ('happy', 'Happy'),
    ('neutral', 'Neutral'),
    ('stressed', 'Stressed'),
]

SPENDING_PERSONALITIES = {
    'planner': {
        'name': 'Planner',
        'description': 'You plan your spending carefully and stick to budgets',
        'color': '#3b82f6',
    },
    'impulse_spender': {
        'name': 'Impulse Spender',
        'description': 'You tend to make spontaneous purchases',
        'color': '#ef4444',
    },
    'minimalist': {
        'name': 'Minimalist',
        'description': 'You keep spending to essentials only',
        'color': '#10b981',
    },
    'balanced': {
        'name': 'Balanced',
        'description': 'You balance savings and spending well',
        'color': '#f59e0b',
    },
}

# Chatbot Integration
GROQ_API_KEY = config('GROQ_API_KEY', default=None)

