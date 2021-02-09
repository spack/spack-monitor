__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

from spackmon.apps.main.models import (
    Configuration,
    Package,
    Architecture,
    Target,
    Dependency,
    Compiler,
    Feature,
)
from spackmon.apps.main.utils import read_json

from django.db.models import Count
import os
import re

import logging

logger = logging.getLogger(__name__)


def get_configuration(packages):
    """A configuration is unique based on it's package specs. We query
    for a match based on a list, and if one is not found, we create a new
    configuration with the specs.

    Parameters
    ==========
    packages (list models.Package): a list of Package objects in the config
    """
    # Filter down to those with same packages (id and number)
    existing = (
        Configuration.objects.filter(packages__in=packages)
        .annotate(number_packages=Count("packages"))
        .filter(number_packages=len(packages))
    )
    if existing:
        return existing.first()

    config = Configuration.objects.create()
    config.packages.set(packages)
    config.save()
    return config


def get_target(meta):
    """Given a section of metadata for a target (expected to have name, vendor,
    features, and parents) create the Target objects, which includes also
    creating Feature and Parent (other Target) objects.
    """
    target, _ = Target.objects.get_or_create(name=meta["name"])
    target.generation = meta.get("generation")
    target.vendor = meta.get("vendor")

    # add features
    features = []
    for feature_name in meta.get("features", []):
        feature, _ = Feature.objects.get_or_create(name=feature_name)
        features.append(feature)

    [target.features.add(x) for x in features]

    # The parent is another target
    for parent_name in meta.get("parents", []):
        parent, _ = Target.objects.get_or_create(name=parent_name)
        target.parents.add(parent)

    target.save()
    return target


def add_dependencies(package, dependency_lookup):
    """Given an already created package and a lookup of dependencies (a dict
    where keys are the dependency (package) name and values include the hash
    and the type) add dependencies to the package, and return a list of all
    (flattened) packages as a list to generate a configuration.
    """
    # Create dependencies (other packages) - they will be updated later
    for dep_name, dep in dependency_lookup.items():
        dependency_package, _ = Package.objects.get_or_create(
            name=dep_name, hash=dep["hash"]
        )
        dependency, _ = Dependency.objects.get_or_create(
            package=dependency_package, dependency_type=dep["type"]
        )
        package.dependencies.add(dependency)

    package.save()
    return package


def get_package(name, meta, arch=None, compiler=None):
    """Given a package name and metadata (hash is required) get or create it"""
    package, _ = Package.objects.get_or_create(name=name, hash=meta["hash"])
    package.version = meta.get("version")
    package.arch = arch
    package.compiler = compiler
    package.namespace = meta.get("namespace")
    package.parameters = meta.get("parameters", {})
    package.build_hash = meta.get("build_hash")
    package.full_hash = meta.get("full_hash")
    package.save()
    return package


def import_configuration(filename):
    """Given a post of a spec / configuration, add the configuration and
    packages to the database. This function will likely be broken into pieces
    when we create the API endpoints for spack (since it won't all be done at
    once).
    """

    filename = os.path.abspath(filename)

    # Tell the user it doesn't exist, but we don't want to exit or raise error
    if not os.path.exists(filename):
        logging.error("%s does not exist" % filename)
        return

    config = read_json(filename)

    # We are required to have a top level spec
    if "spec" not in config:
        logging.error("spec key not found in %s" % filename)
        return

    # Keep a full list of specs for the config
    specs = []

    for metadata in config["spec"]:
        name = list(metadata.keys())[0]
        meta = metadata[name]

        # Create target for architecture (uniqueness based on name)
        target = get_target(meta=meta["arch"]["target"])

        # Create architecture
        arch, _ = Architecture.objects.get_or_create(
            target=target,
            platform=meta["arch"]["platform"],
            platform_os=meta["arch"]["platform_os"],
        )

        # Create compiler (only if it's still there)
        compiler = None
        if "compiler" in meta:
            compiler, _ = Compiler.objects.get_or_create(
                name=meta["compiler"]["name"], version=meta["compiler"]["version"]
            )

        # Create the package (hash and name are unique together)
        package = get_package(name, meta, arch, compiler)

        # Return a list of all packages (the main package and deps)
        package = add_dependencies(package, meta.get("dependencies", {}))
        specs.append(package)

    # Create the top level configuration
    config = get_configuration(specs)
    return config
