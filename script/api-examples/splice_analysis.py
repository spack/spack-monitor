__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

# This is an example for doing a splicing (preliminary) analysis to make
# a prediction about whether a package will build or not. This means:
# 1. Starting with a package of interest
# 2. Getting all specs for that package
# 3. For each spec, finding all the dependencies with install file and symbolator results
# 4. Doing a diff between the working symbol space and the anticipated symbol space
# 5. Making a prediction based on not having new missing symbols!

## IMPORTANT: this is server itensive, and likely won't work when there are
# a large number of specs. Instead, the result files should be downloaded
# and parsed locally (an example will follow)

import os
import sys
import json

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(here))

from spackmoncli import SpackMonitorClient

# defaults to host=http:127.0.0.1 and prefix=ms1
client = SpackMonitorClient()

# Here is a package of interest! Let's get a spec for it.
specs = client.get_specs_by_name("curl")

# Keep a list of predictions
predictions = []

# We will loop through specs, but stop after we find one with analyzer results
for spec in specs:

    # Now for the spec we need to get a listing of analyzer results!
    # We can do a splice analysis for any spec that has symbolator-json
    results = client.get_analyzer_results_spec(spec["id"], "symbolator")

    # Here is what a results list looks like!
    # [{'filename': 'bin/curl', 'id': 2160, 'analyzer': 'symbolator', 'name': 'symbolator-json'}, ... ]
    if results:
        for result in results:

            # We are only interested in splicig for binaries (e.g., stuff in bin)
            if not result["filename"].startswith("bin"):
                continue

            # Get dependency specs
            contender_specs = client.get_splice_contenders(result["id"])
            for contender in contender_specs:

                print(
                    "Performing splicing for %s with %s %s %s"
                    % (
                        result["filename"],
                        contender["name"],
                        contender["version"],
                        contender["full_hash"],
                    )
                )
                predictions.append(
                    client.get_splice_predictions(result["id"], contender["id"])
                )
    if predictions:
        break

print("inspect predictions:")
import IPython

IPython.embed()

# Do we have a results directory?
results_dir = os.path.join(here, "results")
if not os.path.exists(results_dir):
    os.mkdir(results_dir)

# Optionally save results to file
with open(os.path.join(results_dir, "splice_analysis_results.json"), "w") as fd:
    fd.write(json.dumps(predictions, indent=4))
