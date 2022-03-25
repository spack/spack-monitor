"""
test spackmon specs endpoints
"""

from spackmon.apps.main.models import Spec

import os
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
    from spackmoncli import read_json, parse_auth_header, get_basic_auth
except ImportError:
    sys.exit(
        "Cannot import functions from spackmoncli, "
        " make sure script folder is added to Python path."
    )


class SimpleTest(SpackMonitorTest):

    def test_new_spec(self):
        """Test the new spec endpoint. This also tests the auth workflow"""

        print("Testing NewSpec endpoint /ms1/specs/new/")
        spec_file = os.path.join(specs_dir, "singularity-3.8.0.json")
        spec = read_json(spec_file)

        # First attempt without user token should fail
        response = self.client.post(
            "/ms1/specs/new/", data={"spec": spec["spec"], "spack_version": "1.0.0"}
        )
        assert response.status_code == 401

        # And provide a www-authenticate header
        assert "www-authenticate" in response.headers
        h = parse_auth_header(response.headers["www-authenticate"])

        assert h.Realm == "http://testserver/auth/token/"
        assert h.Scope == "build"
        assert h.Service == "http://testserver"

        # Prepare request to retry
        headers = {
            "service": h.Service,
            "Accept": "application/json",
            "User-Agent": "spackmoncli",
            "HTTP_AUTHORIZATION": "Basic %s"
            % get_basic_auth(self.user.username, self.user.token),
        }

        auth_response = self.client.get(h.Realm, **headers)

        assert auth_response.status_code == 200

        # Request the token
        info = auth_response.json()
        token = info.get("token")
        assert token

        # Update authorization headers
        headers["HTTP_AUTHORIZATION"] = "Bearer %s" % token

        # Make sure we have no specs
        assert Spec.objects.count() == 0

        # Retry the request with auth headers
        response = self.client.post(
            "/ms1/specs/new/",
            data={"spec": spec["spec"], "spack_version": "1.0.0"},
            content_type="application/json",
            **headers
        )

        # Was created response is 201
        assert response.status_code == 201
        data = response.json()

        # Check the format of the response
        assert data.get("message") == "success"
        assert data.get("code") == 201

        data = data.get("data")
        assert data.get("created") == True

        # The spec is a field of the data
        data = data.get("spec")
        assert data

        # Check the response object
        assert data.get("full_hash") == "36u22fm5i3w2tqyiyje22j6x55emekjw"
        assert data.get("name") == "singularity"
        assert data.get("version") == "3.8.0"
        assert data.get("spack_version") == "1.0.0"

        specs = data.get("specs")
        assert specs

        # We should have created one spec
        singularity = Spec.objects.get(full_hash=data.get("full_hash"))

        # The list of depdencies should match what is created
        assert singularity.dependencies.count() == len(specs)
        for dep in singularity.dependencies.all():
            assert dep.spec.full_hash in list(specs.values())

        # We should be able to retrieve specs by
        hashes = set()
        hashes.add(data.get("full_hash"))
        for spec_name, spec_hash in specs.items():
            Spec.objects.get(full_hash=spec_hash)
            hashes.add(spec_hash)

        # A second response should indicate it already exists (200)
        response = self.client.post(
            "/ms1/specs/new/",
            data={"spec": spec["spec"], "spack_version": "1.0.0"},
            content_type="application/json",
            **headers
        )
        assert response.status_code == 200
