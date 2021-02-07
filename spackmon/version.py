__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "MPL 2.0"

__version__ = "0.0.1"
AUTHOR = "Vanessa Sochat"
AUTHOR_EMAIL = ""
NAME = "spackmon"
PACKAGE_URL = "https://github.com/spack/spack-monitor"
KEYWORDS = "monitoring,package mangagers,spack"
DESCRIPTION = "Spack Monitor"
LICENSE = "LICENSE"

################################################################################
# Global requirements


INSTALL_REQUIRES = (
    ("pyaml", {"min_version": "20.4.0"}),
    ("Jinja2", {"min_version": "2.11.2"}),
    ("Django", {"exact_version": "3.0.8"}),
    ("django-crispy-forms", {"min_version": "1.10.0"}),
    ("django-taggit", {"min_version": "1.3.0"}),
    ("django-gravatar", {"min_version": None}),
    ("django-ratelimit", {"min_version": "3.0.0"}),
    ("django-extensions", {"min_version": "3.0.2"}),
    ("djangorestframework", {"exact_version": "3.11.1"}),
    ("drf-yasg", {"exact_version": "1.20.0"}),
    ("social-auth-app-django", {"min_version": "4.0.0"}),
    ("social-auth-core", {"min_version": "3.3.3"}),
    ("psycopg2-binary", {"min_version": "2.8.5"}),
)

# Dependencies provided by snakemake: pyYaml, jinja2

EMAIL_REQUIRES = (("sendgrid", {"min_version": "6.4.3"}),)

TESTS_REQUIRES = (("pytest", {"min_version": "4.6.2"}),)

ALL_REQUIRES = INSTALL_REQUIRES + EMAIL_REQUIRES
