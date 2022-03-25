# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings
from django.shortcuts import get_object_or_404

from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response

from spackmon.apps.main.tasks import add_errors

from ..auth import is_authenticated

import json


class NewErrors(APIView):
    """
    Provide a new set of errors (and optional metadata) for spack monitor.
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
        """POST /ms1/errors/new/ to submit new errors, separate from spack"""
        print("POST /ms1/errors/new/")

        # If allow_continue False, return response
        allow_continue, response, user = is_authenticated(request)
        if not allow_continue:
            return response

        # Extra data here includes output, phase_name, and status
        data = json.loads(request.body)
        if not isinstance(data, list):
            return Response(
                status=400, data={"message": "Errors should be provided as a list."}
            )

        # Update the phase
        data = add_errors(data)
        return Response(status=data["code"], data=data)
