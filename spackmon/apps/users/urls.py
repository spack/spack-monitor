# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf.urls import url, include
from spackmon.apps.users import views
from social_django import urls as social_urls

urlpatterns = [
    url(r"^login/$", views.login, name="login"),
    url(r"^accounts/login/$", views.login),
    url(r"^logout/$", views.logout, name="logout"),
    url("", include(social_urls, namespace="social")),
]

app_name = "users"
