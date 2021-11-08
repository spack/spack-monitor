# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from symbolator.asp import PyclingoDriver, ABIGlobalSolverSetup
from symbolator.facts import get_facts
from symbolator.corpus import JsonCorpusLoader
import os


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


def run_symbols_splice(resultA, resultB):
    """
    Given two results, each a corpora with json values, perform a splice
    """
    result = {
        "missing": [],
        "selected": [],
        "A": resultA.install_file.build.spec.pretty_print(),
        "B": resultB.install_file.build.spec.pretty_print(),
        "A_id": resultA.install_file.build.spec.id,
        "B_id": resultB.install_file.build.spec.id,
    }

    if not resultA.json_value or not resultB.json_value:
        result[
            "message"
        ] = "One of the results does not have corpora, so the splice cannot be performed."
        return result

    # Spliced libraries will be added as corpora here
    loader = JsonCorpusLoader()
    loader.load(resultA.json_value)
    corpora = loader.get_lookup()
    print("Corpora without Splice %s" % corpora)

    # original set of symbols without splice
    corpora_result = run_symbol_solver(list(corpora.values()))

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
        for x in corpora_result.answers.get("missing_symbols", [])
    ]
    spliced_missing = [
        "%s %s" % (os.path.basename(x[0]).split(".")[0], x[1])
        for x in spliced_result.answers.get("missing_symbols", [])
    ]

    # these are new missing symbols after the splice
    missing = [x for x in spliced_missing if x not in result_missing]
    result["missing"] = missing
    result["selected"] = selected
    return result
