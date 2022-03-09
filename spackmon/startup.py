# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django_river_ml.client import DjangoClient
from river import feature_extraction, cluster


def ensure_model(model_name):
    """
    This is the "init" function for ensuring that a model exists. Ideally we
    will have a pre-populated model to use, but if not, we generate a new one
    here and add to the client
    """
    client = DjangoClient()
    if model_name not in client.models():
        logger.info(f"{model_name} not yet created, creating!")
        model = feature_extraction.BagOfWords() | cluster.KMeans(
            n_clusters=100, halflife=0.4, sigma=3, seed=0
        )
        client.add_model(model, "cluster", name=model_name)
