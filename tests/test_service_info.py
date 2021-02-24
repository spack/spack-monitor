"""
test spackmon service info
"""

from spackmon.apps.users.models import User
from django.test import TestCase

import os
import sys

# Add spackmoncli to the path
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spackmon_dir = os.path.join(base, "script")
sys.path.insert(0, spackmon_dir)

try:
    from spackmoncli import SpackMonitorClient
except ImportError:
    sys.exit(
        "Cannot import SpackMonitorClient from spackmoncli, "
        " make sure script folder is added to Python path."
    )


class SimpleTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dinosaur", email="dinosaur@dinosaur.com", password="bigd"
        )

    def test_service_info(self):
        """Test the service info endpoint"""

        print("Testing service_info endpoint /ms1/")
        service_info = self.client.get("/ms1/")
        assert service_info.status_code == 200
        data = service_info.json()
        for field in [
            "id",
            "status",
            "name",
            "description",
            "organization",
            "contactUrl",
            "documentationUrl",
            "createdAt",
            "updatedAt",
            "environment",
            "version",
            "auth_instructions_url",
        ]:
            assert field in data
