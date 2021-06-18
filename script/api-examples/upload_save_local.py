#!/usr/bin/env python

# upload_save_local is an example of taking a directory created by spack
# with spack install --monitor --monitor-save-local singularity
# and uploading to a spack monitor server. This is a use case where you might
# have results generated where you don't have internet access or otherwise
# don't want to or cannot interact with spack monitor. This is an API endpoint
# so you are still required to have authentication.
# meaning you should export your username and token
#
# export SPACKMON_TOKEN=xxxxxxxxxxxxxxxxxx
# export SPACKMON_USER=thebestdude

import base64
import os
import json
import requests
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(here))

from spackmoncli import SpackMonitorClient

# If the user doesn't provide a directory to upload, ask for it
if len(sys.argv) < 1:
    sys.exit(
        "Please provide the path to ~/.spack/reports/monitor/<date>/ as the only argument."
    )

# Spec file and spack version as args
dirname = os.path.abspath(sys.argv[1])

if not os.path.exists(dirname):
    sys.exit("%s does not exist." % dirname)

# The spackmoncli doesn't enforce this since auth can be disabled, so we do here
token = os.environ.get("SPACKMON_TOKEN")
username = os.environ.get("SPACKMON_USER")

if not username or not token:
    sys.exit("You are required to export your SPACKMON_TOKEN and SPACKMON_USER")

# defaults to host=http:127.0.0.1 and prefix=ms1
client = SpackMonitorClient()
client.upload_local_save(dirname)
