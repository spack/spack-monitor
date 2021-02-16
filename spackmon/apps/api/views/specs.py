# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings

from ratelimit.mixins import RatelimitMixin
from ratelimit.decorators import ratelimit
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.apps.main.tasks import import_configuration
from spackmon.settings import cfg
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from ..permissions import check_user_authentication

from ..auth import get_user, generate_jwt, is_authenticated

import re

import json


class NewSpec(APIView):
    """Given a loaded config (spec) file as data, add to database if the user has
    the correct permissions. We return the top level parent package.
    """

    permission_classes = []
    allowed_methods = ("POST",)

    @never_cache
    @method_decorator(
        ratelimit(
            key="ip",
            rate=settings.VIEW_RATE_LIMIT,
            method="POST",
            block=settings.VIEW_RATE_LIMIT_BLOCK,
        )
    )
    def post(self, request, *args, **kwargs):
        """POST /v2/specs/new/ to upload a configuration file"""

        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)
        if not allow_continue:
            return response

        # Generate the config
        result = import_configuration(json.loads(request.body))
        data = {"message": result["message"]}

        # Created or already existed
        if result["spec"]:

            # Full data includes message, id and serialized list of package ids
            data["data"] = result["spec"].to_dict_ids()

            # Tell the user that it was created, and didn't exist
            if result["created"]:
                return Response(status=201, data=data)

            # 409 conflict means that it already exists
            return Response(status=200, data=data)

        # 400 Bad request, there was an error parsing the data
        return Response(status=400, data=data)
