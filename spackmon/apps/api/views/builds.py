# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings

from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.apps.main.tasks import (
    update_build_status,
    update_build_phase,
    new_build,
    update_build_metadata,
)
from spackmon.apps.main.utils import BUILD_STATUS
from rest_framework.response import Response
from rest_framework.views import APIView

from ..auth import is_authenticated

import json

BUILD_STATUSES = [x[0] for x in BUILD_STATUS]


def get_build_environment(data):
    """Given a request, get the build environment. Return None if we are missing
    something. Since we require a spec to always get a Build, for now it makes
    sense to also include the full_hash and spack_version. If in the future
    we just need a build environment, this can be removed.
    """
    build_environment = {}
    # Ensure we have required fields
    for field in [
        "host_os",
        "platform",
        "host_target",
        "hostname",
        "kernel_version",
        "spack_version",
        "full_hash",
    ]:
        value = data.get(field)
        if not value:
            return
        build_environment[field] = data.get(field)
    return build_environment


class UpdateBuildStatus(APIView):
    """Given a spec, update the status of the BuildTask."""

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
        """POST /ms1/builds/update/ to update one or more tasks"""

        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)
        if not allow_continue:
            return response

        # Get the task id and status to cancel
        data = json.loads(request.body)
        status = data.get("status")

        # Build environment should be provided alongside tasks
        build_environment = get_build_environment(data)
        if not build_environment or not status:
            return Response(
                status=400, data={"message": "Missing required build environment data."}
            )

        # All statuses must be valid
        if status not in BUILD_STATUSES:
            return Response(
                status=400,
                data={
                    "message": "Invalid status. Choices are %s"
                    % ",".join(BUILD_STATUSES)
                },
            )

        result = update_build_status(status, **build_environment)
        return Response(status=200, data=result)


class NewBuild(APIView):
    """Given a spec and environment information, create a new Build."""

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
        """POST /ms1/builds/new/ to start a new build"""

        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)
        if not allow_continue:
            return response

        # Get the complete build environment
        data = json.loads(request.body)
        build_environment = get_build_environment(data)
        if not build_environment:
            return Response(
                status=400, data={"message": "Missing required build environment data."}
            )

        # Create the new build
        result = new_build(**build_environment)

        return Response(status=200, data=result)


class UpdatePhaseStatus(APIView):
    """Given a phase for a spec, update the BuildPhase."""

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
        """POST /ms1/phases/metadata/ to update one or more tasks"""

        print("POST /ms1/builds/phases/update/")

        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)
        if not allow_continue:
            return response

        # Extra data here includes output, phase_name, and status
        data = json.loads(request.body)
        build_environment = get_build_environment(data)
        if not build_environment:
            return Response(
                status=400, data={"message": "Missing required build environment data."}
            )

        output = data.get("output")
        phase_name = data.get("phase_name")
        status = data.get("status")

        # All of the above are required!
        if not phase_name or status:
            return Response(
                status=400,
                data={"message": "phase_name, and status are required."},
            )

        # Update the phase
        success, data = update_build_phase(
            phase_name, status, output, **build_environment
        )
        if not success:
            return Response(status=400, data=data)
        return Response(status=200, data=data)


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
        metadata = data.get("metadata", {})

        # Includes spack version and full_hash
        build_environment = get_build_environment(data)
        if not build_environment or not metadata:
            return Response(
                status=400,
                data={"message": "Missing required build environment or metadata."},
            )

        build = update_build_metadata(metadata, **build_environment)
        return Response(status=200, data={"build_id": build.id})
