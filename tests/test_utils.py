import unittest
import json

from tiddl.models import Track
from tiddl.utils import TidalResource, formatTrack


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


class TestFormatTrack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.track = Track(
            **{
                "id": 66421438,
                "title": "Shutdown",
                "duration": 189,
                "replayGain": -9.95,
                "peak": 0.966051,
                "allowStreaming": True,
                "streamReady": True,
                "adSupportedStreamReady": True,
                "djReady": True,
                "stemReady": False,
                "streamStartDate": "2016-11-15T00:00:00.000+0000",
                "premiumStreamingOnly": False,
                "trackNumber": 9,
                "volumeNumber": 1,
                "version": None,
                "popularity": 24,
                "copyright": "(P) 2016 Boy Better Know",
                "bpm": 69,
                "url": "http://www.tidal.com/track/66421438",
                "isrc": "GB7QY1500024",
                "editable": False,
                "explicit": True,
                "audioQuality": "LOSSLESS",
                "audioModes": ["STEREO"],
                "mediaMetadata": {"tags": ["LOSSLESS", "HIRES_LOSSLESS"]},
                "artist": {
                    "id": 3566984,
                    "name": "Skepta",
                    "type": "MAIN",
                    "picture": "747af850-fa9c-4178-a3e6-49259b67df86",
                },
                "artists": [
                    {
                        "id": 3566984,
                        "name": "Skepta",
                        "type": "MAIN",
                        "picture": "747af850-fa9c-4178-a3e6-49259b67df86",
                    }
                ],
                "album": {
                    "id": 66421429,
                    "title": "Konnichiwa",
                    "cover": "e0c2f05e-e21f-47c5-9c37-2993437df27d",
                    "vibrantColor": "#ae3b31",
                    "videoCover": None,
                },
                "mixes": {"TRACK_MIX": "001aa4abeb471e8f55f5784772b478"},
                "playlistNumber": None,
            }
        )

    def test_templating(self):
        test_cases = [
            ("{id}", "66421438"),
            ("{title}", "Shutdown"),
            ("{version}", ""),
            ("{artist}", "Skepta"),
            ("{artists}", "Skepta"),
            ("{album}", "Konnichiwa"),
            ("{number}", "9"),
            ("{disc}", "1"),
            ("{date}", "11-15-16"),
            ("{year}", "2016"),
            ("{playlist_number}", ""),
            ("{bpm}", "69"),
            ("{quality}", "high"),
            ("{artist}/{album}/{title}", "Skepta/Konnichiwa/Shutdown"),
        ]

        for template, expected_result in test_cases:
            result = formatTrack(template, self.track)
            self.assertEqual(result, expected_result)

    def test_invalid_characters(self):
        test_cases = [
            "\\",
            ":",
            '"',
            "?",
            "<",
            ">",
            "|",
        ]

        for template in test_cases:
            with self.subTest(template=template):
                with self.assertRaises(ValueError):
                    formatTrack(template, self.track)


if __name__ == "__main__":
    unittest.main()
