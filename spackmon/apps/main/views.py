# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from spackmon.apps.main.models import Spec, Build
from spackmon.apps.main.logparser import parse_build_logs
import os

from ratelimit.decorators import ratelimit
from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
)

import difflib
import json

# Dashboard


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def index(request):
    builds = Build.objects.all()
    tags = builds.values_list("tags__name", flat=True).distinct()
    return render(request, "main/index.html", {"builds": builds, "tags": tags})


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def builds_by_tag(request, tag):
    builds = Build.objects.filter(tags__name=tag)

    # Present all tags for browsing
    tags = Build.objects.all().values_list("tags__name", flat=True).distinct()
    return render(
        request, "main/index.html", {"builds": builds, "tag": tag, "tags": tags}
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def build_detail(request, bid):
    build = get_object_or_404(Build, pk=bid)

    # Generate BuildWarnings and BuildErrors if don't exist
    if build.logs_parsed == 0:
        parse_build_logs(build)
    return render(request, "builds/detail.html", {"build": build})


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def spec_diff(request, spec1=None, spec2=None):
    """Allow the user to select two specs to diff."""
    specs = Spec.objects.all().order_by("name")
    if not spec1 or not spec2:
        return render(request, "specs/diff.html", {"specs": specs})

    spec1 = get_object_or_404(Spec, pk=spec1)
    spec2 = get_object_or_404(Spec, pk=spec2)
    diff1 = json.dumps(spec1.to_dict(), indent=4).split("\n")
    diff2 = json.dumps(spec2.to_dict(), indent=4).split("\n")
    diff = difflib.HtmlDiff().make_table(diff1, diff2)
    return render(
        request,
        "specs/diff.html",
        {"specs": specs, "diff": diff, "spec1": spec1, "spec2": spec2},
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def spec_detail(request, specid):
    """Show detail for a spec."""
    spec = get_object_or_404(Spec, pk=specid)
    return render(
        request,
        "specs/detail.html",
        {"spec": spec},
    )
