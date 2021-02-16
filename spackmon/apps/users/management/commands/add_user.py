# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.core.management.base import BaseCommand, CommandError

from spackmon.apps.users.models import User
from getpass import getpass


class Command(BaseCommand):
    """get a token (required to enter your password) for the API."""

    def add_arguments(self, parser):
        parser.add_argument("username", nargs=1, type=str)

    help = "Generates a user (e.g., for the API) for spackmon."

    def handle(self, *args, **options):
        if not options["username"]:
            raise CommandError("Please provide a username as the first argument.")

        print("Username: %s" % options["username"][0])
        username = options["username"][0]

        # The username cannot exist
        usercount = User.objects.filter(username=username).count()
        if usercount > 0:
            raise CommandError("This username already exists.")

        password = getpass("Enter Password:")
        user = User.objects.create_user(username, password=password)
        # user by default is not staff or superuser, but will have api token
        user.save()
        print("User %s successfully created." % user.username)
