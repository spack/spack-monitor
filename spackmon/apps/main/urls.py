# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="dashboard"),
]

app_name = "main"
