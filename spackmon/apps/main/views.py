# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from spackmon.apps.main.models import Spec, Build
import os

from ratelimit.decorators import ratelimit
from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
)


# Dashboard


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def index(request):
    builds = Build.objects.all()
    return render(request, "main/index.html", {"builds": builds})


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def build_detail(request, bid):
    build = get_object_or_404(Build, pk=bid)
    return render(request, "builds/detail.html", {"build": build})
