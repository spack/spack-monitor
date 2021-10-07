# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf.urls import url, include
from spackmon.apps.users import views

urlpatterns = [
    url(r"^login/$", views.login, name="login"),
    url(r"^accounts/login/$", views.login),
    url(r"^logout/$", views.logout, name="logout"),
    url(r"^token$", views.view_token, name="token"),
    url(r"^auth/tokens$", views.view_token, name="tokens"),
    url(r"^token/update$", views.update_token, name="update_token"),
    url(r"^u/profile$", views.view_profile, name="profile"),
    url(r"^u/delete$", views.delete_account, name="delete_account"),  # delete account
    url(r"^u/profile/(?P<username>.+)$", views.view_profile, name="profile"),
    url(r"", include("social_django.urls", namespace="social")),
]

app_name = "users"
