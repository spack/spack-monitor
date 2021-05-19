# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf import settings
from django.urls import reverse
from django.db.models import Count, Case, When, IntegerField, Q

from ratelimit.mixins import RatelimitMixin

from spackmon.settings import cfg
from spackmon.version import __version__
from spackmon.apps.main.models import Build
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


def filter_buildphase_set(queryset, order_by, status):
    """Given a queryset, order by a particular status and sort."""
    prefix = ""
    if "desc" in order_by:
        prefix = "-"
    queryset = queryset.annotate(
        count_buildphase=Count(
            Case(
                When(buildphase__status=status, then=1),
                output_field=IntegerField(),
            )
        )
    ).order_by("%scount_buildphase" % prefix)
    return queryset


def filter_buildfield(queryset, order_by, field):
    """Given a queryset, order by a particular field and sort."""
    prefix = ""
    if "desc" in order_by:
        prefix = "-"
    return queryset.annotate(count_custom=Count(field)).order_by(
        "%scount_custom" % prefix
    )


class BuildsTable(RatelimitMixin, APIView):
    """server side render main index table"""

    ratelimit_key = "ip"
    ratelimit_rate = settings.VIEW_RATE_LIMIT
    ratelimit_block = settings.VIEW_RATE_LIMIT_BLOCK
    ratelimit_method = "GET"
    renderer_classes = (JSONRenderer,)

    def get(self, request, year=None):
        print("GET BuildsTable")

        # Start and length to return
        start = int(request.GET["start"])
        length = int(request.GET["length"])
        draw = int(request.GET["draw"])
        query = request.GET.get("search[value]", "")
        queryset = Build.objects.all()

        # First do the search to reduce the size of the set
        if query:
            queryset = queryset.filter(
                Q(spec__name__icontains=query)
                | Q(spec__version__icontains=query)
                | Q(spec__compiler__name__icontains=query)
                | Q(spec__compiler__version__icontains=query)
                | Q(spec__full_hash__icontains=query)
                | Q(build_environment__platform__icontains=query)
                | Q(build_environment__host_os__icontains=query)
                | Q(build_environment__host_target__icontains=query)
                | Q(status__icontains=query)
                | Q(tags__name__icontains=query)
                | Q(modify_date__icontains=query)
            )

        # Order column and direction
        order = request.GET["order[0][column]"]
        direction = request.GET["order[0][dir]"]  # asc or desc
        order_lookup = {
            "0asc": "spec__name",
            "0desc": "-spec__name",
            "1asc": "build_environment__platform",
            "1desc": "-build_environment__platform",
            "2asc": "spec__compiler__name",
            "2desc": "-spec__compiler__name",
            "3asc": "status",
            "3desc": "-status",
            "6asc": "tags__name",
            "6desc": "-tags__name",
            "7asc": "modify_date",
            "7desc": "-modify_date",
        }

        # Empty datatable
        data = {"draw": draw, "recordsTotal": 0, "recordsFiltered": 0, "data": []}
        taglist = []
        count = 0

        order_by = "%s%s" % (order, direction)
        if order_by in order_lookup:
            print(f"Ordering by {order_by}")
            queryset = queryset.order_by(order_lookup[order_by])
            count = queryset.count()

        # Custom orderings
        elif order_by.startswith("4"):
            queryset = filter_buildphase_set(queryset, order_by, "SUCCESS")
            count = queryset.count()

        elif order_by.startswith("5"):
            queryset = filter_buildphase_set(queryset, order_by, "ERROR")
            count = queryset.count()

        if start > count:
            start = 0
        end = start + length - 1

        # If we've gone too far
        if end > count:
            end = count - 1

        queryset = queryset[start : end + 1]
        data["recordsTotal"] = count
        data["recordsFiltered"] = count

        for build in queryset:

            tags = ""
            for tag in build.tags.all():
                tags += (
                    (
                        '<a style="color:white" href="%s"><span class="badge badge-info">'
                        % reverse("main:builds_by_tag", args=[tag.name])
                    )
                    + tag.name
                    + "</span></a>"
                )

            data["data"].append(
                [
                    '<a href="%s">%s</a><a href="%s"><span style="float:right" class="badge badge-primary">build details</span></a>'
                    % (
                        reverse("main:spec_detail", args=[build.spec.id]),
                        build.spec.pretty_print(),
                        reverse("main:build_detail", args=[build.id]),
                    ),
                    '<div style="float: left; margin: 0px 4px;">%s</div>'
                    % build.build_environment.arch,
                    '<div style="float: left; margin: 0px 4px;">%s</div>'
                    % build.spec.compiler,
                    build.status,
                    build.phase_success_count,
                    build.phase_error_count,
                    tags,
                    build.modify_date,
                ]
            )
        return Response(status=200, data=data)
