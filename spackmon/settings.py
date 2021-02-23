# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
import tempfile
import yaml
import sys

from django.core.management.utils import get_random_secret_key
from datetime import datetime
from importlib import import_module

# Build paths inside the project with the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# The spackmon global conflict contains all settings.
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.yml")
if not os.path.exists(SETTINGS_FILE):
    sys.exit("Global settings file settings.yml is missing in the install directory.")


# Read in the settings file to get settings
class Settings:
    """convert a dictionary of settings (from yaml) into a class"""

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        setattr(self, "UPDATED_AT", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))

    def __str__(self):
        return "[spackmon-settings]"

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        for key, value in self.__dict__.items():
            yield key, value


with open(SETTINGS_FILE, "r") as fd:
    cfg = Settings(yaml.load(fd.read(), Loader=yaml.FullLoader))

# For each setting, if it's defined in the environment with spackmon_ prefix, override
for key, value in cfg:
    envar = os.getenv("SPACKMON_%s" % key)
    if envar:
        setattr(cfg, key, envar)

# Secret Key and Dates


def generate_secret_keys(filename):
    """A helper function to write a randomly generated secret key to file"""
    with open(filename, "w") as fd:
        for keyname in ["SECRET_KEY", "JWT_SERVER_SECRET"]:
            key = get_random_secret_key()
            fd.writelines("%s = '%s'\n" % (keyname, key))


def generate_creation_date(filename):
    """Keep track of when the server was generated for metadata"""
    created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(filename, "w") as fd:
        fd.writelines("SERVER_CREATION_DATE = '%s'\n" % created_at)


# Generate secret keys if do not exist, and not defined in environment
SECRET_KEY = os.environ.get("SECRET_KEY")
JWT_SERVER_SECRET = os.environ.get("JWT_SERVER_SECRET")
SERVER_CREATION_DATE = os.environ.get("CREATION_DATE")

if not SECRET_KEY or not JWT_SERVER_SECRET:
    try:
        from .secret_key import SECRET_KEY, JWT_SERVER_SECRET
    except ImportError:
        generate_secret_keys(os.path.join(BASE_DIR, "secret_key.py"))
        from .secret_key import SECRET_KEY, JWT_SERVER_SECRET

# A record of the server creation date
if not SERVER_CREATION_DATE:
    try:
        from .creation_date import SERVER_CREATION_DATE
    except ImportError:
        generate_creation_date(os.path.join(BASE_DIR, "creation_date.py"))
        from .creation_date import SERVER_CREATION_DATE

# Set the domain name
DOMAIN_NAME = cfg.DOMAIN_NAME
if cfg.DOMAIN_PORT:
    DOMAIN_NAME = "%s:%s" % (DOMAIN_NAME, cfg.DOMAIN_PORT)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.getenv("DEBUG") != "false" else False

# Derive list of plugins enabled from the environment (currently none)
PLUGINS_LOOKUP = {}
PLUGINS_ENABLED = []
for key, enabled in PLUGINS_LOOKUP.items():
    plugin_key = "PLUGIN_%s_ENABLED" % key.upper()
    if hasattr(cfg, plugin_key) and getattr(cfg, plugin_key) is not None:
        PLUGINS_ENABLED.append(key)

# SECURITY WARNING: App Engine's security features ensure that it is safe to
# have ALLOWED_HOSTS = ['*'] when the app is deployed. If you deploy a Django
# app not on App Engine, make sure to set an appropriate host here.
# See https://docs.djangoproject.com/en/2.1/ref/settings/
ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    # base will eventually have the home to the interfaces
    #    "spackmon.apps.base",
    # api includes all api endpoints for spack to interact with
    "spackmon.apps.api",
    # main includes the main application models
    "spackmon.apps.main",
    # users is relevant to create an authenticated user
    "spackmon.apps.users",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.humanize",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "crispy_forms",
    "social_django",
    "rest_framework",
    "rest_framework.authtoken",
]


CRISPY_TEMPLATE_PACK = "bootstrap4"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "spackmon.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "spackmon.context_processors.globals",
            ],
        },
    },
]

TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG
WSGI_APPLICATION = "spackmon.wsgi.application"

# Authentication and Users

AUTH_USER_MODEL = "users.User"
SOCIAL_AUTH_USER_MODEL = "users.User"
GRAVATAR_DEFAULT_IMAGE = "retro"

# TODO: add authenticated views here
AUTHENTICATED_VIEWS = [
    "spackmon.apps.api.views.specs.NewSpec",
    "spackmon.apps.api.views.specs.UpdateSpecMetadata",
    "spackmon.apps.api.views.builds.UpdateBuildStatus",
    "spackmon.apps.api.views.builds.UpdatePhaseStatus",
]

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases


# Always use sqlite for testing
running_tests = "tests" in sys.argv or "runtests.py" in sys.argv
if running_tests or cfg.USE_SQLITE:

    dbfile = "test-db.sqlite" if running_tests else os.path.join(BASE_DIR, "db.sqlite3")
    print("Using sqlite for database: %s" % dbfile)
    # A user might want to use sqlite instead
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": dbfile,
        }
    }

# Database local development uses DATABASE_* variables
elif os.getenv("DATABASE_HOST") is not None:
    # Make sure to export all of these in your .env file
    DATABASES = {
        "default": {
            "ENGINE": os.environ.get("DATABASE_ENGINE", "django.db.backends.mysql"),
            "HOST": os.environ.get("DATABASE_HOST"),
            "USER": os.environ.get("DATABASE_USER"),
            "PASSWORD": os.environ.get("DATABASE_PASSWORD"),
            "NAME": os.environ.get("DATABASE_NAME"),
        }
    }

else:

    # Fall back to database in postgres container
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "postgres",
            "USER": "postgres",
            "HOST": "db",
            "PORT": "5432",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa: 501
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",  # noqa: 501
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",  # noqa: 501
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",  # noqa: 501
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = "static"
STATIC_URL = "/static/"
MEDIA_ROOT = "data"
MEDIA_URL = "/data/"

# Caches

# Do we want to enable the cache?

# Cache to tmp
# The default cache is for views, likely not used until we have them
CACHE_LOCATION = os.path.join(tempfile.gettempdir(), "spackmon-cache")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": CACHE_LOCATION,
    }
}

CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = 86400  # one day

if not os.path.exists(CACHE_LOCATION):
    os.mkdir(CACHE_LOCATION)

# Add cache middleware
for entry in [
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
]:
    if entry not in MIDDLEWARE:
        MIDDLEWARE.append(entry)


# Create a filesystem cache for temporary upload sessions
cache = cfg.CACHE_DIR or os.path.join(MEDIA_ROOT, "cache")
if not os.path.exists(cache):
    os.makedirs(cache)

CACHES.update(
    {
        "spackmon_api": {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": cache,
        }
    }
)


# Rate Limiting

# Set to very high values to allow for development, etc.
VIEW_RATE_LIMIT = "1000/1d"  # The rate limit for each view, django-ratelimit, "50 per day per ipaddress)
VIEW_RATE_LIMIT_BLOCK = (
    True  # Given that someone goes over, are they blocked for the period?
)

# On any admin or plugin login redirect to standard social-auth entry point for agreement to terms
LOGIN_REDIRECT_URL = "/login"
LOGIN_URL = "/login"

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

## PLUGINS #####################################################################

# Apply any plugin settings
for plugin in PLUGINS_ENABLED:

    plugin_module = "spakmon.plugins." + plugin
    plugin = import_module(plugin_module)

    # Add the plugin to INSTALLED APPS
    INSTALLED_APPS.append(plugin_module)

    # Add AUTHENTICATION_BACKENDS if defined, for authentication plugins
    if hasattr(plugin, "AUTHENTICATION_BACKENDS"):
        AUTHENTICATION_BACKENDS = (
            AUTHENTICATION_BACKENDS + plugin.AUTHENTICATION_BACKENDS
        )

    # Add custom context processors, if defines for plugin
    if hasattr(plugin, "CONTEXT_PROCESSORS"):
        for context_processor in plugin.CONTEXT_PROCESSORS:
            TEMPLATES[0]["OPTIONS"]["context_processors"].append(context_processor)
