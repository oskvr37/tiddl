import pytest
from pytest_mock import MockerFixture, MockType

from tiddl.core.api.api import (
    TidalAPI,
    TidalClient,
    Limits,
    DO_NOT_CACHE,
    EXPIRE_IMMEDIATELY,
)

from tiddl.core.api.models import (
    Album,
    Artist,
    Playlist,
    Track,
    Video,
    AlbumItems,
    AlbumItemsCredits,
    ArtistAlbumsItems,
    Favorites,
    TrackLyrics,
    PlaylistItems,
    MixItems,
    Search,
    SessionResponse,
    TrackStream,
    VideoStream,
)


def test_tidal_api_init(mocker: MockerFixture):
    mock_client = mocker.Mock(spec=TidalClient)

    api = TidalAPI(client=mock_client, user_id="u123", country_code="US")

    assert api.client is mock_client
    assert api.user_id == "u123"
    assert api.country_code == "US"


@pytest.fixture
def mock_client(mocker: MockerFixture):
    return mocker.Mock(spec=TidalClient)


@pytest.fixture
def api(mock_client: MockType):
    return TidalAPI(client=mock_client, user_id="u123", country_code="US")


def test_get_album(api: TidalAPI, mock_client: MockType):
    api.get_album(album_id=1)

    mock_client.fetch.assert_called_once_with(
        Album, "albums/1", {"countryCode": "US"}, expire_after=3600
    )


def test_get_album_items(api: TidalAPI, mock_client: MockType):
    api.get_album_items(1)
    mock_client.fetch.assert_called_once_with(
        AlbumItems,
        "albums/1/items",
        {"countryCode": "US", "limit": Limits.ALBUM_ITEMS, "offset": 0},
        expire_after=3600,
    )


def test_get_album_items_credits(api: TidalAPI, mock_client: MockType):
    api.get_album_items_credits(1)
    mock_client.fetch.assert_called_once_with(
        AlbumItemsCredits,
        "albums/1/items/credits",
        {"countryCode": "US", "limit": Limits.ALBUM_ITEMS, "offset": 0},
        expire_after=3600,
    )


def test_get_artist(api: TidalAPI, mock_client: MockType):
    api.get_artist(1)
    mock_client.fetch.assert_called_once_with(
        Artist, "artists/1", {"countryCode": "US"}, expire_after=3600
    )


def test_get_artist_albums(api: TidalAPI, mock_client: MockType):
    api.get_artist_albums(1)
    mock_client.fetch.assert_called_once_with(
        ArtistAlbumsItems,
        "artists/1/albums",
        {
            "countryCode": "US",
            "limit": Limits.ARTIST_ALBUMS,
            "offset": 0,
            "filter": "ALBUMS",
        },
        expire_after=3600,
    )


def test_get_mix(api: TidalAPI, mock_client: MockType):
    api.get_mix_items("abcd-1234")
    mock_client.fetch.assert_called_once_with(
        MixItems,
        "mixes/abcd-1234/items",
        {"countryCode": "US", "limit": Limits.MIX_ITEMS, "offset": 0},
        expire_after=3600,
    )


def test_get_favorites(api: TidalAPI, mock_client: MockType):
    api.get_favorites()
    mock_client.fetch.assert_called_once_with(
        Favorites,
        "users/u123/favorites/ids",
        {"countryCode": "US"},
        expire_after=EXPIRE_IMMEDIATELY,
    )


def test_get_playlist(api: TidalAPI, mock_client: MockType):
    api.get_playlist("uuid")
    mock_client.fetch.assert_called_once_with(
        Playlist,
        "playlists/uuid",
        {"countryCode": "US"},
        expire_after=EXPIRE_IMMEDIATELY,
    )


def test_get_playlist_items(api: TidalAPI, mock_client: MockType):
    api.get_playlist_items("uuid")
    mock_client.fetch.assert_called_once_with(
        PlaylistItems,
        "playlists/uuid/items",
        {"countryCode": "US", "limit": Limits.PLAYLIST_ITEMS, "offset": 0},
        expire_after=EXPIRE_IMMEDIATELY,
    )


def test_get_search(api: TidalAPI, mock_client: MockType):
    api.get_search("query")
    mock_client.fetch.assert_called_once_with(
        Search,
        "search",
        {"countryCode": "US", "query": "query"},
        expire_after=DO_NOT_CACHE,
    )


def test_get_session(api: TidalAPI, mock_client: MockType):
    api.get_session()
    mock_client.fetch.assert_called_once_with(
        SessionResponse, "sessions", expire_after=DO_NOT_CACHE
    )


def test_get_track_lyrics(api: TidalAPI, mock_client: MockType):
    api.get_track_lyrics(1)
    mock_client.fetch.assert_called_once_with(
        TrackLyrics,
        "tracks/1/lyrics",
        {"countryCode": "US"},
        expire_after=3600,
    )


def test_get_track(api: TidalAPI, mock_client: MockType):
    api.get_track(1)
    mock_client.fetch.assert_called_once_with(
        Track,
        "tracks/1",
        {"countryCode": "US"},
        expire_after=3600,
    )


def test_get_track_stream(api: TidalAPI, mock_client: MockType):
    api.get_track_stream(1, "HIGH")
    mock_client.fetch.assert_called_once_with(
        TrackStream,
        "tracks/1/playbackinfopostpaywall",
        {"audioquality": "HIGH", "playbackmode": "STREAM", "assetpresentation": "FULL"},
        expire_after=DO_NOT_CACHE,
    )


def test_get_video(api: TidalAPI, mock_client: MockType):
    api.get_video(1)
    mock_client.fetch.assert_called_once_with(
        Video,
        "videos/1",
        {"countryCode": "US"},
        expire_after=3600,
    )


def test_get_video_stream(api: TidalAPI, mock_client: MockType):
    api.get_video_stream(1, "HIGH")
    mock_client.fetch.assert_called_once_with(
        VideoStream,
        "videos/1/playbackinfopostpaywall",
        {"videoquality": "HIGH", "playbackmode": "STREAM", "assetpresentation": "FULL"},
        expire_after=DO_NOT_CACHE,
    )
