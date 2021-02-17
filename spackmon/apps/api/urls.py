# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf.urls import url
from django.urls import path

from spackmon.settings import cfg
import spackmon.apps.api.views as api_views

urlpatterns = [
    path(
        "auth/token/",
        api_views.GetAuthToken.as_view(),
        name="auth_token",
    ),
    path(
        "%s/" % cfg.URL_API_PREFIX,
        api_views.ServiceInfo.as_view(),
        name="service_info",
    ),
    path(
        "%s/specs/new/" % cfg.URL_API_PREFIX,
        api_views.NewSpec.as_view(),
        name="new_spec",
    ),
    path(
        "%s/tasks/update/" % cfg.URL_API_PREFIX,
        api_views.UpdateTaskStatus.as_view(),
        name="update_task_status",
    ),
]


app_name = "api"
