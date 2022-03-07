# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings
from django.shortcuts import get_object_or_404

from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.apps.main.models import Attribute
from rest_framework.response import Response
from rest_framework.views import APIView


class DownloadAttribute(APIView):
    """Download an attribute and it's value."""

    permission_classes = []
    allowed_methods = ("GET",)

    @never_cache
    @method_decorator(
        ratelimit(
            key="ip",
            rate=settings.VIEW_RATE_LIMIT,
            method="GET",
            block=settings.VIEW_RATE_LIMIT_BLOCK,
        )
    )
    def get(self, request, *args, **kwargs):
        """GET /ms1/attributes/<id>/download/"""
        attr_id = kwargs.get("attr_id")
        if not attr_id:
            return Response(
                status=400, data={"message": "An attribute id is required."}
            )
        attribute = get_object_or_404(Attribute, id=attr_id)

        # Return different responses depending on data
        if attribute.json_value:
            return Response(status=200, data=attribute.json_value)
        if attribute.value:
            return Response(status=200, data=attribute.value)
        if attribute.binary_value:
            return Response(status=200, data=attribute.binary_value)
        return Response(
            status=404,
            data={"message": "This attribute does not have an associated value."},
        )
