__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from spackmon.apps.users.models import User

admin.site.register(User, UserAdmin)
