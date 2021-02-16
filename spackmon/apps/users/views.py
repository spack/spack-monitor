# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from django.contrib.auth import logout as auth_logout, authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from ratelimit.decorators import ratelimit

from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
    cfg,
)


def logout(request):
    """log the user out, either from the notebook or traditional Django auth"""
    auth_logout(request)

    # A traditional Django authentication is here
    return redirect("/")
