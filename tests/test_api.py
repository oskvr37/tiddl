import unittest

from tiddl.config import Config
from tiddl.api import TidalApi


class TestApi(unittest.TestCase):
    api: TidalApi

    def setUp(self):
        config = Config()
        auth = config.config["auth"]

        token, user_id, country_code = (
            auth.get("token"),
            auth.get("user_id"),
            auth.get("country_code"),
        )

        assert token, "No token found in config file"
        assert user_id, "No user_id found in config file"
        assert country_code, "No country_code found in config file"

        self.api = TidalApi(token, user_id, country_code)

    def test_ready(self):
        session = self.api.getSession()

        self.assertEqual(session["userId"], int(self.api.user_id))
        self.assertEqual(session["countryCode"], self.api.country_code)


if __name__ == "__main__":
    unittest.main()
