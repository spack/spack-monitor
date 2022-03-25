# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.core.management.base import BaseCommand, CommandError
from spackmon.apps.main.tasks import import_configuration_file
import os

try:
    from django_river_ml.client import DjangoClient
except ImportError:
    raise CommandError("django_river_ml needs to be installed as a module.")


class Command(BaseCommand):
    """load a river model by name"""

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs=1, default=None, type=str)
        parser.add_argument("model_name", nargs=1, default=None, type=str)

    help = "Load a river model to overwrite existing."

    def handle(self, *args, **options):
        if not options["filename"]:
            raise CommandError("Please provide a filename (pickle) with the model")
        if not options["model_name"]:
            raise CommandError("Please provide the model_name to load into")

        print("%-35s %-35s" % ("Filename", options["filename"][0]))
        print("%-35s %-35s" % ("Model Name", options["model_name"][0]))

        # Currently only support json (can add yaml if needed)
        if not options["filename"][0].endswith("pkl"):
            raise CommandError("Currently only pickle import is supported.")

        model_file = options["filename"][0]
        model_name = options["model_name"][0]

        client = DjangoClient()

        if not os.path.exists(model_file):
            raise CommandError(f"{model_file} does not exist.")

        print(f"Found {model_file} to load.")
        model = client.load_model(model_file)
        client.add_model(model, "cluster", name=model_name)
