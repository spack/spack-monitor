# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.conf.urls import url, include
from django.urls import path

from spackmon.settings import cfg
import spackmon.apps.api.views as api_views
import rest_framework.authtoken.views as authviews
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from spackmon.apps.api.views.serializers import (
    AttributeViewSet,
    ArchitectureViewSet,
    BuildViewSet,
    BuildEnvironmentViewSet,
    BuildErrorViewSet,
    BuildWarningViewSet,
    BuildPhaseViewSet,
    CompilerViewSet,
    DependencyViewSet,
    EnvironmentVariableViewSet,
    InstallFileViewSet,
    FeatureViewSet,
    TargetViewSet,
    SpecViewSet,
)

router = routers.DefaultRouter()
router.register(r"^attributes", AttributeViewSet, basename="attribute")
router.register(r"^architectures", ArchitectureViewSet, basename="architecture")
router.register(r"^builds", BuildViewSet, basename="build")
router.register(
    r"^buildenvironments", BuildEnvironmentViewSet, basename="buildenvironment"
)
router.register(r"^builderrors", BuildErrorViewSet, basename="builderror")
router.register(r"^buildwarnings", BuildWarningViewSet, basename="buildwarning")
router.register(r"^buildphases", BuildPhaseViewSet, basename="buildphase")
router.register(r"^compilers", CompilerViewSet, basename="compiler")
router.register(r"^dependencies", DependencyViewSet, basename="dependency")
router.register(
    r"^environmentvariable", EnvironmentVariableViewSet, basename="environmentvariable"
)
router.register(r"^installfiles", InstallFileViewSet, basename="installfile")
router.register(r"^features", FeatureViewSet, basename="feature")
router.register(r"^targets", TargetViewSet, basename="target")
router.register(r"^specs", SpecViewSet, basename="spec")

schema_view = get_swagger_view(title="Spack Monitor API")

server_views = [
    url(r"^api/docs/", schema_view, name="docs"),
    path(
        "tables/build/",
        api_views.BuildsTable.as_view(),
        name="builds_table",
    ),
]

urlpatterns = [
    url(r"^api/", include(router.urls)),
    url(r"^", include((server_views, "api"), namespace="internal_apis")),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    url(r"^api-token-auth/", authviews.obtain_auth_token),
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
    # Get all specs based on a package name
    path(
        "%s/specs/name/<str:name>/" % cfg.URL_API_PREFIX,
        api_views.SpecByName.as_view(),
        name="spec_by_name",
    ),
    # Parse through specs -> builds -> install files and return attributes
    # Optionally an analyzer can be provided to filter
    # If the requester wants data for an attribute, it must be requested by id.
    path(
        "%s/specs/<int:spec_id>/attributes/<str:analyzer>/" % cfg.URL_API_PREFIX,
        api_views.SpecAttributes.as_view(),
        name="spec_attributes",
    ),
    path(
        "%s/specs/<int:spec_id>/attributes/" % cfg.URL_API_PREFIX,
        api_views.SpecAttributes.as_view(),
        name="spec_attributes",
    ),
    # Given an analysis result id, return splice contenders (dependency specs)
    path(
        "%s/attributes/<int:attr_id>/splice/contenders/" % cfg.URL_API_PREFIX,
        api_views.AttributeSpliceContenders.as_view(),
        name="attribute_splice_contenders",
    ),
    # Given an analysis result id and spec id, predict splices
    path(
        "%s/analysis/splices/attribute/<int:attr_id>/spec/<int:spec_id>/"
        % cfg.URL_API_PREFIX,
        api_views.AttributeSplicePredictions.as_view(),
        name="predict_attribute_splices",
    ),
    # Download an attribute file
    path(
        "%s/attributes/<int:attr_id>/download/" % cfg.URL_API_PREFIX,
        api_views.DownloadAttribute.as_view(),
        name="download_attribute",
    ),
    # Get a list of splice contenders for a spec (and download links)
    path(
        "%s/specs/<int:spec_id>/splices/contenders/" % cfg.URL_API_PREFIX,
        api_views.SpecSpliceContenders.as_view(),
        name="spec_splice_contenders",
    ),
]


app_name = "api"
