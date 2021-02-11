__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

from django.conf import settings

from ratelimit.mixins import RatelimitMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache

from spackmon.settings import cfg
from spackmon.version import __version__
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import check_user_authentication

from .auth import get_user, generate_jwt

import re


import json


class ServiceInfo(RatelimitMixin, APIView):
    """Return a 200 response to indicate a running service, along with
    metadata about the service. This is similar to https://ga4gh.github.io/,
    but not for a workflow so only a subset of fields.
    """

    ratelimit_key = "ip"
    ratelimit_rate = settings.VIEW_RATE_LIMIT
    ratelimit_block = settings.VIEW_RATE_LIMIT_BLOCK
    ratelimit_method = "GET"
    renderer_classes = (JSONRenderer,)

    def get(self, request):
        print("GET /ms1/")

        data = {
            "id": "spackmon",
            "status": "running",  # Extra field looked for by Snakemake
            "name": "Spack Monitor (Spackmon)",
            "description": "This service provides a database to monitor spack builds.",
            "organization": {"name": "spack", "url": "https://github.com/spack"},
            "contactUrl": cfg.HELP_CONTACT_URL,
            "documentationUrl": "https://spack-monitor.readthedocs.io",
            # This is when the function was written, should be when server created
            "createdAt": "2021-02-10T10:40:19Z",
            "updatedAt": cfg.UPDATED_AT,
            "environment": cfg.ENVIRONMENT,
            "version": __version__,
            # TODO: We will provide this for the user to authenticate
            "auth_instructions_url": "",
        }

        # Must make model json serializable
        return Response(status=200, data=data)


@authentication_classes([])
@permission_classes([])
class GetAuthToken(APIView):
    """Given a GET request for a token, validate and return it."""

    permission_classes = []
    allowed_methods = ("GET",)

    @never_cache
    def get(self, request, *args, **kwargs):
        """GET /auth/token"""
        print("GET /auth/token")
        user = get_user(request)

        # No token provided matching a user, no go
        if not user:
            return HttpResponseForbidden()

        # Formalate the jwt token response, with a unique id
        _ = request.GET.get("service")
        scope = request.GET.get("scope", "build").split(",")

        # Generate domain name for auth server
        DOMAIN_NAME = get_server(request)
        auth_server = cfg.AUTH_SERVER or "%s/auth/token" % cfg.DOMAIN_NAME

        # Generate the token data, a dict with token, expires_in, and issued_at
        data = generate_jwt(
            username=user.username,
            scope=scope,
            realm=auth_server,
        )
        return Response(status=200, data=data)
