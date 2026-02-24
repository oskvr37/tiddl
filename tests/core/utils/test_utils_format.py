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
