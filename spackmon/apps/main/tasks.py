__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

from spackmon.apps.main.models import (
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
            name=dep_name, full_hash=dep["hash"]
        )
        dependency, _ = Dependency.objects.get_or_create(
            package=dependency_package, dependency_type=dep["type"]
        )
        package.dependencies.add(dependency)

    package.save()
    return package


def get_package(name, meta, arch=None, compiler=None):
    """Given a package name and metadata (hash is required) get or create it"""
    package, created = Package.objects.get_or_create(
        name=name, full_hash=meta["full_hash"]
    )
    package.version = meta.get("version")
    package.arch = arch
    package.compiler = compiler
    package.namespace = meta.get("namespace")
    package.parameters = meta.get("parameters", {})
    package.hash = meta.get("hash")
    package.build_hash = meta.get("build_hash")
    package.package_hash = meta.get("package_hash")
    package.save()
    return package, created


def import_configuration_file(filename):
    """import a configuration from file (intended to be run from the command line)"""
    filename = os.path.abspath(filename)

    # Tell the user it doesn't exist, but we don't want to exit or raise error
    if not os.path.exists(filename):
        logging.error("%s does not exist" % filename)
        return

    config = read_json(filename)
    return import_configuration(config)


def import_configuration(config):
    """Given a post of a spec / configuration, add the configuration and
    packages to the database. We return a dictionary with three values:
    a configuration object, a boolean to indicate if it was created or not,
    and an optional message to return to the user. If None is returned
    for the configuration, this means that the data was malformed or there
    was another issue with creating it.
    """

    # We are required to have a top level spec
    if "spec" not in config:
        logging.error("spec key not found in %s" % filename)
        return {"config": None, "created": False, "message": "spec key missing"}

    first_package = None
    for i, metadata in enumerate(config["spec"]):
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
        package, created = get_package(name, meta, arch, compiler)

        if not created:
            package = add_dependencies(package, meta.get("dependencies", {}))
            package.save()

        # Keep a handle on the first package
        if i == 0:
            first_package = package

    return {"package": first_package, "created": created, "message": "success"}
