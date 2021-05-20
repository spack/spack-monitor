# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.http import HttpResponse
from django.shortcuts import render

# Warmup requests for app engine


def handler404(request, exception):
    response = render(request, "base/404.html", {})
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, "base/500.html", {})
    response.status_code = 500
    return response


def warmup():
    return HttpResponse(status=200)
