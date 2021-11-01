# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="dashboard"),
    path("builds/<int:bid>/", views.build_detail, name="build_detail"),
    path("builds/tag/<str:tag>/", views.builds_by_tag, name="builds_by_tag"),
    path("builds/owner/<str:username>/", views.builds_by_owner, name="builds_by_owner"),
    path("specs/diff/<int:spec1>/<int:spec2>/", views.spec_diff, name="spec-diff"),
    path("specs/diff/", views.spec_diff, name="spec-diff"),
    # General analysis results / matrices
    path("analysis/matrix/<str:pkg>/", views.package_matrix, name="package-matrix"),
    path("analysis/matrix/", views.package_matrix, name="package-matrix"),
    path(
        "analysis/diffs/<str:pkg>/<str:analysis>/",
        views.view_analysis_diffs,
        name="package-analysis-diffs",
    ),
    path("analysis/diffs/", views.view_analysis_diffs, name="package-analysis-diffs"),
    path(
        "analysis/results/<str:pkg>/<str:analysis>/",
        views.view_analysis_results,
        name="package-analysis-results",
    ),
    path(
        "analysis/results/",
        views.view_analysis_results,
        name="package-analysis-results",
    ),
    # Smeagle diffs / symbols
    path(
        "analysis/abi/stability/<str:pkg>/",
        views.stability_test_package,
        name="stability-test-package",
    ),
    path(
        "analysis/abi/stability/",
        views.stability_test_package,
        name="stability-test-package",
    ),
    path("specs/detail/<int:specid>", views.spec_detail, name="spec_detail"),
]

app_name = "main"
