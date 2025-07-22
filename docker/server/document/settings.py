import os
from django.utils.translation import gettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'osis-document-secret'

DEBUG = True

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split()

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'django_celery_results',
    'osis_document',
    'debug',
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

ROOT_URLCONF = 'document.urls'

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

WSGI_APPLICATION = 'document.wsgi.application'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s',
            'datefmt': '%d-%m-%Y %H:%M:%S'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(message)s',
            'datefmt': '%d-%m-%Y %H:%M:%S'
        },
    },
    'handlers': {
         'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'default': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'queue_exception': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'send_mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("DATABASE_NAME", 'osis_document_local'),
        'USER': os.environ.get("POSTGRES_USER", 'osis'),
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD", 'osis'),
        'HOST':  os.environ.get("POSTGRES_HOST", '127.0.0.1'),
        'PORT': os.environ.get("POSTGRES_PORT", '5432'),
        'ATOMIC_REQUESTS': os.environ.get('DATABASE_ATOMIC_REQUEST', 'True').lower() == 'true',
    },
}

# I18N
LANGUAGE_CODE = 'fr-be'
LANGUAGES = [
    ('fr-be', _('French')),
    ('en', _('English')),
]

# Time
TIME_ZONE = 'Europe/Brussels'
USE_I18N = True
USE_L10N = True
USE_TZ = False


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Media
MEDIA_ROOT = os.path.join(BASE_DIR, "uploads")

# Osis document
# OSIS_DOCUMENT_BASE_URL = 'http://osis-document-server:9503/api/osis-document/'
OSIS_DOCUMENT_API_SHARED_SECRET = 'osis-document-api-shared-secret'
OSIS_DOCUMENT_DOMAIN_LIST = [
    'localhost',
    '127.0.0.1',
]
OSIS_DOCUMENT_UPLOAD_LIMIT = '10000/minute'
OSIS_DOCUMENT_TOKEN_MAX_AGE = 60 * 60
OSIS_DOCUMENT_TEMP_UPLOAD_MAX_AGE = 60 * 15
OSIS_DOCUMENT_ALLOWED_EXTENSIONS = ['pdf', 'txt', 'docx', 'doc', 'odt', 'png', 'jpg']

# Celery configuration
CELERY_BROKER_URL = "amqp://{user}:{password}@{host}:{port}".format(
    user=os.environ.get('RABBITMQ_USER', 'guest'),
    password=os.environ.get('RABBITMQ_PASSWORD', 'guest'),
    host=os.environ.get('RABBITMQ_HOST', 'localhost'),
    port=os.environ.get('RABBITMQ_PORT', '5672'),
)
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'django-db')
CELERY_TIMEZONE = os.environ.get('TIME_ZONE', 'Europe/Brussels')
DJANGO_CELERY_BEAT_TZ_AWARE = os.environ.get('USE_TZ', 'False').lower() == 'true'
CELERY_ENABLE_UTC = False


# OpenTelemetry
# OTEL_ENABLED = True
# OTEL_PYTHON_DJANGO_INSTRUMENT = True
# OTEL_PYTHON_DJANGO_EXCLUDED_URLS="/admin/*"
# OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST=".*"
# OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE=".*"
# OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SANITIZE_FIELDS=".*session.*,set-cookie,cookie,Authorization,X_USER_GLOBALID,X_USER_EMAIL,X_USER_FIRSTNAME,X_USER_LASTNAME"
# OTEL_EXPORTER_OTLP_ENDPOINT="http://jaeger:4317"
# OTEL_EXPORTER_OTLP_INSECURE = True
# OTEL_SERVICE_NAME = "OSIS-DOCUMENT"
# OTEL_TRACER_MODULE_NAME = "OSIS"
# OTEL_TRACER_LIBRARY_VERSION = "1.0.0"
