# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.views.generic.base import TemplateView
from django.urls import path
from django.conf.urls import url

from . import views

urlpatterns = [
    path("_ah/warmup/", views.warmup, name="warmup"),
    url(
        r"^robots\.txt/$",
        TemplateView.as_view(
            template_name="base/robots.txt", content_type="text/plain"
        ),
    ),
]

app_name = "base"
