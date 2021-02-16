# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.http import HttpResponseForbidden
from django.views.decorators.cache import never_cache

from spackmon.settings import cfg
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from ..auth import get_user, generate_jwt, get_server


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
        auth_server = cfg.AUTH_SERVER or "%s/auth/token" % DOMAIN_NAME

        # Generate the token data, a dict with token, expires_in, and issued_at
        data = generate_jwt(
            username=user.username,
            scope=scope,
            realm=auth_server,
        )
        return Response(status=200, data=data)
