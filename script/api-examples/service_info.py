__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

# This examples shows how to get (and print) service info for a running
# Spack Monitor server. You should already have started containers,
# and created your username and token (although you don't need it for this
# endpoint)

import os
import sys
import json

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(here))

from spackmoncli import SpackMonitorClient

# defaults to host=http:127.0.0.1 and prefix=ms1
client = SpackMonitorClient()
info = client.service_info()

# Make it pretty to print to the screen
print(json.dumps(info, indent=4))
