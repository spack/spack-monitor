# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spackmon.apps.users.models import User
from ratelimit.decorators import ratelimit

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from rest_framework.authtoken.models import Token

from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
)


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
@login_required
def view_token(request):
    """
    View a token for interacting with the Spack Monitor API
    """
    return render(request, "users/token.html")


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
@login_required
def update_token(request):
    """a user is allowed to change/update their current token"""
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
    except Token.DoesNotExist:
        pass

    token = Token.objects.create(user=request.user)
    token.save()

    return render(request, "users/token.html")


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def view_profile(request, username=None):
    """
    View a user's profile.
    """
    message = "You must select a user or be logged in to view a profile."
    if not username:
        if not request.user:
            messages.info(request, message)
            return redirect("/")
        user = request.user
    else:
        user = get_object_or_404(User, username=username)

    # TODO need to add build links here, and a view to see user builds
    context = {"profile": user}
    return render(request, "users/profile.html", context)


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
@login_required
def delete_account(request):
    """Delete a user's account"""
    if not request.user or request.user.is_anonymous:
        messages.info(request, "This action is not prohibited.")
        return redirect("/")

    # Log the user out
    logout(request)
    request.user.is_active = False
    messages.info(request, "Thank you for using Singularity Registry Server!")
    return redirect("/")
