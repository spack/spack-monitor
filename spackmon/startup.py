# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django_river_ml.client import DjangoClient
from river import feature_extraction, cluster
import os
import logging

logger = logging.getLogger(__name__)


def ensure_model(model_name, model_type, model_file, force=False):
    """
    This is the "init" function for ensuring that a model exists.
    """
    client = DjangoClient()
    if model_name not in client.models() or force is True:
        logger.info(f"{model_name} not yet added, adding!")

        if model_file and os.path.exists(model_file):
            logger.info(f"Found {model_file} to load.")
            model = client.load_model(model_file)
            client.add_model(model, model_type, name=model_name)
        else:
            logger.warning(f"Cannot find {model_file} to load")
