__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2020-2021, Vanessa Sochat"
__license__ = "MPL 2.0"

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from spackmon.main.models import Configuration
import os

from ratelimit.decorators import ratelimit
from spackmon.settings import cfg
from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
)


# Dashboard


@login_required
@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def index(request):
    # All users can see all configurations
    configs = Configuration.objects.all()
    return render(request, "main/index.html", {"configs": configs})
