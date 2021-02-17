# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import json

import logging

logger = logging.getLogger(__name__)

# Valid build statuses

BUILD_STATUS = [
    ("CANCELLED", "CANCELLED"),
    ("SUCCESS", "SUCCESS"),
    ("NOTRUN", "NOTRUN"),
    ("FAILED", "FAILED"),
]


def read_json(filename):
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content
