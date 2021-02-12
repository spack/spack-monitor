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


class UploadConfig(APIView):
    """Given a loaded config file as data, add to database if the user has
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
        """POST /v2/configs/upload to upload a configuration file"""

        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)

        if not allow_continue:
            return response

        # Generate the config
        config = import_configuration(json.loads(request.body))

        # Tell the user that it was created
        if config:
            return Response(status=201)

        # 409 conflict means that it already exists
        return Response(status=409)
