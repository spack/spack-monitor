"""
test spackmon service info
"""

from django.test import TestCase


class SimpleTest(TestCase):

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
