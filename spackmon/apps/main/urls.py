# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spackmon.settings import cfg
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
    path(
        "analysis/matrix/<str:pkg>/<str:arch>/",
        views.package_matrix,
        name="package-matrix",
    ),
    path("analysis/matrix/", views.package_matrix, name="package-matrix"),
    path("specs/detail/<int:specid>", views.spec_detail, name="spec_detail"),
]

# Add the cluster view if we aren't disabling online and if the model flavor is cluster
if not cfg.DISABLE_ONLINE_ML and cfg.MODEL_FLAVOR == "cluster":
    urlpatterns += [
        path("analysis/clusters/", views.view_clusters, name="view-clusters"),
        path(
            "analysis/clusters/centroids/<name>/",
            views.get_centroids,
            name="get-centroids",
        ),
        path(
            "analysis/cluster/center/<name>/",
            views.get_cluster_center,
            name="get-cluster-center",
        ),
    ]

app_name = "main"
