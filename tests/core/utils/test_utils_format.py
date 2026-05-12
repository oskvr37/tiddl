from datetime import datetime

import pytest

from tiddl.core.utils.format import AlbumTemplate, format_template, generate_template_data
from tiddl.core.api.models.resources import Video


# Minimal Video instance used across format tests
BASE_VIDEO = Video.model_validate(
    {
        "id": 1,
        "title": "My Video",
        "volumeNumber": 1,
        "trackNumber": 1,
        "duration": 200,
        "quality": "MP4_1080P",
        "streamReady": True,
        "adSupportedStreamReady": False,
        "djReady": False,
        "stemReady": False,
        "allowStreaming": True,
        "explicit": False,
        "popularity": 10,
        "type": "Music Video",
        "adsPrePaywallOnly": False,
        "artists": [{"id": 1, "name": "Gorillaz", "type": "MAIN"}],
        "artist": {"id": 1, "name": "Gorillaz", "type": "MAIN"},
    }
)


class TestAlbumTemplateDefaults:
    def test_can_be_instantiated_with_no_args(self):
        t = AlbumTemplate()
        assert t.id == 0
        assert t.title == ""
        assert t.artist == ""
        assert t.artists == ""
        assert t.release == ""

    def test_date_defaults_to_datetime_min(self):
        assert AlbumTemplate().date == datetime.min

    def test_explicit_formats_to_empty_string(self):
        assert f"{AlbumTemplate().explicit}" == ""

    def test_master_formats_to_empty_string(self):
        assert f"{AlbumTemplate().master:MASTER}" == ""


class TestFormatTemplateNoAlbum:
    def test_album_artist_token_does_not_raise(self):
        """Default template must not raise AttributeError when album is None."""
        result = format_template(
            template="{album.artist}/{album.title}/{item.title}",
            item=BASE_VIDEO,
            album=None,
            with_asterisk_ext=False,
        )
        # album tokens render as "_" (empty string → sanitised fallback)
        assert result == "_/_/My Video"

    def test_album_title_token_does_not_raise(self):
        result = format_template(
            template="{album.title}",
            item=BASE_VIDEO,
            album=None,
            with_asterisk_ext=False,
        )
        assert result == "_"

    def test_item_title_still_rendered(self):
        result = format_template(
            template="{item.title}",
            item=BASE_VIDEO,
            album=None,
            with_asterisk_ext=False,
        )
        assert result == "My Video"

    def test_item_artist_still_rendered(self):
        result = format_template(
            template="{item.artist}",
            item=BASE_VIDEO,
            album=None,
            with_asterisk_ext=False,
        )
        assert result == "Gorillaz"


MULTI_ARTIST_VIDEO = Video.model_validate(
    {
        "id": 2,
        "title": "Collab",
        "volumeNumber": 1,
        "trackNumber": 1,
        "duration": 200,
        "quality": "MP4_1080P",
        "streamReady": True,
        "adSupportedStreamReady": False,
        "djReady": False,
        "stemReady": False,
        "allowStreaming": True,
        "explicit": False,
        "popularity": 10,
        "type": "Music Video",
        "adsPrePaywallOnly": False,
        "artists": [
            {"id": 1, "name": "Artist A", "type": "MAIN"},
            {"id": 2, "name": "Artist B", "type": "MAIN"},
        ],
        "artist": {"id": 1, "name": "Artist A", "type": "MAIN"},
    }
)


class TestListSeparator:
    def test_default_separator_in_template(self):
        result = format_template(
            template="{item.artists}",
            item=MULTI_ARTIST_VIDEO,
            album=None,
            with_asterisk_ext=False,
        )
        assert result == "Artist A; Artist B"

    def test_custom_separator_in_template(self):
        result = format_template(
            template="{item.artists}",
            item=MULTI_ARTIST_VIDEO,
            album=None,
            with_asterisk_ext=False,
            list_separator=", ",
        )
        assert result == "Artist A, Artist B"

    def test_ampersand_separator_in_template(self):
        result = format_template(
            template="{item.artists}",
            item=MULTI_ARTIST_VIDEO,
            album=None,
            with_asterisk_ext=False,
            list_separator=" & ",
        )
        assert result == "Artist A & Artist B"

    def test_separator_applied_to_features(self):
        video = Video.model_validate(
            {
                **MULTI_ARTIST_VIDEO.model_dump(),
                "artists": [
                    {"id": 1, "name": "Main", "type": "MAIN"},
                    {"id": 2, "name": "Feat A", "type": "FEATURED"},
                    {"id": 3, "name": "Feat B", "type": "FEATURED"},
                ],
            }
        )
        data = generate_template_data(item=video, list_separator=" & ")
        assert data["item"].features == "Feat A & Feat B"

    def test_separator_applied_to_artists_with_features(self):
        video = Video.model_validate(
            {
                **MULTI_ARTIST_VIDEO.model_dump(),
                "artists": [
                    {"id": 1, "name": "Main", "type": "MAIN"},
                    {"id": 2, "name": "Feat", "type": "FEATURED"},
                ],
            }
        )
        data = generate_template_data(item=video, list_separator=" / ")
        assert data["item"].artists_with_features == "Main / Feat"


class TestGenerateTemplateDataAlbumFallback:
    def test_album_template_is_never_none(self):
        """generate_template_data should always return an AlbumTemplate, never None."""
        data = generate_template_data(item=BASE_VIDEO, album=None)
        assert data["album"] is not None
        assert isinstance(data["album"], AlbumTemplate)

    def test_album_template_has_empty_fields_when_no_album(self):
        data = generate_template_data(item=BASE_VIDEO, album=None)
        album = data["album"]
        assert album.title == ""
        assert album.artist == ""
