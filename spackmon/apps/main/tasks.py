# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spackmon.apps.main.models import (
    BuildPhase,
    BuildEnvironment,
    Build,
    Spec,
    Architecture,
    Target,
    Dependency,
    Compiler,
    Feature,
)
from spackmon.apps.main.utils import read_json

import os
import platform

import logging

logger = logging.getLogger(__name__)


def update_build_phase(phase_name, status, output, **kwargs):
    """Given a spec hash, spack version, and then a phase name, output, and
    status, update the phase associated with the spec. Return a json response
    with a message
    """
    success, result = get_build(**kwargs)
    if not success:
        return success, {"message": "There was an issue with updating the phase."}

    build = result["build"]
    build_phase, _ = BuildPhase.objects.get_or_create(build=build, name=phase_name)
    build_phase.status = status
    build_phase.output = output
    build_phase.save()
    return True, {"message": "Phase %s was successfully updated." % phase_name}


def get_build(
    full_hash, spack_version, hostname, kernel_version, host_os, host_target, platform
):
    """A shared function to first retrieve a spec, then the environment, then the build.
    This could be made much more efficient if we create a build id to return to the client
    to store first.
    """
    try:
        spec = Spec.objects.get(full_hash=full_hash, spack_version=spack_version)
    except Spec.DoesNotExist:
        return False, {
            "message": "The spec with full hash %s and spack version %s does not exist."
            % (full_hash, spack_version),
            "build_created": False,
            "build_environment_created": False,
        }

    # Get or create the BuildEnvironment
    build_environment, created = BuildEnvironment.objects.get_or_create(
        hostname=hostname,
        kernel_version=kernel_version,
        host_target=host_target,
        host_os=host_os,
        platform=platform,
    )

    build, build_created = Build.objects.get_or_create(
        spec=spec, build_environment=build_environment
    )
    return True, {
        "message": "Build get or create was successful.",
        "build_created": build_created,
        "build_environment_created": created,
        "build": build,
        "build_environment": build_environment,
        "spec": spec,
    }


def prepare_build_result(result):
    """Once we are done with using the build result, remove everything
    except for a dict with build information
    """
    if "build" in result:
        result["build"] = result["build"].to_dict()

    # For a new build, we only need to return the build identifier
    for key in ["spec", "build_environment"]:
        if key in result:
            del result[key]
    return result


def new_build(**kwargs):
    """given the full hash and spack version to retrieve a spec, upon successful
    retrieval, generate (or get) a Build object. We require all variables about
    the host environment.
    """
    _, result = get_build(**kwargs)
    return prepare_build_result(result)


def update_build_status(status, **kwargs):
    """Given the metadata (environment and hashes) for a build, retrieve the build based
    on finding the spec and environment
    """
    success, result = get_build(**kwargs)
    if not success:
        return result

    # Update the build status
    build = result["build"]
    build.status = status
    build.save()

    # If the build's spec has other specs with builds, mark them as cancelled
    for dep in build.spec.dependencies.all():
        if dep.spec.build_set.count() > 0:
            dep_build = dep.spec.build_set.first()
            if dep_build.status != "SUCCESS":
                dep_build.status = "CANCELLED"
                dep_build.save()

    return prepare_build_result(result)


def update_build_metadata(metadata, **kwargs):
    """Given a spec, update it with metadata from the package folder where
    it's installed. We assume that not all data is present.
    """
    success, result = get_build(**kwargs)
    if not success:
        return result

    build = result["build"]
    config_args = metadata.get("config")
    envars = metadata.get("envars")
    manifest = metadata.get("manifest")

    # Update the spec with output
    if config_args:
        build.config_args = config_args
    if envars:
        build.update_envars(envars)
    if manifest:
        build.update_install_files(manifest)
    build.save()
    return build


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

        # This assumes the dependencies have the same spack version
        dependency_spec, _ = Spec.objects.get_or_create(
            name=dep_name, full_hash=dep["hash"], spack_version=spec.spack_version
        )
        dependency, _ = Dependency.objects.get_or_create(
            spec=dependency_spec, dependency_type=dep["type"]
        )
        spec.dependencies.add(dependency)

    spec.save()
    return spec


def get_spec(name, meta, spack_version, arch=None, compiler=None):
    """Given a spec name and metadata (hash is required) get or create it"""
    spec, created = Spec.objects.get_or_create(
        name=name, full_hash=meta["full_hash"], spack_version=spack_version
    )
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


def import_configuration_file(filename, spack_version):
    """import a configuration from file (intended to be run from the command line)"""
    filename = os.path.abspath(filename)

    # Tell the user it doesn't exist, but we don't want to exit or raise error
    if not os.path.exists(filename):
        logging.error("%s does not exist" % filename)
        return

    config = read_json(filename)
    return import_configuration(config, spack_version)


def import_configuration(config, spack_version):
    """Given a post of a spec / configuration and a spack version, add the spec
    and entities within to the database. We return a dictionary with three
    values: a Spec object, a boolean to indicate if it was created or not,
    and an optional message to return to the user. If None is returned
    for the configuration, this means that the data was malformed or there
    was another issue with creating it.
    """

    # We are required to have a top level spec
    if "spec" not in config:
        logging.error("spec key not found in file.")
        return {"spec": None, "created": False, "message": "spec key missing"}

    first_spec = None
    was_created = False
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
        spec, created = get_spec(name, meta, spack_version, arch, compiler)

        # Add dependencies if not added yet
        if spec.dependencies.count() == 0:
            spec = add_dependencies(spec, meta.get("dependencies", {}))
            spec.save()

        # Keep a handle on the first spec
        if i == 0:
            was_created = created
            first_spec = spec

    return {"spec": first_spec, "created": was_created, "message": "success"}
