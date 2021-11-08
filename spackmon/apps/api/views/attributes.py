# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings
from django.shortcuts import get_object_or_404

from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from spackmon.apps.main.models import Spec, Attribute
from spackmon.apps.main.analysis.symbols import run_symbols_splice
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import SpecSerializer


class AttributeSpliceContenders(APIView):
    """Get a list of contender libraries to splice for an attribute."""

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
        """GET /ms1/attributes/<id>/splice/contenders/"""
        attr_id = kwargs.get("attr_id")
        if not attr_id:
            return Response(
                status=400, data={"message": "An attribute id is required."}
            )
        attribute = get_object_or_404(Attribute, id=attr_id)

        # What spec is associated with the attribute?
        spec = attribute.install_file.build.spec

        # Return the list of specs that can be spliced...
        dep_ids = (
            Spec.objects.filter(id=spec.id)
            .values_list("dependencies__spec", flat=True)
            .distinct()
        )
        specs = [
            SpecSerializer(x).data
            for x in Spec.objects.filter(id__in=dep_ids).distinct()
        ]
        return Response(status=200, data=specs)


class DownloadAttribute(APIView):
    """Download an attribute and it's value."""

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
        """GET /ms1/attributes/<id>/download/"""
        attr_id = kwargs.get("attr_id")
        if not attr_id:
            return Response(
                status=400, data={"message": "An attribute id is required."}
            )
        attribute = get_object_or_404(Attribute, id=attr_id)

        # Return different responses depending on data
        if attribute.json_value:
            return Response(status=200, data=attribute.json_value)
        if attribute.value:
            return Response(status=200, data=attribute.value)
        if attribute.binary_value:
            return Response(status=200, data=attribute.binary_value)
        return Response(
            status=404,
            data={"message": "This attribute does not have an associated value."},
        )


class AttributeSplicePredictions(APIView):
    """Given a spec id and attribute (analyer result), make predictions for splicing."""

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
        """GET /ms1/analysis/splices/attribute/<int:attr_id>/spec/<int:spec_id>/"""
        attr_id = kwargs.get("attr_id")
        spec_id = kwargs.get("spec_id")
        if not attr_id or not spec_id:
            return Response(
                status=400,
                data={
                    "message": "An attribute id and spec id to splice in are required."
                },
            )
        attribute = get_object_or_404(Attribute, id=attr_id)
        spec = get_object_or_404(Spec, id=spec_id)

        # Keep a list of the splices
        splices = []

        # What other versions can be spliced (aside from the original)?
        contenders = Attribute.objects.filter(
            name="symbolator-json",
            install_file__build__spec__name=spec.name,
        ).exclude(install_file__id=attribute.id)

        for contender in contenders.all():
            splices.append(run_symbols_splice(attribute, contender))

        return Response(status=200, data=splices)
