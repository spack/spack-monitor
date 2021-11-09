__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

# This is an example for doing a splicing (preliminary) analysis LOCALLY to make
# a prediction about whether a package will build or not. This means:
# 1. Starting with a package of interest
# 2. Getting all specs for that package
# 3. For each spec, finding all the dependencies with install file and symbolator results
# 4. Doing a diff between the working symbol space and the anticipated symbol space
# 5. Making a prediction based on not having new missing symbols!

# Unlike splice_analysis.py, this uses API endpoints to download data locally
# first, and then do analysis from that.

from symbolator.asp import PyclingoDriver, ABIGlobalSolverSetup
from symbolator.facts import get_facts
from symbolator.corpus import JsonCorpusLoader
import os


import os
import sys
import json
import logging
import time

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(here))

from spackmoncli import SpackMonitorClient

# Default save to spack analysis folder
logger = logging.getLogger("splice-analysis")

results_dir = os.path.expanduser("~/.spack/spack-monitor/analysis")
logger.info("Results will be written to %s" % results_dir)

# defaults to host=http:127.0.0.1 and prefix=ms1
client = SpackMonitorClient(host="https://builds.spack.io")


def read_json(filename):
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content


def write_json(content, filename):
    with open(filename, "w") as fd:
        fd.write(json.dumps(content, indent=4))


def download_result(result_dir, result):
    """
    A shared function to download a result and return the content. If the
    result is already downloaded, just read and return the content.
    A return of "None" indicates there is no result.
    """
    # We will return the loaded content, None indicates no result
    content = None

    # The result directory "the thing we are splicing"
    result_dir = os.path.join(result_dir, os.path.dirname(result["filename"]))
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    # If we haven't written the file yet
    result_file = "%s/%s.json" % (result_dir, os.path.basename(result["filename"]))
    if not os.path.exists(result_file):
        try:
            content = client.download_analyzer_result(result["id"])
        except:
            return content
        if not content:
            return content
        with open(result_file, "w") as fd:
            fd.write(json.dumps(content, indent=4))
    else:
        content = read_json(result_file)
    return content


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


def get_spec_id(spec):
    """Get a quasi identifier for the spec, with the name, version, hash, spackmon id"""
    return "%s@%s/%s:%s" % (
        spec["name"],
        spec["version"],
        spec["full_hash"],
        spec["id"],
    )


def run_symbols_splice(A, B):
    """
    Given two results, each a corpora with json values, perform a splice
    """
    result = {
        "missing": [],
        "selected": [],
    }

    # Spliced libraries will be added as corpora here
    loader = JsonCorpusLoader()
    loader.load(A)
    corpora = loader.get_lookup()

    # original set of symbols without splice
    corpora_result = run_symbol_solver(list(corpora.values()))

    # Now load the splices separately, and select what we need
    splice_loader = JsonCorpusLoader()
    splice_loader.load(B)
    splices = splice_loader.get_lookup()

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


def main():
    """Note that this is optimized for continuing to run, so we catch/continue"""
    # This can be an argument
    pkg = "curl"

    # Here is a package of interest! Let's get a spec for it.
    specs = client.get_specs_by_name(pkg)

    # Let's write a results file to analyzer folder
    result_file = os.path.join(results_dir, pkg, "symbolator-predictions.json")

    # If the results file exists, load the results we have!
    results = {}
    if os.path.exists(result_file):
        results = read_json(result_file)

    # We will loop through specs, and download analysis results we want to look at further
    for spec in specs:
        spec_id = get_spec_id(spec)

        # Don't parse something twice
        if spec_id in results:
            continue

        print("Preparing to parse %s" % spec_id)
        try:
            new_results = run_analysis(spec)
            if new_results:
                results[spec_id] = new_results
                write_json(results, result_file)
        except:
            logger.error("ERROR: Issue parsing %s" % spec_id)
            time.sleep(600)


def run_analysis(spec):

    # An easy way to identify it, if needed later
    spec_id = get_spec_id(spec)

    # Make a directory for the spec
    spec_dir = os.path.join(
        results_dir, spec["name"], spec["version"], spec["full_hash"]
    )
    if not os.path.exists(spec_dir):
        os.makedirs(spec_dir)

    # Now for the spec we need to get a listing of analyzer results!
    # We can do a splice analysis for any spec that has symbolator-json
    results = client.get_analyzer_results_spec(spec["id"], "symbolator")
    print(
        "Found %s analysis results for %s@%s/%s"
        % (len(results), spec["name"], spec["version"], spec["full_hash"])
    )

    predictions = []

    # Here is what a results list looks like!
    # [{'filename': 'bin/curl', 'id': 2160, 'analyzer': 'symbolator', 'name': 'symbolator-json'}, ... ]
    if results:
        for result in results:

            # We are only interested in splicig for binaries (e.g., stuff in bin)
            if not result["filename"].startswith("bin"):
                continue

            content = download_result(spec_dir, result)
            if not content:
                continue

            # Get dependency specs
            try:
                contender_specs = client.get_splice_contenders(result["id"])
            except:
                logger.error(
                    "ERROR: cannot get splice contenders for %s" % result["id"]
                )
                continue

            if not contender_specs:
                continue

            print(
                "Found %s dependency specs for %s"
                % (len(contender_specs), result["filename"])
            )
            for contender in contender_specs:

                # Although we technically can, we don't want to splice a different version library into itself
                if contender["name"] == spec["name"]:
                    continue

                # Contender splices is a list of libs of different versions that can be spliced
                try:
                    contender_splices = client.get_spec_analyzer_results(
                        contender["id"]
                    )
                except:
                    logger.error(
                        "ERROR: issue retrieving analysis results %s" % contender["id"]
                    )
                    continue

                if not contender_splices:
                    continue

                contender_id = get_spec_id(contender)
                print(
                    "Found %s contender splices for %s."
                    % (len(contender_splices), contender_id)
                )

                # Now that we know there are splices, create a spec directory for the contender
                contender_dir = os.path.join(
                    results_dir,
                    contender["name"],
                    contender["version"],
                    contender["full_hash"],
                )
                if not os.path.exists(contender_dir):
                    os.makedirs(contender_dir)

                # NOTE: this assumes that we bring in the spliced libs dependencies too
                # We may not want to do this (update run_symbol_splice function)
                for splice in contender_splices:

                    # A contender splice MUST be a lib
                    if not splice["filename"].startswith("lib"):
                        continue

                    spliced = download_result(contender_dir, splice)
                    if spliced:
                        sym_result = run_symbols_splice(content, spliced)
                        if sym_result:
                            will_splice = True if not sym_result["missing"] else False
                            predict = {
                                "missing": sym_result["missing"],
                                "B_insert": splice["filename"],
                                "A_binary": result["filename"],
                                "prediction": will_splice,
                                "A_id": result["id"],
                                "B_id": splice["id"],
                                "specA_id": contender["id"],
                                "specB_id": spec["id"],
                                "specA": spec_id,
                                "specB": contender_id,
                            }
                            print(predict)
                            predictions.append(predict)

    # TODO we can do a cleanup here, but then more server pinging baaad
    return predictions


if __name__ == "__main__":
    main()
