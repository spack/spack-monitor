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


class UpdatePackageMetadata(APIView):
    """Given a finished package install, receive content from the metadata
    folder. Any metadata that is missing will expect a None response. Fields
    that we expect to parse include:

     - output: goes into the spec.output field
     - error: goes into the spec.error field
     - manifest: includes a json object with install files. Install files are
                 linked to a spec and go into the ManyToMany install_files
                 field, which points to the InstallFile table.
     - environ: should be a list of parsed environment variables, which go
                into the spec.envars field, pointing to EnvironmentVariable.
     - config: text of config arguments.
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
        """POST /ms1/packages/metadata/ to add or update a package metadata"""

        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)
        if not allow_continue:
            return response

        # Get the data, including output, error, environ, manifest, config
        data = json.loads(request.body)

        # Look up the spec based on the full hash
        spec = get_object_or_404(Spec, full_hash=data.get("full_hash"))

        # Update the output, error, install files, config, and environment
        spec = update_package_metadata(spec, data)
        return Response(status=200, data={"full_hash": spec.full_hash})
