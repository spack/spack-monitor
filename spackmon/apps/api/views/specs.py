__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

from django.conf import settings

from ratelimit.mixins import RatelimitMixin
from ratelimit.decorators import ratelimit
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.settings import cfg
from spackmon.apps.main.tasks import import_configuration
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from ..permissions import check_user_authentication

from ..auth import get_user, generate_jwt, is_authenticated

import re

import json


class UploadSpec(APIView):
    """Given a loaded spec file as data, add to database if the user has
    the correct permissions.
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
        """POST /v2/config/new/ to upload a new spec file"""

        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)
        print(allow_continue)
        print(response)

        if not allow_continue:
            return response

        print(json.loads(request.body))

        # Return response that spec was created (should return an id?)
        return Response(status=201)
