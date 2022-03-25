from django.test import TestCase

class SpackMonitorTest(TestCase):

    def setUp(self):
        self.password = "bigd"
        self.headers = {}
        self.user = User.objects.create_user(
            username="dinosaur", email="dinosaur@dinosaur.com", password=self.password
        )

    def add_authentication(self, response):
        """Given a request that gets a 403 response, authenticate it."""

        assert "www-authenticate" in response.headers
        h = parse_auth_header(response.headers["www-authenticate"])

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

