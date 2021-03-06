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
    import_configuration,
)
from spackmon.apps.main.utils import BUILD_STATUS
from spackmon.apps.main.models import Build
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
            print(field)
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
        build_id = data.get("build_id")

        # Build environment should be provided alongside tasks
        if not build_id:
            return Response(status=400, data={"message": "Missing required build id."})

        # All statuses must be valid
        if status not in BUILD_STATUSES:
            return Response(
                status=400,
                data={
                    "message": "Invalid status. Choices are %s"
                    % ",".join(BUILD_STATUSES)
                },
            )

        build = get_object_or_404(Build, pk=build_id)
        result = update_build_status(build, status)
        return Response(status=result["code"], data=result)


class NewBuild(APIView):
    """Given a spec and environment information, create a new Build.
    If the build already exists, we return the build_id with it.
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
        result = get_build(**build_environment)

        # If a spec is included in the build, the requester is okay to create
        # it given that it does not exist.
        if "spec" in data and "spack_version" in data:
            spack_version = data.get("spack_version")
            result = import_configuration(data["spec"], data["spack_version"])
            result = get_build(**build_environment)

        # Prepare data with
        return Response(status=result["code"], data=result)


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
        build_id = data.get("build_id")
        if not build_id:
            return Response(status=400, data={"message": "Missing required build_id."})

        output = data.get("output")
        phase_name = data.get("phase_name")
        status = data.get("status")

        # All of the above are required!
        if not phase_name or not status:
            return Response(
                status=400,
                data={"message": "phase_name, and status are required."},
            )

        build = get_object_or_404(Build, pk=build_id)

        # Update the phase
        data = update_build_phase(build, phase_name, status, output)
        return Response(status=data["code"], data=data)
