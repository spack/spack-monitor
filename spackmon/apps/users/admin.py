# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from spackmon.apps.users.models import User

admin.site.register(User, UserAdmin)
