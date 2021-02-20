# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.http import HttpResponse

# Warmup requests for app engine


def warmup():
    return HttpResponse(status=200)
