#!/usr/bin/env python

# upload_spec is an example of using the restful API to upload a spec file.
# Since this is an API endpoint, you are required to have authentication.
# meaning you should export your username and token
#
# export SPACKMON_TOKEN=xxxxxxxxxxxxxxxxxx
# export SPACKMON_USER=thebestdude

import os
import json
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(here))

from spackmoncli import SpackMonitorClient

# If the user doesn't provide a spec file, ask for it
if len(sys.argv) < 2:
    sys.exit(
        "Please provide the spec json file to upload and the spack version as arguments."
    )

# Spec file and spack version as args
spec_file = os.path.abspath(sys.argv[1])
spack_version = sys.argv[2]

if not os.path.exists(spec_file):
    sys.exit("%s does not exist." % spec_file)

# The spackmoncli doesn't enforce this since auth can be disabled, so we do here
token = os.environ.get("SPACKMON_TOKEN")
username = os.environ.get("SPACKMON_USER")

if not username or not token:
    sys.exit("You are required to export your SPACKMON_TOKEN and SPACKMON_USER")

# defaults to host=http:127.0.0.1 and prefix=ms1
client = SpackMonitorClient()

response = client.upload_specfile(spec_file, spack_version)
if response.status_code == 200:
    print("This package already exists in the database.")
elif response.status_code == 201:
    print("The package was successfully created.")
print(json.dumps(response.json(), indent=4))
