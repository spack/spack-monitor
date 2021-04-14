# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="dashboard"),
    path("builds/<int:bid>/", views.build_detail, name="build_detail"),
    path("specs/diff/<int:spec1>/<int:spec2>/", views.spec_diff, name="spec-diff"),
    path("specs/diff/", views.spec_diff, name="spec-diff"),
    path("specs/detail/<int:specid>", views.spec_detail, name="spec_detail"),
]

app_name = "main"
