# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.db.models import Value
from django.db.models.functions import Concat
from django.shortcuts import render
from spackmon.apps.main.models import Spec, Attribute
from symbolator.smeagle.model import SmeagleRunner, Model
import os

from ratelimit.decorators import ratelimit
from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
)

import difflib


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
            specA = A.install_file.build.spec.pretty_print().replace(" ", "-")

            # Do comparison based on basename (e.g. libz.1.so == libz.1.2.11.so)
            prefixA = os.path.basename(A.install_file.name).split(".")[0]
            for B in results.all():
                prefixB = os.path.basename(B.install_file.name).split(".")[0]
                specB = B.install_file.build.spec.pretty_print().replace(" ", "-")

                # Try to match files, and don't compare perfectly equal objects
                if not prefixB.startswith(prefixA) or A == B:
                    continue

                modelB = Model(B.install_file.name, B.json_value)
                runner.records = {
                    specA + "-" + A.install_file.name: modelA,
                    specB + "-" + B.install_file.name: modelB,
                }
                try:
                    res = runner.stability_test(return_result=True)

                    # Currently we can only see missing imports
                    comps.append(
                        {
                            "missing_imports": set(
                                [x[0] for x in res.answers.get("missing_imports", [])]
                            ),
                            "A": A.install_file.name,
                            "B": B.install_file.name,
                            "specA": A.install_file.build.spec,
                            "specB": B.install_file.build.spec,
                        }
                    )
                except:
                    print("Skipping %s and %s" % (A, B))
                    pass

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
