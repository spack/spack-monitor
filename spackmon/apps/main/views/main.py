# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.shortcuts import render, get_object_or_404
from spackmon.apps.main.models import Build
from spackmon.apps.main.logparser import parse_build_logs

from ratelimit.decorators import ratelimit
from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
)


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
def builds_by_owner(request, username):
    builds = Build.objects.filter(owner__username=username)
    tags = builds.values_list("tags__name", flat=True).distinct()
    return render(
        request, "main/index.html", {"builds": builds, "owner": username, "tags": tags}
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def build_detail(request, bid):
    build = get_object_or_404(Build, pk=bid)

    # Generate BuildWarnings and BuildErrors if don't exist
    if build.logs_parsed == 0:
        parse_build_logs(build)
    return render(request, "builds/detail.html", {"build": build})
