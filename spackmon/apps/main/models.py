# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField as DjangoJSONField
from django.db.models import Field, Count

from .utils import BUILD_STATUS, PHASE_STATUS

import json


class JSONField(DjangoJSONField):
    pass


# Sqlite doesn't support a Json Field, so we make it
if "sqlite" in settings.DATABASES["default"]["ENGINE"]:

    class JSONField(Field):
        def db_type(self, connection):
            return "text"

        def from_db_value(self, value, expression, connection):
            if value is not None:
                return self.to_python(value)
            return value

        def to_python(self, value):
            if value is not None:
                try:
                    return json.loads(value)
                except (TypeError, ValueError):
                    return value
            return value

        def get_prep_value(self, value):
            if value is not None:
                return str(json.dumps(value))
            return value

        def value_to_string(self, obj):
            return self.value_from_object(obj)


class BaseModel(models.Model):
    add_date = models.DateTimeField("date published", auto_now_add=True)
    modify_date = models.DateTimeField("date modified", auto_now=True)

    class Meta:
        abstract = True


class Attribute(BaseModel):
    """an attribute can be any key/value pair (e.g., an ABI feature) associated
    with an object
    """

    name = models.CharField(
        max_length=150, blank=False, null=False, help_text="The name of the attribute"
    )
    value = models.TextField(blank=False, null=False, help_text="The value")

    class Meta:
        app_label = "main"
        unique_together = (("name", "value"),)


class InstallFile(BaseModel):
    """An Install File is associated with a spec package install.
    An install file can be an object, in which case it will have an object_type.
    Each can optionally have attributes (features extracted for it)
    """

    build = models.ForeignKey(
        "main.Build", null=False, blank=False, on_delete=models.CASCADE
    )

    name = models.CharField(
        max_length=500,
        blank=False,
        null=False,
        help_text="The name of the install file, with user prefix removed",
        unique=True,
    )

    ftype = models.CharField(
        max_length=25,
        blank=True,
        null=False,
        help_text="The type of install file",
    )

    mode = models.PositiveIntegerField(blank=True, null=True)
    owner = models.PositiveIntegerField(blank=True, null=True)
    group = models.PositiveIntegerField(blank=True, null=True)

    # The object type, e.g., .jar, .so,)
    object_type = models.CharField(
        max_length=25, blank=False, null=False, help_text="The type of library"
    )
    hash = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text="The hash of the object",
    )

    # This is where we export ABI features to, via a general attribute that can
    # accept any name/value
    attributes = models.ManyToManyField(
        "main.Attribute",
        blank=True,
        default=None,
        related_name="object",
        related_query_name="object",
    )

    def to_manifest(self):
        """If we return a single dependency as a dict, the configuration can
        combine them into one dict by updating based on the name as key.
        """
        manifest = {
            self.name: {
                "mode": self.mode,
                "owner": self.owner,
                "group": self.group,
                "type": self.type,
            }
        }
        if self.hash:
            manifest[self.name]["hash"] = self.hash
        return manifest

    def to_dict(self):
        """An extended manifest with the object type and hash."""
        manifest = self.to_manifest()
        manifest["object_type"] = self.object_type
        manifest["build"] = self.build.to_dict()

    class Meta:
        app_label = "main"
        unique_together = (("build", "name"),)


class Build(BaseModel):
    """A build is the highest level object that enforces uniqueness for a spec,
    and a build environment (basically the hostname and kernel version).
    We also have a link to Objects (of type object) that can hold the
    object type, and a group of features (e.g., ABI features)
    """

    spec = models.ForeignKey(
        "main.Spec", null=False, blank=False, on_delete=models.CASCADE
    )

    # States: succeed, fail, fail because dependency failed (cancelled), not run
    status = models.CharField(
        choices=BUILD_STATUS,
        default="NOTRUN",
        blank=False,
        null=False,
        max_length=25,
        help_text="The status of the spec build.",
    )

    files_installed = models.ManyToManyField(
        "main.InstallFile",
        blank=True,
        default=None,
        related_name="build_for_files",
        related_query_name="build_for_files",
    )
    build_environment = models.ForeignKey(
        "main.BuildEnvironment", null=False, blank=False, on_delete=models.DO_NOTHING
    )

    # Dependencies are just other specs
    envars = models.ManyToManyField(
        "main.EnvironmentVariable",
        blank=True,
        default=None,
        related_name="build_for_environment",
        related_query_name="build_for_environment",
    )

    config_args = models.TextField(blank=True, null=True)

    def update_envars(self, envars):
        """Given a dictionary of key value pairs, update the associated
        environment variables. Since a build can be updated, we first
        remove any associated environment variables.
        """
        # Delete existing environment variables not associated elsewhere
        self.envars.annotate(build_count=Count("build_for_environment")).filter(
            build_count=1
        ).delete()

        new_envars = []
        for key, value in envars.items():
            new_envar, _ = EnvironmentVariable.objects.get_or_create(
                name=key, value=value
            )
            new_envars.append(new_envar)

        # This does bulk save / update to database
        self.envars.add(*new_envars)

    def update_install_files_attributes(self, files):
        """Given install files that have one or more attributes, update them
        The data should have install files as keys in a dictionary, with
        each having another dictionary of key, value paired attributes.
        """
        for file_name, attributes in files.items():
            obj = InstallFile.objects.get_or_create(
                build=self,
                name=file_name,
            )
            for attr_name, attr_value in attributes.items():
                attr, _ = Attribute.objects.get_or_create(
                    name=attr_name, value=attr_value
                )
                obj.attributes.add(attr)

    def update_install_files(self, manifest):
        """Given a spack install manifest, update the spec to include the
        files. We remove the prefix so the files are relative
        to the spack installation directory
        """
        for filename, attrs in manifest.items():

            # Store path after /spack/opt/spack
            filename = filename.split("/spack/opt/spack/", 1)
            install_file, _ = InstallFile.objects.get_or_create(
                build=self,
                name=filename,
            )
            install_file.ftype = attrs["type"]
            install_file.mode = attrs["mode"]
            install_file.owner = attrs["owner"]
            install_file.group = attrs["group"]

    def to_dict(self):
        return {
            "build_id": self.id,
            "spec_full_hash": self.spec.full_hash,
            "spec_name": self.spec.name,
        }

    def __str__(self):
        return "[build|%s v%s|%s]" % (
            self.spec.name,
            self.spec.version,
            self.build_environment.arch,
        )

    def __repr__(self):
        return str(self)

    class Meta:
        app_label = "main"
        unique_together = (("spec", "build_environment"),)


class BuildEnvironment(BaseModel):
    """A build environment holds information about the hostname and kernel."""

    hostname = models.CharField(
        max_length=150, blank=False, null=False, help_text="The hostname"
    )
    platform = models.CharField(
        max_length=50, blank=False, null=False, help_text="The platform"
    )
    kernel_version = models.CharField(
        max_length=150, blank=False, null=False, help_text="The kernel version"
    )
    host_os = models.CharField(
        max_length=150, blank=False, null=False, help_text="The hostname"
    )
    # host target we can get from archspec inside spack
    host_target = models.CharField(
        max_length=150, blank=False, null=False, help_text="The hostname"
    )

    def __str__(self):
        return "[build-environment|%s]" % self.arch

    def __repr__(self):
        return str(self)

    @property
    def arch(self):
        return "%s %s %s" % (self.platform, self.host_os, self.host_target)

    class Meta:
        app_label = "main"
        unique_together = (
            ("hostname", "kernel_version", "host_os", "host_target", "platform"),
        )


class Architecture(BaseModel):
    """the architecture for a spec. Each spec only has one."""

    platform = models.CharField(
        max_length=50, blank=False, null=False, help_text="The platform (e.g., linux)"
    )
    platform_os = models.CharField(
        max_length=50,
        blank=False,
        null=False,
        help_text="The platform operating system",
    )
    target = models.ForeignKey(
        "main.Target", null=False, blank=False, on_delete=models.CASCADE
    )

    def __str__(self):
        return "[architecture:%s|%s]" % (self.platform, self.platform_os)

    def __repr__(self):
        return str(self)

    def to_dict(self):
        return {
            "platform": self.platform,
            "platform_os": self.platform_os,
            "target": self.target.to_dict(),
        }

    class Meta:
        app_label = "main"
        unique_together = (("platform", "platform_os", "target"),)


class Target(BaseModel):
    """the target of an architecture."""

    name = models.CharField(
        max_length=50,
        blank=False,
        null=False,
        help_text="The name of the target (e.g., skylake)",
        unique=True,
    )
    vendor = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The vendor for the target (e.g., GenuineIntel",
    )
    features = models.ManyToManyField(
        "main.Feature",
        blank=True,
        default=None,
        related_name="target_features",
        related_query_name="target_features",
    )
    generation = models.PositiveIntegerField(blank=True, null=True)
    parents = models.ManyToManyField(
        "main.Target",
        blank=True,
        default=None,
        related_name="targets",
        related_query_name="targets",
    )

    def list_features(self):
        """Return the features as a list of strings"""
        return [x.name for x in self.features.all()]

    def list_parents(self):
        """Return the parents as a list of strings"""
        return [x.name for x in self.parents.all()]

    def __str__(self):
        if self.vendor:
            return "[target:%s|%s]" % (self.name, self.vendor)
        return "[target:%s|%s]" % self.name

    def __repr__(self):
        return str(self)

    def to_dict(self):
        return {
            "name": self.name,
            "vendor": self.vendor,
            "features": self.list_features(),
            "generation": self.generation,
            "parents": self.list_parents(),
        }

    class Meta:
        app_label = "main"


class Compiler(BaseModel):
    """A compiler associated with a spec. I'm not sure this is going to be
    kept in the long run (a compiler will be represented as a spec) but
    I'm adding for now since it's currently represented in a spec spec.
    """

    name = models.CharField(
        max_length=50, blank=False, null=False, help_text="The compiler name"
    )
    version = models.CharField(
        max_length=50, blank=False, null=False, help_text="The compiler version string"
    )

    def __str__(self):
        return "[compiler:%s|%s]" % (self.name, self.version)

    def __repr__(self):
        return str(self)

    def to_dict(self):
        """Dump the data back into it's original dictionary representation"""
        return {"name": self.name, "version": self.version}

    class Meta:
        app_label = "main"


class Feature(BaseModel):
    """A feature of an architecture. While this is one a few fields (inherited
    from BaseModel) we keep it stored in a separate table for easier query.
    """

    name = models.CharField(
        max_length=50, blank=False, null=False, help_text="The name of the feature"
    )

    def to_dict(self):
        """It's unlikely that we want a single feature in a list, but we provide
        this function to be consistent with the other models
        """
        return [self.name]

    def __str__(self):
        return "[feature:%s]" % self.name

    def __repr__(self):
        return str(self)


class Spec(BaseModel):
    """A spec is a descriptor for a package, or a particular build configuration
    for it. It doesn't just include package information, but also information
    about a compiler, targets, and other dependnecies. Note that by default
    'spack spec <package>' returns dependencies with a build hash, but here we
    use the full_hash as the identifier.
    """

    # REQUIRED FIELDS: The full hash is used as the unique identifier along with name
    name = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text="The spec name (without version)",
    )

    spack_version = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text="The version of spack",
    )

    full_hash = models.CharField(
        max_length=50, blank=True, null=True, help_text="The full hash"
    )

    name = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text="The spec name (without version)",
    )

    # OPTIONAL FIELDS: We might not have all these at creation time
    build_hash = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The build hash",
    )

    hash = models.CharField(
        max_length=50, blank=False, null=False, help_text="The hash"
    )

    # I'm not sure why I see this instead of build_hash after specifying to
    # use the full_hash as the identifier instead of build_hash
    package_hash = models.CharField(
        max_length=250, blank=True, null=True, help_text="The spec hash"
    )

    namespace = models.CharField(
        max_length=250, blank=True, null=True, help_text="The spec namespace"
    )
    version = models.CharField(
        max_length=50, blank=True, null=True, help_text="The spec version"
    )

    # This assumes that a package can only have one architecture
    # If we delete an architecture, the associated packages are deleted too
    arch = models.ForeignKey(
        "main.Architecture", null=True, blank=True, on_delete=models.CASCADE
    )

    # Assume that we won't represent compilers in the future
    compiler = models.ForeignKey(
        "main.Compiler", null=True, blank=True, on_delete=models.DO_NOTHING
    )

    # Parameters are less likely to be queried (we still can with json field) but we should
    # use json field to allow for more flexibility in variance or change
    parameters = JSONField(blank=True, null=True, default=dict)

    # Dependencies are just other specs
    dependencies = models.ManyToManyField(
        "main.Dependency",
        blank=True,
        default=None,
        related_name="dependencies_for_spec",
        related_query_name="dependencies_for_spec",
    )

    def print(self):
        if self.version:
            name = "%s v%s" % (self.name, self.version)
            print("%-35s %-35s" % (name, self.full_hash))
        else:
            print("%-35s %-35s" % (self.name, self.full_hash))

    def __str__(self):
        if self.version:
            return "[spec:%s|%s|%s]" % (self.name, self.version, self.full_hash)
        return "[spec:%s|%s]" % (self.name, self.full_hash)

    def __repr__(self):
        return str(self)

    def to_dict_ids(self):
        """This function is intended to return a simple json response that
        includes the configuration and spec ids, but not additional
        metadata. It's intended to be a lookup for a calling client to make
        additional calls.
        """
        return {
            "full_hash": self.full_hash,
            "name": self.name,
            "version": self.version,
            "spack_version": self.spack_version,
            "specs": {p.spec.name: p.spec.full_hash for p in self.dependencies.all()},
        }

    def list_dependencies(self):
        """Loop through associated dependencies and return a single dictionary,
        with the key as the dependency name
        """
        deps = {}
        for dep in self.dependencies.all():
            deps.update(dep.to_dict())
        return deps

    def to_dict_dependencies(self):
        """return the serialized dependency packages"""
        deps = {}
        for dep in self.dependencies.all():
            deps[dep.spec.name] = dep.spec.to_dict()
        return deps

    def to_dict(self, include_deps=False):
        """We return a dictionary with the package name as key, metadata as
        another dictionary as the main item. This should mimic the original
        spec json object imported.
        """

        result = {
            self.name: {
                "version": self.version,
                "arch": self.arch.to_dict() if self.arch else None,
                "compiler": self.compiler.to_dict() if self.compiler else None,
                "namespace": self.namespace,
                "parameters": self.parameters,
                "dependencies": self.list_dependencies(),
                "hash": self.hash,
                "full_hash": self.full_hash,
                "build_hash": self.build_hash,
                "package_hash": self.package_hash,
            }
        }

        # Do we want to also dump the dependency packages?
        if include_deps:
            result.update(self.to_dict_dependencies())

        return result

    class Meta:
        app_label = "main"
        unique_together = (("name", "full_hash", "spack_version"),)


class BuildPhase(BaseModel):
    """A build phase stores the name, status, output, and error for a phase.
    We associated it with a Build (and not a Spec) as the same spec can have
    different builds depending on the environment.
    """

    build = models.ForeignKey(
        "main.Build", null=False, blank=False, on_delete=models.CASCADE
    )

    # Allow for arbitrary storage of output and error
    output = models.TextField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)

    status = models.CharField(
        choices=PHASE_STATUS,
        max_length=50,
        blank=True,
        null=True,
        help_text="The status of the phase, if run.",
    )

    name = models.CharField(
        max_length=500,
        blank=False,
        null=False,
        help_text="The name of the install file, with user prefix removed",
        unique=True,
    )

    def __str__(self):
        return "[build-phase:%s|%s]" % (self.build.spec.name, self.name)

    def __repr__(self):
        return str(self)

    def to_dict(self):
        return {"id": self.id, "status": self.status, "name": self.name}

    class Meta:
        app_label = "main"
        unique_together = (("build", "name"),)


class Dependency(BaseModel):
    """A dependency is actually just a link to a spec, but it also includes
    the dependency type
    """

    spec = models.ForeignKey(
        "main.Spec", null=False, blank=False, on_delete=models.CASCADE
    )
    dependency_type = JSONField(
        blank=False,
        null=False,
        default=list,
        help_text="The dependency type, e.g., build run",
    )

    def __str__(self):
        return "[dependency:%s|%s]" % (self.spec.name, self.dependency_type)

    def __repr__(self):
        return str(self)

    def to_dict(self):
        """If we return a single dependency as a dict, the configuration can
        combine them into one dict by updating based on the name as key.
        """
        return {
            self.spec.name: {
                "hash": self.spec.build_hash,
                "type": self.dependency_type,
            }
        }

    class Meta:
        app_label = "main"
        unique_together = (("spec", "dependency_type"),)


class EnvironmentVariable(BaseModel):
    """An environment variable is a key value pair that can be associated with
    one or more spec installs. We parse them from the spack-build-env.txt file,
    and filter down to only include SPACK_* variables.
    """

    name = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        help_text="The name of the environment variable.",
    )
    value = models.TextField(
        blank=False,
        null=False,
        help_text="The value of the environment variable",
    )

    def __str__(self):
        value = self.value
        if len(self.value) > 200:
            value = "%s..." % self.value[:200]
        return "[envar:%s|%s]" % (self.name, value)

    def __repr__(self):
        return str(self)

    def to_dict(self):
        """If we return a single dependency as a dict, the configuration can
        combine them into one dict by updating based on the name as key.
        """
        return {self.name: self.value}

    class Meta:
        app_label = "main"
        unique_together = (("name", "value"),)
