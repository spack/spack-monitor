# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spackmon.apps.main.models import (
    Attribute,
    Architecture,
    Build,
    BuildEnvironment,
    BuildError,
    BuildWarning,
    BuildPhase,
    Compiler,
    Dependency,
    EnvironmentVariable,
    InstallFile,
    Feature,
    Target,
    Spec,
)

from taggit.models import Tag

from .permissions import IsAuthenticated
from rest_framework import serializers, viewsets


################################################################################
# Serializers paired with Viewsets
################################################################################

# Attribute


class AttributeSerializer(serializers.ModelSerializer):
    install_file = serializers.PrimaryKeyRelatedField(
        queryset=InstallFile.objects.all(), required=False
    )
    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "attribute"

    class Meta:
        model = Attribute
        fields = (
            "id",
            "install_file",
            "analyzer",
            "value",
            "binary_value",
            "add_date",
            "modify_date",
            "label",
        )


class AttributeViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Attribute.objects.all()

    serializer_class = AttributeSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# Architecture


class ArchitectureSerializer(serializers.ModelSerializer):
    target = serializers.PrimaryKeyRelatedField(queryset=Target.objects.all())
    label = serializers.SerializerMethodField("get_label")

    def get_label(self, container):
        return "architecture"

    class Meta:
        model = Architecture
        fields = (
            "id",
            "platform",
            "platform_os",
            "target",
            "add_date",
            "modify_date",
            "label",
        )


class ArchitectureViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Architecture.objects.all()

    serializer_class = ArchitectureSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# Builds


class BuildSerializer(serializers.ModelSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), required=False, many=True
    )
    build_environment = serializers.PrimaryKeyRelatedField(
        queryset=BuildEnvironment.objects.all()
    )
    envars = serializers.PrimaryKeyRelatedField(
        queryset=EnvironmentVariable.objects.all(),
        many=True,
        required=False,
    )
    spec = serializers.PrimaryKeyRelatedField(queryset=Spec.objects.all())
    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "build"

    class Meta:
        model = Build
        fields = (
            "id",
            "spec",
            "tags",
            "status",
            "build_environment",
            "envars",
            "config_args",
            "add_date",
            "modify_date",
            "label",
        )


class BuildViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Build.objects.all()

    serializer_class = BuildSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# Build Environment


class BuildEnvironmentSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "build-environment"

    class Meta:
        model = BuildEnvironment

        # Extra keyword arguments for create
        fields = (
            "id",
            "hostname",
            "platform",
            "kernel_version",
            "host_os",
            "host_target",
            "add_date",
            "modify_date",
            "label",
        )


class BuildEnvironmentViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return BuildEnvironment.objects.all()

    serializer_class = BuildEnvironmentSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# BuildError


class BuildErrorSerializer(serializers.ModelSerializer):

    phase = serializers.PrimaryKeyRelatedField(queryset=BuildPhase.objects.all())
    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "build-error"

    class Meta:
        model = BuildError
        fields = (
            "id",
            "phase",
            "source_file",
            "source_line_no",
            "line_no",
            "repeat_count",
            "start",
            "end",
            "text",
            "pre_context",
            "post_context",
            "add_date",
            "modify_date",
            "label",
        )


class BuildErrorViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return BuildError.objects.all()

    serializer_class = BuildErrorSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# BuildWarning


class BuildWarningSerializer(serializers.ModelSerializer):

    phase = serializers.PrimaryKeyRelatedField(queryset=BuildPhase.objects.all())
    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "build-error"

    class Meta:
        model = BuildWarning
        fields = (
            "id",
            "phase",
            "source_file",
            "source_line_no",
            "line_no",
            "repeat_count",
            "start",
            "end",
            "text",
            "pre_context",
            "post_context",
            "add_date",
            "modify_date",
            "label",
        )


class BuildWarningViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return BuildWarning.objects.all()

    serializer_class = BuildWarningSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# Build Phase


class BuildPhaseSerializer(serializers.ModelSerializer):
    build = serializers.PrimaryKeyRelatedField(queryset=Build.objects.all())
    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "build-phase"

    class Meta:
        model = BuildPhase
        fields = (
            "id",
            "label",
            "build",
            "output",
            "error",
            "status",
            "name",
            "label",
            "add_date",
            "modify_date",
        )


class BuildPhaseViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return BuildPhase.objects.all()

    serializer_class = BuildPhaseSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# Compiler


class CompilerSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "compiler"

    class Meta:
        model = Compiler
        fields = ("id", "version", "name", "add_date", "modify_date", "label")


class CompilerViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Compiler.objects.all()

    serializer_class = CompilerSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# Dependency


class DependencySerializer(serializers.ModelSerializer):

    spec = serializers.PrimaryKeyRelatedField(queryset=Spec.objects.all())
    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "dependency"

    class Meta:
        model = Dependency
        fields = ("id", "spec", "dependency_type", "add_date", "modify_date", "label")


class DependencyViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Dependency.objects.all()

    serializer_class = DependencySerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# EnvironmentVariable


class EnvironmentVariableSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "environment-variable"

    class Meta:
        model = EnvironmentVariable
        fields = ("id", "name", "value", "add_date", "modify_date", "label")


class EnvironmentVariableViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return EnvironmentVariable.objects.all()

    serializer_class = EnvironmentVariableSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# Install Files


class InstallFileSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField("get_label")
    build = serializers.PrimaryKeyRelatedField(queryset=Build.objects.all())

    def get_label(self, instance):
        return "install-file"

    class Meta:
        model = InstallFile
        fields = (
            "id",
            "build",
            "name",
            "ftype",
            "mode",
            "owner",
            "group",
            "category",
            "hash",
            "add_date",
            "modify_date",
            "label",
        )


class InstallFileViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return InstallFile.objects.all()

    serializer_class = InstallFileSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# Feature


class FeatureSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "feature"

    class Meta:
        model = Feature
        fields = ("id", "name", "add_date", "modify_date", "label")


class FeatureViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Feature.objects.all()

    serializer_class = FeatureSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# Target


class TargetSerializer(serializers.ModelSerializer):

    features = serializers.PrimaryKeyRelatedField(
        queryset=Feature.objects.all(), required=False, many=True
    )
    parents = serializers.PrimaryKeyRelatedField(
        queryset=Target.objects.all(), many=True, required=False
    )
    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "target"

    class Meta:
        model = Target
        fields = (
            "id",
            "name",
            "vendor",
            "features",
            "generation",
            "parents",
            "add_date",
            "modify_date",
            "label",
        )


class TargetViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Target.objects.all()

    serializer_class = TargetSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]


# Spec


class SpecSerializer(serializers.ModelSerializer):

    dependencies = serializers.PrimaryKeyRelatedField(
        queryset=Dependency.objects.all(), many=True
    )
    compiler = serializers.PrimaryKeyRelatedField(queryset=Compiler.objects.all())
    arch = serializers.PrimaryKeyRelatedField(queryset=Architecture.objects.all())
    label = serializers.SerializerMethodField("get_label")

    def get_label(self, instance):
        return "spec"

    class Meta:
        model = Spec
        fields = (
            "id",
            "name",
            "spack_version",
            "full_hash",
            "build_hash",
            "hash",
            "package_hash",
            "namespace",
            "version",
            "arch",
            "compiler",
            "parameters",
            "dependencies",
            "add_date",
            "modify_date",
            "label",
        )


class SpecViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Spec.objects.all()

    serializer_class = SpecSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "head"]
