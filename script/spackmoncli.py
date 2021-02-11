__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

# This class can be imported into examples cripts to easily interact
# with a Spack Monitor interface. You can customize this for your use case,
# or perhaps eventually we will integrate this into spack

import base64
import requests
import sys
import logging
import os

logger = logging.getLogger(__name__)


class SpackMonitorClient:
    def __init__(self, host=None, prefix="ms1", token=None):
        self.host = host or "http://127.0.0.1"
        self.baseurl = "%s/%s" % (self.host, prefix.strip("/"))
        self.headers = {}
        self.token = os.environ.get("SPACKMON_TOKEN", token)
        self.session = requests.Session()

    def set_header(self, name, value):
        self.headers.update({name: value})

    def set_basic_auth(self, username, password):
        """A wrapper to adding basic authentication to the Request"""
        auth_str = "%s:%s" % (username, password)
        auth_header = base64.b64encode(auth_str.encode("utf-8"))
        self.set_header("Authorization", "Basic %s" % auth_header.decode("utf-8"))

    def do_request(
        self, endpoint, method="GET", authenticate=True, data=None, headers=None
    ):
        """Do a request. This is a wrapper around requests."""
        headers = self.headers.update(headers or {})
        url = "%s/%s" % (self.baseurl, endpoint)
        if authenticate and "Authorization" not in self.headers:
            sys.exit(
                "This endpoint requires a token. Please set"
                "client.set_basic_auth(username, password) first."
            )

        # Make the request and return to calling function
        return self.session.request(method, url, data=data, headers=headers)

    # Functions correspond to endpoints
    def service_info(self):
        """get the service information endpoint"""
        # Base endpoint provides service info
        response = self.do_request("", authenticate=False)
        return response.json()

    def upload_specfile(self, filename):
        """Given a spec file (must be json) upload to the UploadSpec endpoint"""
        pass
