import os
from .local_settings import *

APP_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))

DEBUG = True
THUMBNAIL_DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'pay.db',
    }
}
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = APP_ROOT + STATIC_URL
MEDIA_ROOT = STATIC_ROOT + 'media/'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(APP_ROOT, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # auth
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
)
ROOT_URLCONF = 'pay.tests.test_urls'
INSTALLED_APPS = (
    'pay',
    'django.contrib.staticfiles',

    # auth (for payments associated to users)
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.admin',
)
SECRET_KEY = 'foobar'
