# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings

from ratelimit.decorators import ratelimit
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.apps.main.models import Spec
from spackmon.apps.main.tasks import update_package_metadata
from rest_framework.response import Response
from rest_framework.views import APIView

from ..auth import is_authenticated

import json

from spackmon.apps.main.tasks import update_package_metadata
