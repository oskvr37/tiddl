import unittest

from tiddl.utils import TidalResource


class TestTidalResource(unittest.TestCase):

    def test_resource_parsing(self):
        positive_cases = [
            ("https://tidal.com/browse/track/12345678", "track", "12345678"),
            ("track/12345678", "track", "12345678"),
            ("https://tidal.com/browse/album/12345678", "album", "12345678"),
            ("album/12345678", "album", "12345678"),
            ("https://tidal.com/browse/playlist/12345678", "playlist", "12345678"),
            ("playlist/12345678", "playlist", "12345678"),
            ("https://tidal.com/browse/artist/12345678", "artist", "12345678"),
            ("artist/12345678", "artist", "12345678"),
        ]

        for resource, expected_type, expected_id in positive_cases:
            with self.subTest(resource=resource):
                tidal_url = TidalResource(resource)
                self.assertEqual(tidal_url.resource_type, expected_type)
                self.assertEqual(tidal_url.resource_id, expected_id)

    def test_failing_cases(self):
        failing_cases = [
            "https://tidal.com/browse/invalid/12345678",
            "invalid/12345678",
            "https://tidal.com/browse/track/invalid",
            "track/invalid",
            "",
            "invalid",
            "https://tidal.com/browse/track/",
            "track/",
            "/12345678",
        ]

        for resource in failing_cases:
            with self.subTest(resource=resource):
                with self.assertRaises(ValueError):
                    TidalResource(resource)


if __name__ == "__main__":
    unittest.main()
