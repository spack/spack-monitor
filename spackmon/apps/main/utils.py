__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

import json

import logging

logger = logging.getLogger(__name__)


def read_json(filename):
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content
