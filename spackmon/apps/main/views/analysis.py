# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.http import JsonResponse
from django.db.models import Value, F
from django.db.models.functions import Concat
from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from spackmon.apps.main.models import Spec, Build
import spackmon.apps.main.online_ml as online_ml
from itertools import chain
import pandas

from ratelimit.decorators import ratelimit
from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
)


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
@never_cache
def view_clusters(request):
    """
    View machine learning clusters for our model!
    """
    data = online_ml.get_centers()
    return render(request, "online_ml/clusters.html", {"data": data})


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
@never_cache
def get_cluster_center(request):
    """
    View machine learning clusters for our model!
    """
    number = int(request.GET.get("center", 99))
    data = online_ml.get_center(number)
    return JsonResponse(data)


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def package_matrix(request, pkg=None, arch=None):
    """
    Generate a build matrix for one or more specs.
    """
    # Unique package names and os options
    packages = (
        Spec.objects.exclude(build=None).values_list("name", flat=True).distinct()
    )
    failed_packages = (
        Spec.objects.filter(build_hash="FAILED_CONCRETIZATION")
        .exclude(name__in=packages)
        .values_list("name", flat=True)
        .distinct()
    )
    packages = chain(packages, failed_packages)

    # arch options
    arches = (
        Spec.objects.exclude(arch__platform_os=None)
        .values_list("arch__platform_os", flat=True)
        .distinct()
    )
    compilers = (
        Spec.objects.exclude(compiler=None)
        .values_list("compiler__name", flat=True)
        .distinct()
    )

    specs = None
    rows = []
    versions = None

    if pkg and arch:

        # Annotate with compiler name and version - if failed concrete, we cannot know
        failed_concrete = (
            Spec.objects.filter(name=pkg, build_hash="FAILED_CONCRETIZATION")
            .order_by("version")
            .annotate(
                compiler_name=Concat("compiler__name", Value(" "), "compiler__version"),
                build_status=Value("FAILED_CONCRETIZATION"),
            )
        )

        # If we don't have any builds!
        if Build.objects.filter(spec__name=pkg).count() + failed_concrete.count() == 0:
            messages.info(
                request,
                "Spack monitor doesn't have build data for %s and %s" % (pkg, arch),
            )

        specs = (
            Spec.objects.filter(name=pkg, arch__platform_os=arch)
            .exclude(build__status=None)
            .order_by("version")
            .annotate(
                compiler_name=Concat("compiler__name", Value(" "), "compiler__version"),
                build_status=F("build__status"),
            )
        ).distinct()

        # Unique compilers and versions
        versions = specs.values_list("version", flat=True).distinct()
        failed_versions = (
            failed_concrete.exclude(version__in=versions)
            .values_list("version", flat=True)
            .distinct()
        )
        versions = list(set(chain(versions, failed_versions)))

        # distinct doesn't seem to work here
        compilers = specs.values_list("compiler_name", flat=True).distinct()
        failed_compilers = (
            failed_concrete.exclude(compiler_name__in=compilers)
            .values_list("compiler_name", flat=True)
            .distinct()
        )
        compilers = list(set(chain(compilers, failed_compilers)))

        # Ensure we are sorted!
        versions.sort()
        compilers.sort()

        # Convert to a data frame to do summary stats (yes this is actually faster)
        df = pandas.DataFrame(list(specs.values()))
        df = df.append(pandas.DataFrame(list(failed_concrete.values())))

        # Assemble results by compiler and host os
        rows = []
        for version in versions:
            row = []
            version_df = df[df["version"] == version]
            for compiler in compilers:

                # Do a count of specs that use that version and compiler
                filtered = version_df[version_df["compiler_name"] == compiler]

                # We don't have that compiler /version combo, it's "we don't know"
                if filtered.shape[0] == 0:
                    row.append({"specs": {}, "value": 0, "status": "UNKNOWN"})
                else:
                    total = filtered.shape[0]
                    success = len(filtered[filtered["build_status"] == "SUCCESS"])
                    cancelled = len(filtered[filtered["build_status"] == "CANCELLED"])
                    failed = len(filtered[filtered["build_status"] == "FAILED"])
                    notrun = len(filtered[filtered["build_status"] == "NOTRUN"])
                    failed_concrete = len(
                        filtered[filtered["build_hash"] == "FAILED_CONCRETIZATION"]
                    )
                    row.append(
                        {
                            "specs": list(filtered.id.unique()),
                            "version": version,
                            "compiler": compiler,
                            "status": "RUN",
                            "value": success / total,
                            "cancelled": cancelled,
                            "failed": failed,
                            "failed_concrete": failed_concrete,
                            "notrun": notrun,
                            "success": success,
                            "total": total,
                        }
                    )
            rows.append(row)

    return render(
        request,
        "matrix/package.html",
        {
            "packages": packages,
            "package": pkg,
            "specs": specs,
            "rows": rows,
            "numrows": len(rows),
            "arches": arches,
            "arch": arch,
            "rowLabels": versions,
            "colLabels": compilers,
        },
    )
