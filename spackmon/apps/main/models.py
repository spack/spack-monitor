# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from django.db import models, IntegrityError


from django.conf import settings
from django.contrib.postgres.fields import JSONField as DjangoJSONField
from django.db.models import Field, Count
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


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
        related_name="features",
        related_query_name="features",
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


BUILD_STATUS = [
    ("CANCELLED", "CANCELLED"),
    ("SUCCESS", "SUCCESS"),
    ("NOTRUN", "NOTRUN"),
    ("FAILED", "FAILED"),
]


class Spec(BaseModel):
    """A spec is a descriptor for a package, or a particular build configuration
    for it. It doesn't just include package information, but also information
    about a compiler, targets, and other dependnecies. Note that by default
    'spack spec <package>' returns dependencies with a build hash, but here we
    use the full_hash as the identifier.
    """

    # States: succeed, fail, fail because dependency failed (cancelled), not run
    build_status = models.CharField(
        choices=BUILD_STATUS,
        default="NOTRUN",
        blank=False,
        null=False,
        max_length=25,
        help_text="The status of the spec build.",
    )

    # REQUIRED FIELDS: The full hash is used as the unique identifier along with name
    name = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text="The spec name (without version)",
    )
    full_hash = models.CharField(
        max_length=50, blank=True, null=True, help_text="The full hash", unique=True
    )

    build_hash = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The build hash",
    )

    # OPTIONAL FIELDS: We might not have all these at creation time
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
        related_name="dependencies",
        related_query_name="dependencies",
    )

    # Allow for arbitrary storage of output and error
    output = models.TextField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)

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
            "specs": {p.spec.name: p.spec.full_hash for p in self.dependencies.all()},
        }

    def to_dict(self):
        """return the original configuration object, a list of specs"""
        specs = []
        for spec in self.specs.all():
            specs.append(spec.to_dict())
        return {"spec": specs}

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
        unique_together = (("name", "full_hash"),)


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
