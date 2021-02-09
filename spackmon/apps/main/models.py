__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021, Vanessa Sochat"
__license__ = "MPL 2.0"

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
    generation = models.PositiveIntegerField()
    parents = models.ManyToManyField(
        "main.Target",
        blank=True,
        default=None,
        related_name="parents",
        related_query_name="parents",
    )

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


class Feature(BaseModel):
    """A feature of an architecture. While this is one a few fields (inherited
    from BaseModel) we keep it stored in a separate table for easier query.
    """

    name = models.CharField(
        max_length=50, blank=False, null=False, help_text="The name of the feature"
    )


class Package(BaseModel):
    """A package corresponds with a package, meaning it has a version,"""

    name = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text="The package name (without version)",
    )
    namespace = models.CharField(
        max_length=250, blank=True, null=True, help_text="The package namespace"
    )
    version = models.CharField(
        max_length=50, blank=False, null=False, help_text="The package version"
    )

    # Will there always be a build hash (here assumes no)?
    hash_ = models.CharField(
        max_length=50, blank=False, null=False, help_text="The hash"
    )
    full_hash = models.CharField(
        max_length=50, blank=False, null=False, help_text="The full hash"
    )
    build_hash = models.CharField(
        max_length=50, blank=True, null=True, help_text="The build hash"
    )

    # This assumes that a package can only have one architecture
    # If we delete an architecture, the associated packages are deleted too
    arch = models.ForeignKey(
        "main.Architecture", null=False, blank=False, on_delete=models.CASCADE
    )

    # Assume that we won't represent compilers in the future
    compiler = models.ForeignKey(
        "main.Compiler", null=True, blank=True, on_delete=models.DO_NOTHING
    )

    # Parameters are less likely to be queried (we still can with json field) but we should
    # use json field to allow for more flexibility in variance or change
    parameters = JSONField(blank=False, null=False, default="{}")

    # Dependencies are just other packages
    dependencies = models.ManyToManyField(
        "main.Dependency",
        blank=True,
        default=None,
        related_name="dependencies",
        related_query_name="dependencies",
    )

    # TODO: have a function to easily add a dependency based on hash

    class Meta:
        app_label = "main"

        # Or should we use hash or full_hash?
        unique_together = (("name", "version", "arch", "full_hash"),)


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
