import unittest

from .utils import parseURL, formatFilename
from .types.track import Track


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

    def test_formatFilename(self):
        track: Track = {
            "id": 133017101,
            "title": "HAUTE COUTURE",
            "duration": 243,
            "replayGain": -7.7,
            "peak": 0.944031,
            "allowStreaming": True,
            "streamReady": True,
            "adSupportedStreamReady": True,
            "djReady": True,
            "stemReady": False,
            "streamStartDate": "2020-03-05T00:00:00.000+0000",
            "premiumStreamingOnly": False,
            "trackNumber": 1,
            "volumeNumber": 1,
            "version": None,
            "popularity": 29,
            "copyright": "2020 TUZZA Globale",
            "bpm": None,
            "url": "http://www.tidal.com/track/133017101",
            "isrc": "PL70D1900060",
            "editable": False,
            "explicit": False,
            "audioQuality": "LOSSLESS",
            "audioModes": ["STEREO"],
            "mediaMetadata": {"tags": ["LOSSLESS"]},
            "artist": {
                "id": 9550100,
                "name": "Tuzza Globale",
                "type": "MAIN",
                "picture": "125c9343-3257-407a-8285-5e9f1d283a2e",
            },
            "artists": [
                {
                    "id": 9550100,
                    "name": "Tuzza Globale",
                    "type": "MAIN",
                    "picture": "125c9343-3257-407a-8285-5e9f1d283a2e",
                },
                {
                    "id": 6847736,
                    "name": "Taco Hemingway",
                    "type": "FEATURED",
                    "picture": "7a1f5193-5d96-452c-b8dd-5ff0f81d5335",
                },
            ],
            "album": {
                "id": 133017100,
                "title": "HAUTE COUTURE",
                "cover": "efd381c2-a982-4d09-bb15-da872006cadf",
                "vibrantColor": "#f6a285",
                "videoCover": None,
            },
            "mixes": {"TRACK_MIX": "001ec78dae0d4a470999adefffd570"},
        }

        self.assertEqual(formatFilename("{title}", track), "HAUTE COUTURE")
        self.assertEqual(
            formatFilename("{artist} - {title}", track), "Tuzza Globale - HAUTE COUTURE"
        )
        self.assertEqual(
            formatFilename("{album} - {title}", track),
            "HAUTE COUTURE - HAUTE COUTURE",
        )
        self.assertEqual(
            formatFilename("{number}. {title}", track),
            "1. HAUTE COUTURE",
        )
        self.assertEqual(
            formatFilename("{artists} - {title}", track),
            "Tuzza Globale, Taco Hemingway - HAUTE COUTURE",
        )
        self.assertEqual(
            formatFilename("{id}", track),
            "133017101",
        )


if __name__ == "__main__":
    unittest.main()
