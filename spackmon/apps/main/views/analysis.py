# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.db.models import Value, F
from django.db.models.functions import Concat
from django.contrib import messages
from django.shortcuts import render
from spackmon.apps.main.models import Spec, Attribute, Build
from symbolator.smeagle.model import SmeagleRunner, Model
from symbolator.corpus import JsonCorpusLoader
from symbolator.asp import PyclingoDriver, ABIGlobalSolverSetup
from symbolator.facts import get_facts
from itertools import chain
import os
import pandas

from ratelimit.decorators import ratelimit
from spackmon.settings import (
    VIEW_RATE_LIMIT as rl_rate,
    VIEW_RATE_LIMIT_BLOCK as rl_block,
)

import difflib


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def stability_test_package(request, pkg=None, specA=None, specB=None):
    """This is the Smeagle stability test (although not complete)"""

    # Filter down to those we have analyzer results for
    packages = Spec.objects.values_list("name", flat=True).distinct()
    versions = None
    comps = []

    # If we have a package and no specs, the user needs to select
    if pkg and not specA or not specB:
        versions = Spec.objects.filter(
            name=pkg, build__installfile__attribute__name="smeagle-json"
        ).distinct()
        if not versions:
            messages.info(
                request, "We don't have any ABI analysis results for that package."
            )

    elif pkg and specA and specB:
        versions = Spec.objects.filter(
            name=pkg, build__installfile__attribute__name="smeagle-json"
        ).distinct()
        specs = Spec.objects.filter(id__in=[specA, specB])
        specA = specs[0]
        specB = specs[1]
        results = Attribute.objects.filter(
            name="smeagle-json", install_file__build__spec__in=specs
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
        {
            "package": pkg,
            "packages": packages,
            "package": pkg,
            "comps": comps,
            "versions": versions,
            "A": specA,
            "B": specB,
        },
    )


def get_splice_contenders(pkg=None, names=None):
    if names:
        return (
            Spec.objects.filter(
                name__in=names, build__installfile__attribute__name="symbolator-json"
            )
            .exclude(build__installfile__attribute__json_value=None)
            .distinct()
        )
    return (
        Spec.objects.filter(
            name=pkg, build__installfile__attribute__name="symbolator-json"
        )
        .exclude(build__installfile__attribute__json_value=None)
        .distinct()
    )


def run_symbol_solver(corpora):
    """
    A helper function to run the symbol solver.
    """
    driver = PyclingoDriver()
    setup = ABIGlobalSolverSetup()
    return driver.solve(
        setup,
        corpora,
        dump=False,
        logic_programs=get_facts("missing_symbols.lp"),
        facts_only=False,
        # Loading from json already includes system libs
        system_libs=False,
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def symbol_test_package(request, pkg=None, specA=None, specB=None):
    """This is looking at symbols undefined for some package, and (optionally) a splice."""
    # Filter down to those we have analyzer results for
    packages = (
        Spec.objects.filter(build__installfile__attribute__name="symbolator-json")
        .values_list("name", flat=True)
        .distinct()
    )
    splicesA = None
    splicesB = None
    selected = None
    missing = []

    # Keep track of original IDs
    specA_id = specA
    specB_id = specB

    # If we have a package but no selected splices
    if pkg and not specA and not specB:

        # SpecA will be spliced INTO
        splicesA = get_splice_contenders(pkg)
        if not splicesA:
            messages.info(
                request, "We don't have any symbol analysis results for that package."
            )

    elif pkg and specA and not specB:

        # SpecB can be any dependency package of A
        splicesA = get_splice_contenders(pkg)
        specA = Spec.objects.filter(id=specA)
        if not specA:
            messages.info(request, "We cannot find that spec.")
        else:
            names = specA.values_list("dependencies__spec__name", flat=True)
            splicesB = get_splice_contenders(names=names)

    elif pkg and specA and specB:
        splicesA = get_splice_contenders(pkg=pkg)
        names = splicesA.values_list("dependencies__spec__name", flat=True)
        splicesB = get_splice_contenders(names=names)

        # Retrieve the specs chosen by ID (if empty, we will fail getting results)
        specA = Spec.objects.filter(id=specA).first()
        specB = Spec.objects.filter(id=specB).first()

        # We have to assume one analyzer result per spec chosen
        resultA = (
            Attribute.objects.filter(
                name="symbolator-json", install_file__build__spec=specA
            )
            .exclude(json_value=None)
            .first()
        )
        resultB = (
            Attribute.objects.filter(
                name="symbolator-json", install_file__build__spec=specB
            )
            .exclude(json_value=None)
            .first()
        )

        if not resultA and not resultB:
            messages.info(
                request,
                "Cannot find analysis result for either spec selection, choose others",
            )
        elif not resultA:
            messages.info(
                request,
                "Cannot find analysis result for spec %s" % specA.pretty_print(),
            )
        elif not resultB:
            messages.info(
                request,
                "Cannot find analysis result for spec %s" % specB.pretty_print(),
            )
        else:

            # Spliced libraries will be added as corpora here
            loader = JsonCorpusLoader()
            loader.load(resultA.json_value)
            corpora = loader.get_lookup()
            print("Corpora without Splice %s" % corpora)

            # original set of symbols without splice
            result = run_symbol_solver(list(corpora.values()))

            # Now load the splices separately, and select what we need
            splice_loader = JsonCorpusLoader()
            splice_loader.load(resultB.json_value)
            splices = splice_loader.get_lookup()
            print("Splices %s" % splices)

            # If we have the library in corpora, delete it, add spliced libraries
            # E.g., libz.so.1.2.8 is just "libz" and will be replaced by anything with the same prefix
            corpora_lookup = {key.split(".")[0]: corp for key, corp in corpora.items()}
            splices_lookup = {key.split(".")[0]: corp for key, corp in splices.items()}

            # Keep a lookup of libraries names
            corpora_libnames = {key.split(".")[0]: key for key, _ in corpora.items()}
            splices_libnames = {key.split(".")[0]: key for key, _ in splices.items()}

            # Splices selected
            selected = []

            # Here we match based on the top level name, and add splices that match
            # (this assumes that if a lib is part of a splice corpus set but not included, we don't add it)
            for lib, corp in splices_lookup.items():

                # ONLY splice in those known
                if lib in corpora_lookup:

                    # Library A was spliced in place of Library B
                    selected.append([splices_libnames[lib], corpora_libnames[lib]])
                    corpora_lookup[lib] = corp

            spliced_result = run_symbol_solver(list(corpora_lookup.values()))
            print("After splicing %s" % corpora_lookup)

            # Compare sets of missing symbols
            result_missing = [
                "%s %s" % (os.path.basename(x[0]).split(".")[0], x[1])
                for x in result.answers.get("missing_symbols", [])
            ]
            spliced_missing = [
                "%s %s" % (os.path.basename(x[0]).split(".")[0], x[1])
                for x in spliced_result.answers.get("missing_symbols", [])
            ]
            # these are new missing symbols after the splice
            missing = [x for x in spliced_missing if x not in result_missing]

    return render(
        request,
        "analysis/symbols.html",
        {
            "package": pkg,
            "packages": packages,
            "splicesA": splicesA,
            "splicesB": splicesB,
            "selected": selected,
            "A": specA,
            "B": specB,
            "specA": specA_id,
            "specB": specB_id,
            "missing": missing,
        },
    )


@ratelimit(key="ip", rate=rl_rate, block=rl_block)
def view_analysis_results(request, pkg=None, analysis=None):
    """
    General view to show results (json, values) for some analyzer and a spec
    """
    results = None
    specs = Spec.objects.exclude(build__installfile__attribute=None).distinct()
    analyses = Attribute.objects.values_list("name", flat=True).distinct()
    if pkg and analysis:
        pkg = Spec.objects.filter(id=pkg)
        if not pkg:
            messages.info(request, "We cannot find a package spec with that id.")
        else:
            results = Attribute.objects.filter(
                name=analysis, install_file__build__spec_id__in=pkg
            ).exclude(json_value=None)

    return render(
        request,
        "analysis/results.html",
        {
            "package": pkg,
            "results": results,
            "specs": specs,
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
    specs = None
    rows = None
    versions = None
    compilers = None

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

        if arch == "all":
            specs = (
                Spec.objects.filter(name=pkg)
                .exclude(build__status=None)
                .order_by("version")
                .annotate(
                    compiler_name=Concat(
                        "compiler__name", Value(" "), "compiler__version"
                    ),
                    build_status=F("build__status"),
                )
            )
        else:
            specs = (
                Spec.objects.filter(name=pkg, arch__platform_os=arch)
                .exclude(build__status=None)
                .order_by("version")
                .annotate(
                    compiler_name=Concat(
                        "compiler__name", Value(" "), "compiler__version"
                    ),
                    build_status=F("build__status"),
                )
            )

        # Unique compilers and versions
        versions = specs.values_list("version", flat=True).distinct()
        failed_versions = (
            failed_concrete.exclude(version__in=versions)
            .values_list("version", flat=True)
            .distinct()
        )
        versions = list(chain(versions, failed_versions))

        # distinct doesn't seem to work here
        compilers = specs.values_list("compiler_name", flat=True).distinct()
        failed_compilers = (
            failed_concrete.exclude(compiler_name__in=compilers)
            .values_list("compiler_name", flat=True)
            .distinct()
        )
        compilers = list(chain(compilers, failed_compilers))

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
            "arches": arches,
            "arch": arch,
            "rowLabels": versions,
            "colLabels": compilers,
        },
    )
