import unittest

from .utils import parseURL


class TestUtils(unittest.TestCase):

    def test_parseURL(self):
        self.assertEqual(
            parseURL("https://tidal.com/browse/track/284165609"), ("track", "284165609")
        )
        self.assertEqual(
            parseURL("https://tidal.com/browse/track/284165609/"),
            ("track", "284165609"),
        )
        self.assertEqual(
            parseURL("https://tidal.com/browse/track/284165609?u"),
            ("track", "284165609"),
        )
        self.assertEqual(
            parseURL(
                "https://listen.tidal.com/album/284165608/track/284165609",
            ),
            ("track", "284165609"),
        )

        self.assertEqual(
            parseURL("https://listen.tidal.com/album/284165608"), ("album", "284165608")
        )
        self.assertEqual(
            parseURL("https://tidal.com/browse/album/284165608"), ("album", "284165608")
        )
        self.assertEqual(
            parseURL("https://tidal.com/browse/album/284165608?u"),
            ("album", "284165608"),
        )

        self.assertEqual(
            parseURL("https://listen.tidal.com/artist/7695548"), ("artist", "7695548")
        )
        self.assertEqual(
            parseURL("https://tidal.com/browse/artist/7695548"), ("artist", "7695548")
        )

        self.assertEqual(
            parseURL(
                "https://tidal.com/browse/playlist/803be625-97e4-4cbb-88dd-43f0b1c61ed7"
            ),
            ("playlist", "803be625-97e4-4cbb-88dd-43f0b1c61ed7"),
        )
        self.assertEqual(
            parseURL(
                "https://listen.tidal.com/playlist/803be625-97e4-4cbb-88dd-43f0b1c61ed7"
            ),
            ("playlist", "803be625-97e4-4cbb-88dd-43f0b1c61ed7"),
        )

        self.assertEqual(
            parseURL(
                "https://listen.tidal.com/playlist/803be625-97e4-4cbb-88dd-43f0b1c61ed7"
            ),
            ("playlist", "803be625-97e4-4cbb-88dd-43f0b1c61ed7"),
        )

        self.assertEqual(parseURL("track/284165609"), ("track", "284165609"))
        self.assertEqual(
            parseURL("playlist/803be625-97e4-4cbb-88dd-43f0b1c61ed7"),
            ("playlist", "803be625-97e4-4cbb-88dd-43f0b1c61ed7"),
        )

        # we can also omit domain
        self.assertEqual(
            parseURL("playlist/803be625-97e4-4cbb-88dd-43f0b1c61ed7"),
            ("playlist", "803be625-97e4-4cbb-88dd-43f0b1c61ed7"),
        )

        self.assertRaises(ValueError, parseURL, "")


if __name__ == "__main__":
    unittest.main()
