from decouple import config, Csv
from pathlib import Path



#  BASE PATHS
# ===============================
BASE_DIR = Path(__file__).resolve().parent.parent



#  SECURITY
# ===============================
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())



#  APPLICATIONS
# ===============================
PROJECT_APPS = [
    "scheduler",
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
] + PROJECT_APPS



# MIDDLEWARE
# ===============================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'weight_department_schedule.urls'



#  TEMPLATES
# ===============================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'scheduler/ui/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'weight_department_schedule.wsgi.application'



#  DATABASE CONFIG
# ===============================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}



#  PASSWORD VALIDATORS
# ===============================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]



#  LOCALIZATION
# ===============================
LANGUAGE_CODE = 'bg'
TIME_ZONE = 'Europe/Sofia'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('bg', 'Български'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'accounts' / 'locale',
]



#  STATIC / MEDIA FILES
# ===============================
STATIC_ROOT = BASE_DIR / 'static'
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'scheduler/ui/static']



# MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'



#  PRIMARY KEY TYPE
# ===============================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


#  FRAMEWORK
# ===============================
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
