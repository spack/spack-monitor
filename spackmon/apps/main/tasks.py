# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spackmon.apps.main.models import (
    Spec,
    Architecture,
    Target,
    Dependency,
    Compiler,
    Feature,
)
from spackmon.apps.main.utils import read_json

import os

import logging

logger = logging.getLogger(__name__)


def update_task_status(full_hash, status):
    """Given a full hash to identify a spec, and a status, update the status
    for the spec. Given that we are cancelling a spec, this means that all
    dependencies are cancelled too.
    """
    try:
        spec = Spec.objects.get(full_hash=full_hash)
        spec.build_status = status
        spec.save()

        # If we cancel or fail, cancel all dependencies that were not successful
        if status in ["CANCELLED", "FAILED"]:
            spec.cancel_dependencies()
    except:
        pass


def update_package_metadata(spec, data):
    """Given a spec, update it with metadata from the package folder where
    it's installed. We assume that not all data is present.
    """
    output = data.get("output")
    error = data.get("output")
    config_args = data.get("config")
    envars = data.get("envars")
    manifest = data.get("manifest")

    # Update the spec with output
    if output:
        spec.output = output
    if error:
        spec.error = error
    if config_args:
        spec.config_args = config_args
    if envars:
        spec.update_envars(envars)
    if manifest:
        spec.update_install_files(manifest)
    spec.save()
    return spec


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


def add_dependencies(spec, dependency_lookup):
    """Given an already created spec and a lookup of dependencies (a dict
    where keys are the dependency (package) name and values include the hash
    and the type) add dependencies to the package, and return a list of all
    (flattened) specs as a list to generate a configuration.
    """
    # Create dependencies (other specs) - they will be updated later
    for dep_name, dep in dependency_lookup.items():
        dependency_spec, _ = Spec.objects.get_or_create(
            name=dep_name, full_hash=dep["hash"]
        )
        dependency, _ = Dependency.objects.get_or_create(
            spec=dependency_spec, dependency_type=dep["type"]
        )
        spec.dependencies.add(dependency)

    spec.save()
    return spec


def get_spec(name, meta, arch=None, compiler=None):
    """Given a spec name and metadata (hash is required) get or create it"""
    spec, created = Spec.objects.get_or_create(name=name, full_hash=meta["full_hash"])
    spec.version = meta.get("version")
    spec.arch = arch
    spec.compiler = compiler
    spec.namespace = meta.get("namespace")
    spec.parameters = meta.get("parameters", {})
    spec.hash = meta.get("hash")
    spec.build_hash = meta.get("build_hash")
    spec.package_hash = meta.get("package_hash")
    spec.save()
    return spec, created


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
    specs to the database. We return a dictionary with three values:
    a configuration object, a boolean to indicate if it was created or not,
    and an optional message to return to the user. If None is returned
    for the configuration, this means that the data was malformed or there
    was another issue with creating it.
    """

    # We are required to have a top level spec
    if "spec" not in config:
        logging.error("spec key not found in file.")
        return {"spec": None, "created": False, "message": "spec key missing"}

    first_spec = None
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

        # Create the spec (full hash and name are unique together)
        spec, created = get_spec(name, meta, arch, compiler)

        # Add dependencies if not added yet
        if spec.dependencies.count() == 0:
            spec = add_dependencies(spec, meta.get("dependencies", {}))
            spec.save()

        # Keep a handle on the first spec
        if i == 0:
            first_spec = spec

    return {"spec": first_spec, "created": created, "message": "success"}
