# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spackmon.settings import cfg as settings
from spackmon.apps.main.models import (
    BuildPhase,
    BuildError,
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
import spackmon.apps.main.online_ml as online_ml

import os

import logging

logger = logging.getLogger(__name__)


def create_build_error(phase, error):
    """
    Create or get a build error associated with a phase.
    """
    error, created = BuildError.objects.get_or_create(
        phase=phase,
        source_file=error.get("source_file"),
        source_line_no=error.get("source_line_no"),
        line_no=error.get("line_no"),
        repeat_count=error.get("repeat_count"),
        start=error.get("start"),
        end=error.get("end"),
        text=error.get("text"),
        pre_context=error.get("pre_context"),
        post_context=error.get("post_context"),
    )
    if settings.MODEL_NAME and not settings.DISABLE_ONLINE_ML and created:
        online_ml.learn(error.text, uid=error.id)


def add_errors(errors):
    """
    Add standalone errors.
    """
    count = 0
    error_ids = set()
    for error in errors:
        if "text" not in error:
            logger.warning(
                f"Found error missing text attribute, which is required, skipping.\n{error}"
            )
            continue

        print(error)
        err, created = BuildError.objects.get_or_create(
            source_file=error.get("source_file"),
            source_line_no=error.get("source_line_no"),
            line_no=error.get("line_no"),
            repeat_count=error.get("repeat_count"),
            start=error.get("start"),
            end=error.get("end"),
            text=error["text"],
            pre_context=error.get("pre_context"),
            post_context=error.get("post_context"),
        )
        error_ids.add(err.id)
        if "meta" in error:
            print("ADDING META")
            err.meta = error["meta"]
            err.save()

        if settings.MODEL_NAME and not settings.DISABLE_ONLINE_ML and created:
            online_ml.learn(err.text, uid=err.id)
        count += 1

    return {
        "message": "Successful addition of %s errors" % count,
        "code": 200,
        "error_ids": list(error_ids),
    }


def update_build_phase(build, phase_name, status, errors, **kwargs):
    """Given a build, and then a phase name, output, and
    status, update the phase associated with the build. Return a json response
    with a message
    """
    try:
        build_phase, _ = BuildPhase.objects.get_or_create(build=build, name=phase_name)
        build_phase.status = status
        build_phase.save()
        for error in errors:
            try:
                create_build_error(build_phase, error)
            except:
                pass
        data = {"build_phase": build_phase.to_dict()}
        return {
            "message": "Phase %s was successfully updated." % phase_name,
            "code": 200,
            "data": data,
        }
    except:
        return {"message": "There was an issue updating this phase.", "code": 400}


def get_build(
    full_hash,
    spack_version,
    hostname,
    kernel_version,
    host_os,
    host_target,
    platform,
    owner,
    tags=None,
):
    """A shared function to first retrieve a spec, then the environment, then the build.
    This could be made much more efficient if we create a build id to return to the client
    to store first.
    """
    try:
        spec = Spec.objects.get(full_hash=full_hash, spack_version=spack_version)
    except Spec.DoesNotExist:
        return {
            "message": "The spec with full hash %s and spack version %s does not exist."
            % (full_hash, spack_version),
            "data": {"build_created": False, "build_environment_created": False},
            "code": 400,
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
        spec=spec, build_environment=build_environment, owner=owner
    )

    # Update the tags, the input is comma separated
    if tags:
        for tag in tags.split(","):
            build.tags.add(tag)
        build.save()

    return {
        "message": "Build get or create was successful.",
        "data": {
            "build_created": build_created,
            "build_environment_created": created,
            "build": build.to_dict(),
        },
        "code": 201 if build_created else 200,
    }


def update_build_status(build, status):
    """Given the metadata (environment and hashes) for a build, retrieve the build based
    on finding the spec and environment
    """
    # Update the build status
    build.status = status
    build.save()
    data = {"build": build.to_dict()}

    # If the build's spec has other specs with builds, mark them as cancelled
    for dep in build.spec.dependencies.all():
        if dep.spec.build_set.count() > 0:
            dep_build = dep.spec.build_set.first()
            if dep_build.status != "SUCCESS":
                dep_build.status = "CANCELLED"
                dep_build.save()

    return {"message": "Status updated", "data": data, "code": 200}


def update_build_metadata(build, metadata, **kwargs):
    """Given a spec, update it with metadata from the package folder where
    it's installed. We assume that not all data is present. This "metadata"
    is typically generated by spack analyzers.
    """
    for analyzer_name, results in metadata.items():

        if analyzer_name == "config_args":
            build.config_args = results
        elif analyzer_name == "install_files":
            build.update_install_files(results)
        elif analyzer_name == "environment_variables":
            build.update_envars(results)

        # A generic analyzer is updating features for objects (e.g., libabigail)
        else:
            build.update_install_files_attributes(analyzer_name, results)

    build.save()

    data = {"build": build.to_dict()}
    return {"message": "Metadata updated", "data": data, "code": 200}


def get_target(meta):
    """Given a section of metadata for a target (expected to have name, vendor,
    features, and parents) create the Target objects, which includes also
    creating Feature and Parent (other Target) objects.
    """
    # A target can be a string or a data structure
    if isinstance(meta, str):
        target, _ = Target.objects.get_or_create(name=meta)
        return target

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


def add_dependencies(spec, dependency_list):
    """Given an already created spec and a list of dependencies
    add dependencies to the package, and return a list of all
    (flattened) specs as a list to generate a configuration.
    """
    # Create dependencies (other specs) - they will be updated later
    for dep in dependency_list:

        # This assumes the dependencies have the same spack version
        dependency_spec, _ = Spec.objects.get_or_create(
            name=dep["name"],
            full_hash=dep.get("full_hash") or dep.get("build_hash"),
            spack_version=spec.spack_version,
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
    if "spec" in config:
        config = config["spec"]

    # We are required to have a top level spec
    if "nodes" not in config:
        logging.error("nodes key not found in file.")
        return {
            "spec": None,
            "created": False,
            "message": "spec key missing",
            "code": 400,
        }

    first_spec = None
    was_created = False
    for i, meta in enumerate(config["nodes"]):
        name = meta["name"]

        # If "arch" is not in meta, we failed concretization
        target = None
        arch = None
        if "arch" in meta:

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
            spec = add_dependencies(spec, meta.get("dependencies", []))
            spec.save()

        # Keep a handle on the first spec
        if i == 0:
            was_created = created
            first_spec = spec

    data = {"spec": first_spec, "created": was_created}
    return {"message": "success", "data": data, "code": 201 if was_created else 200}
