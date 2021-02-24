"""
test spackmon specs endpoints
"""

from spackmon.apps.main.models import Spec, Dependency, BuildPhase, Build
from spackmon.apps.users.models import User
from django.test import TestCase

import os
import sys

# Add spackmoncli to the path
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spackmon_dir = os.path.join(base, "script")
specs_dir = os.path.join(base, "specs")
sys.path.insert(0, spackmon_dir)


try:
    from spackmoncli import read_json, parse_auth_header, get_basic_auth
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


class SimpleTest(TestCase):
    def setUp(self):
        self.password = "bigd"
        self.headers = {}
        self.user = User.objects.create_user(
            username="dinosaur", email="dinosaur@dinosaur.com", password=self.password
        )

    def add_authentication(self, response):
        """Given a request that gets a 403 response, authenticate it."""
        assert "www-authenticate" in response._headers
        h = parse_auth_header(response._headers["www-authenticate"][1])

        self.headers.update(
            {
                "service": h.Service,
                "Accept": "application/json",
                "User-Agent": "spackmoncli",
                "HTTP_AUTHORIZATION": "Basic %s"
                % get_basic_auth(self.user.username, self.user.token),
            }
        )
        auth_response = self.client.get(h.Realm, **self.headers)
        assert auth_response.status_code == 200

        # Get the token and update headers
        info = auth_response.json()
        token = info.get("token")
        assert token

        # Update authorization headers
        self.headers["HTTP_AUTHORIZATION"] = "Bearer %s" % token

    def test_build_metadata(self):
        """Test the build endpoints, meaning updating a build, and then
        a build phase. A build generally references an entire Spec, while
        a BuildPhase is a portion of it (e.g., install).
        """

        # We have to add a spec file first to do an associated build
        spec_file = os.path.join(specs_dir, "singularity-3.6.4.json")
        spec = read_json(spec_file)

        # Add the new spec
        response = self.client.post(
            "/ms1/specs/new/", data={"spec": spec, "spack_version": "1.0.0"}
        )
        assert response.status_code == 401
        self.add_authentication(response)

        # Retry the request with auth headers
        response = self.client.post(
            "/ms1/specs/new/",
            data={"spec": spec, "spack_version": "1.0.0"},
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data.get("code") == 201
        data = data.get("data", {}).get("spec")
        full_hash = data.get("full_hash")
        singularity = Spec.objects.get(full_hash=full_hash)

        # Assert we don't have any builds
        assert Build.objects.count() == 0

        # Create the build
        response = self.client.post(
            "/ms1/builds/new/",
            data={"full_hash": full_hash, "spack_version": "1.0.0", **fake_environment},
            content_type="application/json",
            **self.headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data.get("code") == 201
        data = data.get("data", {}).get("build")
        assert data
        assert data.get("build_created", True)
        assert data.get("build_environment_created", True)
        assert data.get("spec_full_hash", full_hash)
        assert data.get("spec_name", singularity.name)
        assert data.get("build_id")

        # Assert we now have a build
        assert Build.objects.count() == 1
        build = Build.objects.first()
        assert build.status == "NOTRUN"

        # Now let's update the build to be failed - this should cancel deps
        response = self.client.post(
            "/ms1/builds/update/",
            data={"build_id": data.get("build_id"), "status": "FAILED"},
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        assert "build" in data.get("data")

        build = Build.objects.first()
        assert build.status == "FAILED"

        # Next, let's emulate updating package phases
        phases = ["autoconf", "build", "install"]
        for i, phase in enumerate(phases):
            output = "%s-output" % phase
            status = "SUCCESS"
            phase_data = {
                "status": status,
                "output": output,
                "build_id": build.id,
                "phase_name": phase,
            }

            response = self.client.post(
                "/ms1/builds/phases/update/",
                data=phase_data,
                content_type="application/json",
                **self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("code") == 200

            assert BuildPhase.objects.count() == i+1
            assert build.buildphase_set.count() == i+1
            build_phase = build.buildphase_set.get(name=phase)

            # Check that metadata was set successfully
            assert build_phase.name == phase
            assert build_phase.output == output
            assert build_phase.status == status

        # TODO: add metadata (install directory) upload, after testing with spakc
