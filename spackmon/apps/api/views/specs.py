# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.settings import cfg
from spackmon.apps.main.models import Spec, Attribute, Build
from spackmon.apps.main.tasks import import_configuration
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SpecSerializer
from ..auth import is_authenticated

import json


class SpecByName(APIView):
    """Get a list of specs based on a package name."""

    permission_classes = []
    allowed_methods = ("GET",)

    @never_cache
    @method_decorator(
        ratelimit(
            key="ip",
            rate=settings.VIEW_RATE_LIMIT,
            method="GET",
            block=settings.VIEW_RATE_LIMIT_BLOCK,
        )
    )
    def get(self, request, *args, **kwargs):
        """GET /ms1/specs/name/<name>/"""

        name = kwargs.get("name")
        if not name:
            return Response(status=400, data={"message": "A package name is required."})
        specs = [
            SpecSerializer(x).data for x in Spec.objects.filter(name=name).distinct()
        ]
        return Response(status=200, data=specs)


class SpecAttributes(APIView):
    """Get a list of attribute (install analyses) for a spec."""

    permission_classes = []
    allowed_methods = ("GET",)

    @never_cache
    @method_decorator(
        ratelimit(
            key="ip",
            rate=settings.VIEW_RATE_LIMIT,
            method="GET",
            block=settings.VIEW_RATE_LIMIT_BLOCK,
        )
    )
    def get(self, request, *args, **kwargs):
        """GET /ms1/specs/<spec_id>/attributes/"""
        spec_id = kwargs.get("spec_id")
        if not spec_id:
            return Response(status=400, data={"message": "A spec id is required."})

        # Can optionally provide an analyzer
        analyzer = kwargs.get("analyzer")
        results = []

        if analyzer:
            attributes = Attribute.objects.filter(
                install_file__build__spec__id=spec_id, analyzer=analyzer
            )
        else:
            attributes = Attribute.objects.filter(install_file__build__spec__id=spec_id)

        for attribute in attributes.all():
            results.append(
                {
                    "filename": attribute.install_file.name,
                    "id": attribute.id,
                    "analyzer": attribute.analyzer,
                    "name": attribute.name,
                }
            )
        return Response(status=200, data=results)


class SpecSpliceContenders(APIView):
    """Return a list of contenders (analyzer results) for a spec for splicing."""

    permission_classes = []
    allowed_methods = ("GET",)

    @never_cache
    @method_decorator(
        ratelimit(
            key="ip",
            rate=settings.VIEW_RATE_LIMIT,
            method="GET",
            block=settings.VIEW_RATE_LIMIT_BLOCK,
        )
    )
    def get(self, request, *args, **kwargs):
        """GET /ms1/specs/<int:spec_id>/splices/contenders/"""
        spec_id = kwargs.get("spec_id")
        if not spec_id:
            return Response(
                status=400,
                data={"message": "A spec id is required to get splice contenders for."},
            )
        spec = get_object_or_404(Spec, id=spec_id)

        # Realistically we will just have one build for the hash
        build = spec.build_set.first()

        if not build:
            return Response(
                status=400, data={"message": "We don't have any builds for that spec."}
            )

        # Find specs first via other builds
        builds = Build.objects.filter(
            spec__name=spec.name,
            spec__compiler__name=spec.compiler.name,
            build_environment__host_os=build.build_environment.host_os,
            build_environment__host_target=build.build_environment.host_target,
            build_environment__platform=build.build_environment.platform,
        ).values_list("spec", flat=True)

        # What other versions can be spliced (aside from the original)?
        contenders = list(
            Attribute.objects.filter(
                name="symbolator-json",
                install_file__build__id__in=builds,
            ).values("id", "analyzer", "name", filename=F("install_file__name"))
        )
        return Response(status=200, data=contenders)


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

        # Created or already existed
        if result["data"].get("spec"):

            # Full data includes message, id and serialized list of package ids
            result["data"]["spec"] = result["data"]["spec"].to_dict_ids()

        return Response(status=result["code"], data=result)
