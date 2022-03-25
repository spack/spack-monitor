# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spackmon.settings import cfg as settings

if not settings.DISABLE_ONLINE_ML:
    from django_river_ml.client import DjangoClient

from scipy.spatial.distance import pdist, squareform
from sklearn import manifold

import os
import re
import logging
import pandas

logger = logging.getLogger(__name__)


def get_centers(model):
    """
    Helper function to derive centroids from a model
    """
    if hasattr(model, "steps"):
        for step_name, step in model.steps.items():
            if hasattr(step, "centers") and step.centers:
                return step.centers
    elif hasattr(model, "centers") and model.centers:
        return model.centers


def get_center(model, number):
    """
    Helper function to derive centroids from a model
    """
    centers = get_centers(model)
    if centers and number < len(centers):
        return centers[number]


def generate_embeddings(centers):
    df = pandas.DataFrame(centers)

    # 200 rows (centers) and N columns (words)
    df = df.transpose()
    df = df.fillna(0)

    # Create a distance matrix
    distance = pandas.DataFrame(
        squareform(pdist(df)), index=list(df.index), columns=list(df.index)
    )

    # Make the tsne (output embeddings go into docs for visual)
    fit = manifold.TSNE(n_components=2)
    embedding = fit.fit_transform(distance)
    emb = pandas.DataFrame(embedding, index=distance.index, columns=["x", "y"])
    emb.index.name = "name"

    # cluster ids
    emb["name"] = emb.index
    return emb.to_dict(orient="records")


def predict(text):
    """
    Given a new error, predict where it belongs.
    """
    text = process_text(text)
    if not text:
        return
    client = DjangoClient()
    return client.predict(model_name=settings.MODEL_NAME, features=text)


def learn(text, **kwargs):
    """
    Given a new text entry, preprocess it and give to the model to learn.
    """
    text = process_text(text)
    if not text:
        return
    client = DjangoClient()

    # Extra kwargs go to learn
    client.learn(model_name=settings.MODEL_NAME, features=text, **kwargs)


def process_text(text):
    """
    Process text, including:
    1. Lowercase
    2. Remove numbers and punctuation
    3. Strip whitespace

    We don't do stemming or stop word removal since most error messages
    are already structured and it's not free text.
    """
    # Split based on error
    if not text or "error:" not in text:
        return

    text = text.split("error:", 1)[-1]

    # Make lowercase
    text = text.lower()

    # Remove numbers and punctuation (but leave path separator for now)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^\w\s\/]", "", text)

    # Strip whitespace
    text = text.strip()
    words = [word.strip() for word in text.split(" ")]
    return " ".join(words)
