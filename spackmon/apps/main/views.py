# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.db.models import Value
from django.db.models.functions import Concat
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from spackmon.apps.main.models import Spec, Build, Attribute
from spackmon.apps.main.logparser import parse_build_logs
from symbolator.smeagle.model import SmeagleRunner, Model
import os

from ratelimit.decorators import ratelimit
from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
)

import difflib
import json

# Dashboard


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def index(request):
    builds = Build.objects.all()
    tags = builds.values_list("tags__name", flat=True).distinct()
    return render(request, "main/index.html", {"builds": builds, "tags": tags})


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def builds_by_tag(request, tag):
    builds = Build.objects.filter(tags__name=tag)
    # Present all tags for browsing
    tags = Build.objects.all().values_list("tags__name", flat=True).distinct()
    return render(
        request, "main/index.html", {"builds": builds, "tag": tag, "tags": tags}
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def builds_by_owner(request, username):
    builds = Build.objects.filter(owner__username=username)
    tags = builds.values_list("tags__name", flat=True).distinct()
    return render(
        request, "main/index.html", {"builds": builds, "owner": username, "tags": tags}
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def build_detail(request, bid):
    build = get_object_or_404(Build, pk=bid)

    # Generate BuildWarnings and BuildErrors if don't exist
    if build.logs_parsed == 0:
        parse_build_logs(build)
    return render(request, "builds/detail.html", {"build": build})


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def spec_diff(request, spec1=None, spec2=None):
    """
    Allow the user to select two specs to diff.
    """
    specs = Spec.objects.all().order_by("name")
    if not spec1 or not spec2:
        return render(request, "specs/diff.html", {"specs": specs})

    spec1 = get_object_or_404(Spec, pk=spec1)
    spec2 = get_object_or_404(Spec, pk=spec2)
    diff1 = json.dumps(spec1.to_dict(), indent=4).split("\n")
    diff2 = json.dumps(spec2.to_dict(), indent=4).split("\n")
    diff = difflib.HtmlDiff().make_table(diff1, diff2)
    return render(
        request,
        "specs/diff.html",
        {"specs": specs, "diff": diff, "spec1": spec1, "spec2": spec2},
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def spec_detail(request, specid):
    """
    Show detail for a spec.
    """
    spec = get_object_or_404(Spec, pk=specid)
    return render(
        request,
        "specs/detail.html",
        {"spec": spec},
    )


# Analyze


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def stability_test_package(request, pkg=None):

    # Filter down to those we have analyzer results for
    packages = Spec.objects.values_list("name", flat=True).distinct()
    comps = []

    if pkg:
        results = Attribute.objects.filter(
            name="smeagle-json", install_file__build__spec__name=pkg
        ).exclude(json_value=None)
        runner = SmeagleRunner()

        # Run symbolator on all pairs - we will present a list of comparisons
        for A in results.all():
            modelA = Model(A.install_file.name, A.json_value)

            # Do comparison based on basename (e.g. libz.1.so == libz.1.2.11.so)
            prefixA = os.path.basename(A.install_file.name).split(".")[0]
            for B in results.all():
                prefixB = os.path.basename(B.install_file.name).split(".")[0]
                if not prefixB.startswith(prefixA):
                    continue
                modelB = Model(B.install_file.name, B.json_value)
                runner.records = {
                    A.install_file.name: modelA,
                    B.install_file.name: modelB,
                }
                res = runner.stability_test(return_result=True)

                # Currently we can only see missing imports
                comps.append(
                    {
                        "missing_imports": set(
                            [x[0] for x in res.answers["missing_imports"]]
                        ),
                        "A": A.install_file.name,
                        "B": B.install_file.name,
                        "specA": A.install_file.spec,
                        "specB": B.install_file.spec,
                    }
                )

    return render(
        request,
        "smeagle/diffs.html",
        {"package": pkg, "packages": packages, "package": pkg, "comps": comps},
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def view_analysis_results(request, pkg=None, analysis=None):
    """
    General view to show results (json, values) for some analyzer across a package
    """
    results = None
    packages = Spec.objects.values_list("name", flat=True).distinct()
    analyses = Attribute.objects.values_list("name", flat=True).distinct()
    if pkg and analysis:
        results = Attribute.objects.filter(
            name=analysis, install_file__build__spec__name=pkg
        ).exclude(json_value=None)

    return render(
        request,
        "analysis/results.html",
        {
            "package": pkg,
            "results": results,
            "packages": packages,
            "analyses": analyses,
            "analysis": analysis,
        },
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def view_analysis_diffs(request, pkg=None, analysis=None):
    packages = Spec.objects.values_list("name", flat=True).distinct()
    analyses = Attribute.objects.values_list("name", flat=True).distinct()
    diffs = []

    if pkg and analysis:
        results = Attribute.objects.filter(
            name=analysis, install_file__build__spec__name=pkg
        ).exclude(json_value=None)
        for A in results.all():
            prefixA = os.path.basename(A.install_file.name).split(".")[0]
            for B in results.all():
                prefixB = os.path.basename(B.install_file.name).split(".")[0]
                if not prefixB.startswith(prefixA):
                    continue

                value1 = A.to_json().split("\n")
                value2 = B.to_json().split("\n")
                same = False
                if value1 == value2:
                    res = "These two analyses are the same."
                    same = True
                else:
                    res = difflib.HtmlDiff().make_table(value1, value2)
                diffs.append(
                    {
                        "A": A.install_file.name,
                        "B": B.install_file.name,
                        "diff": res,
                        "same": same,
                    }
                )

    return render(
        request,
        "analysis/diffs.html",
        {
            "package": pkg,
            "diffs": diffs,
            "packages": packages,
            "analyses": analyses,
            "analysis": analysis,
        },
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def package_matrix(request, pkg=None):
    """
    Generate a build matrix for one or more specs.
    """
    # Unique package names
    packages = Spec.objects.values_list("name", flat=True).distinct()
    specs = None
    rows = None
    versions = None
    compilers = None

    if pkg:
        # Annotate with compiler name and version
        specs = (
            Spec.objects.filter(name=pkg)
            .order_by("version")
            .annotate(
                compiler_name=Concat("compiler__name", Value(" "), "compiler__version")
            )
        )

        # Unique compilers and versions
        versions = specs.values_list("version", flat=True).distinct()

        # distinct doesn't seem to work here
        compilers = list(set(specs.values_list("compiler_name", flat=True)))

        # Assemble results by compiler (we don't have different arches for now)
        # TODO this won't scale, but should work okay for small datasets
        rows = []
        for version in versions:
            row = []
            for compiler in compilers:
                match = (
                    specs.filter(version=version, compiler_name=compiler)
                    .exclude(build__status=None)
                    .distinct()
                )

                # Appending an empty record means "We don't have that version/compiler"
                if match.count() == 0:
                    row.append({"specs": match, "value": 0, "status": "UNKNOWN"})
                else:
                    # Calculate percentage of matches with success
                    statuses = match.values_list("build__status", flat=True)
                    success = [x for x in statuses if x == "SUCCESS"]
                    row.append(
                        {
                            "spec": match.first(),
                            "status": "RUN",
                            "value": len(success) / len(statuses),
                            "spec_id": match.first().id,
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
            "rowLabels": versions,
            "colLabels": compilers,
        },
    )
