# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings

from ratelimit.mixins import RatelimitMixin

from spackmon.settings import cfg
from spackmon.version import __version__
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


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
            "status": "running",
            "name": "Spack Monitor (Spackmon)",
            "description": "This service provides a database to monitor spack builds.",
            "organization": {"name": "spack", "url": "https://github.com/spack"},
            "contactUrl": cfg.HELP_CONTACT_URL,
            "documentationUrl": "https://spack-monitor.readthedocs.io",
            "createdAt": settings.SERVER_CREATION_DATE,
            "updatedAt": cfg.UPDATED_AT,
            "environment": cfg.ENVIRONMENT,
            "version": __version__,
            "auth_instructions_url": cfg.AUTH_INSTRUCTIONS,
        }

        # Must make model json serializable
        return Response(status=200, data=data)
