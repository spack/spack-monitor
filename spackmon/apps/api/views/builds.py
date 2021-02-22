# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings

from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.apps.main.tasks import update_task_status, update_phase
from spackmon.apps.main.utils import BUILD_STATUS
from rest_framework.response import Response
from rest_framework.views import APIView

from ..auth import is_authenticated

import json

BUILD_STATUSES = [x[0] for x in BUILD_STATUS]


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
        tasks = data.get("tasks", {})
        spack_version = data.get("spack_version")

        # The spack version is required
        if not spack_version:
            return Response(
                status=400, data={"message": "A spack_version string is required"}
            )

        # All statuses must be valid
        statuses = list(tasks.values())
        if any([x for x in statuses if x not in BUILD_STATUSES]):
            return Response(
                status=400,
                data={
                    "message": "Invalid status. Choices are %s"
                    % ",".join(BUILD_STATUSES)
                },
            )

        # Update each task
        for full_hash, status in tasks.items():
            update_task_status(full_hash, status, spack_version)

        return Response(status=200, data=tasks)


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

        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)
        if not allow_continue:
            return response

        # Get the task id and status to cancel
        data = json.loads(request.body)
        full_hash = data.get("full_hash")
        output = data.get("output")
        phase_name = data.get("phase_name")
        status = data.get("status")
        spack_version = data.get("spack_version")

        # The spack version is required
        if not spack_version:
            return Response(
                status=400, data={"message": "A spack_version string is required"}
            )

        # All of the above are required!
        if not full_hash or not phase_name or not status:
            return Response(
                status=400,
                data={"message": "full_hash, phase_name, and status are required."},
            )

        # Update the phase
        success, data = update_phase(full_hash, spack_version, output, status)
        if not success:
            return Response(status=400, data=data)
        return Response(status=200, data=data)
