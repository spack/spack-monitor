# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from django_river_ml.client import DjangoClient
from spackmon.settings import cfg as settings

from scipy.spatial.distance import pdist, squareform
from sklearn import manifold

import os
import re
import logging
import pandas

logger = logging.getLogger(__name__)


def get_centers():
    """
    Get centroids of the KMeans model to visualize!
    """
    client = DjangoClient()
    model = client.get_model(settings.MODEL_NAME)

    # Get the centers!
    centers = model.steps["KMeans"].centers

    # UIDS as id for each row, vectors across columns
    values = list(centers.values())
    df = pandas.DataFrame(centers)

    # 100 rows (centers) and N columns (words)
    # This might have issues with scaling if the vocabulary gets too big
    # (hopefully it does not)
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
    emb["name"] = emb.index
    return emb.to_dict(orient="records")


def get_center(number):
    """
    Given a centroid number, get the centroid values
    """
    client = DjangoClient()
    model = client.get_model(settings.MODEL_NAME)

    # Get the centers!
    centers = model.steps["KMeans"].centers
    if number not in centers:
        return {}
    values = dict(centers[number])

    # Return sorted highest to lowest weight
    return {
        k: v for k, v in sorted(values.items(), key=lambda item: item[1], reverse=True)
    }


def predict(text):
    """
    Given a new error, predict where it belongs.
    """
    text = process_text(text)
    if not text:
        return
    client = DjangoClient()
    return client.predict(model_name=settings.MODEL_NAME, features=sentence)


def learn(text):
    """
    Given a new text entry, preprocess it and give to the model to learn.
    """
    text = process_text(text)
    if not text:
        return
    client = DjangoClient()
    client.learn(model_name=settings.MODEL_NAME, features=sentence)


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
    words = [word.strip() for work in text.split(" ")]
    return " ".join(words)
