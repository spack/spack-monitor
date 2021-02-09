__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "Apache-2.0 OR MIT"

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


class Configuration(BaseModel):
    """A configuration is one or more packages (specs) that are being tested
    to work together, e.g., with singularity we have cryptsetup, autoconf, etc.
    Technically I think we have one main package and then it's dependencies,
    but since we represent them all as a set of packages together, this model
    of a Configuration removes the directionality and simply allows us to say
    "These packages (names and versions unique) are represented together for
    this configuration. In the spack landscape, it would be exported to
    json/yaml with the top level "spec" and each entry under that a
    package name. For example:

    {"spec": {"singularity": .. , "cryptsetup": ...}}

    Since packages can be shared between configurations, we use a many to many
    field so each configuration can point to the set of packages that it needs.
    See the m2m signal at the bottom of this file (verify_unique_configuration)
    to see how we ensure that a Configuration cannot be duplicated.
    """

    # Allow for arbitrary storage of output and error
    output = models.TextField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)

    # And a set of packages determine uniqueness
    packages = models.ManyToManyField(
        "main.Package",
        blank=True,
        default=None,
        related_name="packages",
        related_query_name="packages",
    )

    def print(self):
        for package in self.packages.order_by("name"):
            package.print()

    # TODO: generate an export function (to json or yaml) OR we could just save
    # the original config file (but it might not exist)

    def __str__(self):
        return "[configuration:%s packages]" % self.packages.count()

    def __repr__(self):
        return str(self)

    class Meta:
        app_label = "main"


class Architecture(BaseModel):
    """the architecture for a package. Each package only has one."""

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

    def __str__(self):
        if self.vendor:
            return "[target:%s|%s]" % (self.name, self.vendor)
        return "[target:%s|%s]" % self.name

    def __repr__(self):
        return str(self)

    class Meta:
        app_label = "main"


class Compiler(BaseModel):
    """A compiler associated with a package. I'm not sure this is going to be
    kept in the long run (a compiler will be represented as a package) but
    I'm adding for now since it's currently represented in a package spec.
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

    class Meta:
        app_label = "main"


class Feature(BaseModel):
    """A feature of an architecture. While this is one a few fields (inherited
    from BaseModel) we keep it stored in a separate table for easier query.
    """

    name = models.CharField(
        max_length=50, blank=False, null=False, help_text="The name of the feature"
    )

    def __str__(self):
        return "[feature:%s]" % self.name

    def __repr__(self):
        return str(self)


class Package(BaseModel):
    """A package corresponds with a package, meaning it has a version, hashes,
    and other metadata. Since the spack package spec has dependencies with only
    the package name and hash, these are the only two fields we can require.
    """

    # REQUIRED FIELDS: The hash is used as the unique identifier along with name
    name = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text="The package name (without version)",
    )
    hash = models.CharField(
        max_length=50, blank=False, null=False, help_text="The hash", unique=True
    )

    # OPTIONAL FIELDS: We might not have all these at creation time
    namespace = models.CharField(
        max_length=250, blank=True, null=True, help_text="The package namespace"
    )
    version = models.CharField(
        max_length=50, blank=True, null=True, help_text="The package version"
    )

    full_hash = models.CharField(
        max_length=50, blank=True, null=True, help_text="The full hash"
    )
    build_hash = models.CharField(
        max_length=50, blank=True, null=True, help_text="The build hash"
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
    parameters = JSONField(blank=True, null=True, default="{}")

    # Dependencies are just other packages
    dependencies = models.ManyToManyField(
        "main.Dependency",
        blank=True,
        default=None,
        related_name="dependencies",
        related_query_name="dependencies",
    )

    def print(self):
        if self.version:
            name = "%s v%s" % (self.name, self.version)
            print("%-35s %-35s" % (name, self.hash))
        else:
            print("%-35s %-35s" % (self.name, self.hash))

    def __str__(self):
        if self.version:
            return "[package:%s|%s|%s]" % (self.name, self.version, self.hash)
        return "[package:%s|%s]" % (self.name, self.hash)

    def __repr__(self):
        return str(self)

    # TODO: have a function to easily add a dependency based on hash

    class Meta:
        app_label = "main"
        unique_together = (("name", "hash"),)


class Dependency(BaseModel):
    """A dependency is actually just a link to a package, but it also includes
    the dependency type
    """

    package = models.ForeignKey(
        "main.Package", null=False, blank=False, on_delete=models.CASCADE
    )
    dependency_type = JSONField(
        blank=False,
        null=False,
        default="[]",
        help_text="The dependency type, e.g., build run",
    )

    # TODO: have a function to easily add / remove a type

    def __str__(self):
        return "[dependency:%s|%s]" % (self.package.name, self.dependency_type)

    def __repr__(self):
        return str(self)

    class Meta:
        app_label = "main"
        unique_together = (("package", "dependency_type"),)


@receiver(m2m_changed, sender=Configuration.packages.through)
def verify_unique_configuration(sender, **kwargs):
    """This is a many to many manager signal that ensures that the packages
    (names and versions) provided to the Configuration model are unique.
    This would prevent us from adding the same configuration twice. Since
    packages are unique based on name and version, we can do this check by
    way of ensuring that no other configurations exist with exactly those
    packages.
    """
    action = kwargs.get("action", None)
    packages = kwargs.get("pk_set", None)

    if action == "pre_add":

        # Filter down to those with same packages (id and number)
        contenders = (
            Configuration.objects.filter(packages__in=packages)
            .annotate(number_packages=Count("packages"))
            .filter(number_packages=len(packages))
        ).count()

        # If we have a result, this means the Configuration already exists
        if contenders > 0:
            raise IntegrityError(
                "Configuration already exists for packages %s" % packages
            )
