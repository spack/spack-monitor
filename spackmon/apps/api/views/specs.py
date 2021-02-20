# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings

from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.apps.main.tasks import import_configuration, update_spec_metadata
from rest_framework.response import Response
from rest_framework.views import APIView

from ..auth import is_authenticated

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
        """POST /ms1/specs/new/ to upload a specs file"""

        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)
        if not allow_continue:
            return response

        # Generate the config
        data = json.loads(request.body)
        spack_version = data.get("spack_version")

        # The spack version is required
        if not spack_version:
            return Response(
                status=400, data={"message": "A spack_version string is required"}
            )

        # We require the spack version and the spec
        result = import_configuration(data.get("spec"), spack_version)
        data = {"message": result["message"]}

        # Created or already existed
        if result["spec"]:

            # Full data includes message, id and serialized list of package ids
            data["data"] = result["spec"].to_dict_ids()

            # Tell the user that it was created, and didn't exist
            if result["created"]:
                return Response(status=201, data=data)

            # 200 is success, but already exists
            return Response(status=200, data=data)

        # 400 Bad request, there was an error parsing the data
        return Response(status=400, data=data)


class UpdateSpecMetadata(APIView):
    """Given a finished spec install, receive content from the metadata
    folder. Any metadata that is missing will expect a None response. Fields
    that we expect to parse include:

     - errors: goes into the spec.errors field
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
        spack_version = data.get("spack_version")

        # The spack version is required
        if not spack_version:
            return Response(
                status=400, data={"message": "A spack_version string is required"}
            )

        # Look up the spec based on the full hash and spack version
        spec = get_object_or_404(
            Spec, full_hash=data.get("full_hash"), spack_version=spack_version
        )

        # Update the output, error, install files, config, and environment
        spec = update_spec_metadata(spec, data)
        return Response(status=200, data={"full_hash": spec.full_hash})
