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
    # The build can already exist (e.g., if being re-run)
    path(
        "%s/builds/new/" % cfg.URL_API_PREFIX,
        api_views.NewBuild.as_view(),
        name="new_build",
    ),
    path(
        "%s/builds/update/" % cfg.URL_API_PREFIX,
        api_views.UpdateBuildStatus.as_view(),
        name="update_build_status",
    ),
    path(
        "%s/builds/phases/update/" % cfg.URL_API_PREFIX,
        api_views.UpdatePhaseStatus.as_view(),
        name="update_phase_status",
    ),
    # Analyze to add metadata to builds
    path(
        "%s/analyze/builds/" % cfg.URL_API_PREFIX,
        api_views.UpdateBuildMetadata.as_view(),
        name="update_build_metadata",
    ),
]

app_name = "api"
