from __future__ import unicode_literals, absolute_import

import os
import sys

import django
from django.core import management
from django.conf import settings
from django.test.utils import get_runner

from datetime import datetime

here = os.path.dirname(os.path.abspath(__file__))


def run_tests(*test_args):
    if not test_args:
        test_args = ["tests"]

    testing_db = os.path.join(here, "test-db.sqlite")

    # Testing DB
    if os.path.exists(testing_db):
        os.remove(testing_db)

    # Set environment variables
    os.environ["DJANGO_SETTINGS_MODULE"] = "spackmon.settings"
    os.environ["SECRET_KEY"] = "youarethetacomaster"
    os.environ["JWT_SERVER_SECRET"] = "youarethetacomaster"
    os.environ["CREATION_DATE"] = str(datetime.now())

    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    # Prepare databases and server
    management.call_command("makemigrations", "main", verbosity=1)
    management.call_command("makemigrations", "users", verbosity=1)
    management.call_command("makemigrations", "admin", verbosity=1)
    management.call_command("migrate", verbosity=1)

    test_runner.setup_databases()

    failures = test_runner.run_tests(test_args)
    # test_runner.teardown_test_environment()
    sys.exit(bool(failures))


if __name__ == "__main__":
    run_tests(*sys.argv[1:])
