__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import authenticate
from spackmon.apps.users.models import User
from getpass import getpass


class Command(BaseCommand):
    """add a user (typically to use the API) without any special permissions."""

    def add_arguments(self, parser):
        parser.add_argument("username", nargs=1, default=None, type=str)

    help = "Get a user token to interact with the API"

    def handle(self, *args, **options):
        if not options["username"]:
            raise CommandError("Please provide a username")
        username = options["username"][0]
        print("Username: %s" % username)

        # The username must exist
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError("This username does not exist.")

        # Create the user and ask for password
        password = getpass("Enter Password:")
        user = authenticate(None, username=user.username, password=password)
        if user is not None:
            print(user.token)
        else:
            print("This password is incorrect.")
