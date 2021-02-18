# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings

from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.apps.main.tasks import update_task_status
from spackmon.apps.main.utils import BUILD_STATUS
from rest_framework.response import Response
from rest_framework.views import APIView

from ..auth import is_authenticated

import json

BUILD_STATUSES = [x[0] for x in BUILD_STATUS]


class UpdateTaskStatus(APIView):
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
        """POST /ms1/tasks/update/ to update one or more tasks"""

        print("IN POST")
        # If allow_continue False, return response
        allow_continue, response, _ = is_authenticated(request)
        if not allow_continue:
            print("NOT ALLOWED")
            return response

        # Get the task id and status to cancel
        tasks = json.loads(request.body)

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
            update_task_status(full_hash, status)

        return Response(status=200, data=tasks)
