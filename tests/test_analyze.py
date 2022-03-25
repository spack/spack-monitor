"""
test spackmon analyze endpoints
"""

from spackmon.apps.main.models import (
    Spec,
    InstallFile,
    Build,
    EnvironmentVariable,
)

import os
import re
import sys

# Add spackmoncli to the path
test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, test_dir)
base = os.path.dirname(test_dir)
spackmon_dir = os.path.join(base, "script")
specs_dir = os.path.join(base, "specs")
sys.path.insert(0, spackmon_dir)

from base import SpackMonitorTest

try:
    from spackmoncli import read_json, read_file
except ImportError:
    sys.exit(
        "Cannot import functions from spackmoncli, "
        " make sure script folder is added to Python path."
    )

fake_environment = {
    "host_target": "skylake",
    "host_os": "ubuntu20.04",
    "platform": "linux",
    "hostname": "hostyhosthost",
    "kernel_version": "#73-Ubuntu SMP Mon Jan 18 17:25:17 UTC 2021",
}


def read_environment_file(filename):
    if not os.path.exists(filename):
        return
    content = read_file(filename)
    lines = re.split("(;|\n)", content)
    lines = [x for x in lines if x not in ["", "\n", ";"] and "SPACK_" in x]
    lines = [x.strip() for x in lines if "export " not in x]
    lines = [x.strip() for x in lines if "export " not in x]
    return {x.split("=", 1)[0]: x.split("=", 1)[1] for x in lines}


class SimpleTest(SpackMonitorTest):

    def test_analyze(self):
        """Test the analyze endpoints, meaning uploading metadata files
        from a package directory.
        """

        # We have to add a spec file first to do an associated build
        spec_file = os.path.join(specs_dir, "singularity-3.8.0.json")
        spec = read_json(spec_file)

        # Add the new spec
        response = self.client.post(
            "/ms1/specs/new/", data={"spec": spec["spec"], "spack_version": "1.0.0"}
        )
        assert response.status_code == 401
        self.add_authentication(response)

        # Retry the request with auth headers
        response = self.client.post(
            "/ms1/specs/new/",
            data={"spec": spec["spec"], "spack_version": "1.0.0"},
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data.get("code") == 201
        data = data.get("data", {}).get("spec")
        full_hash = data.get("full_hash")
        Spec.objects.get(full_hash=full_hash)

        # Create the build (it can be not run)
        response = self.client.post(
            "/ms1/builds/new/",
            data={"full_hash": full_hash, "spack_version": "1.0.0", **fake_environment},
            content_type="application/json",
            **self.headers
        )
        build = Build.objects.first()
        assert build.status == "NOTRUN"

        # We next want to emulate reading in environment, manifest, and
        # other data, and uploading to analyze endpoint
        # Prepare build environment data (including spack version)
        data = {"build_id": build.id}

        # Test upload of faux install directory
        meta_dir = os.path.join(base, "tests", "dummy-tar", ".spack")
        env_file = os.path.join(meta_dir, "spack-build-env.txt")
        config_file = os.path.join(meta_dir, "spack-configure-args.txt")
        manifest_file = os.path.join(meta_dir, "install_manifest.json")

        metadata = {
            "environment_variables": read_environment_file(env_file),
            "config_args": read_file(config_file),
            "install_files": read_json(manifest_file),
        }

        data["metadata"] = metadata
        response = self.client.post(
            "/ms1/analyze/builds/",
            data=data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        response = response.json()
        assert response.get("code") == 200
        assert "build" in response.get("data", {})

        # We should have created an exact number of install files
        assert len(data["metadata"]["install_files"]) == InstallFile.objects.count()
        assert (
            len(data["metadata"]["environment_variables"])
            == EnvironmentVariable.objects.count()
        )
        assert InstallFile.objects.first().build == build
