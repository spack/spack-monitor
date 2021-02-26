# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings
from django.shortcuts import get_object_or_404

from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.apps.main.tasks import (
    update_build_status,
    update_build_phase,
    get_build,
    update_build_metadata,
)
from spackmon.apps.main.utils import BUILD_STATUS
from spackmon.apps.main.models import Build
from rest_framework.response import Response
from rest_framework.views import APIView

from ..auth import is_authenticated

import json


class UpdateBuildMetadata(APIView):
    """Given a finished build for a spec, receive content from the metadata
    folder. Any metadata that is missing will expect a None response. Fields
    that we expect to parse include:

     - errors: goes into the spec.errors field
     - manifest: includes a json object with install files. Install files are
                 linked to a spec and go into the ManyToMany install_files
                 field, which points to the InstallFile table.
     - environ: should be a list of parsed environment variables, which go
                into the spec.envars field, pointing to EnvironmentVariable.
     - config: text of config arguments.

    We don't include output files, as they are included with build phases.
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
        """POST /ms1/builds/metadata/ to add or update a package metadata"""

        print("POST /ms1/builds/metadata/")

        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)
        if not allow_continue:
            return response

        # Get the data, including output, error, environ, manifest, config
        data = json.loads(request.body)
        build_environment = get_build_environment(data)
        if not build_environment:
            return Response(
                status=400, data={"message": "Missing required build environment data."}
            )

        # Get or create a representation of the build
        result = get_build(**build_environment)
        if result["code"] not in [200, 201]:
            return Response(status=result["code"], data=result)

        build_id = result.get("data", {}).get("build", {}).get("id", {})
        if not build_id:
            return Response(status=400, data={"message": "Missing required build_id."})

        metadata = data.get("metadata", {})
        build = get_object_or_404(Build, pk=build_id)
        result = update_build_metadata(build, metadata)
        return Response(status=result["code"], data=result)
