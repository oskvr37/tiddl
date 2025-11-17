import pytest
from tiddl.cli.utils.resource import TidalResource, ResourceTypeLiteral

valid_test_data = [
    ("track", "12345"),
    ("album", "98765"),
    ("video", "11111"),
    ("artist", "22222"),
    ("playlist", "abcde"),
    ("mix", "xyz123"),
]


@pytest.mark.parametrize("resource_type, resource_id", valid_test_data)
def test_tidalresource_from_string_shorthand(
    resource_type: ResourceTypeLiteral, resource_id: str
):
    string = f"{resource_type}/{resource_id}"
    res = TidalResource.from_string(string)

    assert res.type == resource_type
    assert res.id == resource_id
    assert str(res) == string
    assert res.url == f"https://listen.tidal.com/{resource_type}/{resource_id}"


@pytest.mark.parametrize("resource_type, resource_id", valid_test_data)
def test_tidalresource_from_string_url(
    resource_type: ResourceTypeLiteral, resource_id: str
):
    url = f"https://listen.tidal.com/{resource_type}/{resource_id}"
    res = TidalResource.from_string(url)

    assert res.type == resource_type
    assert res.id == resource_id
    assert str(res) == f"{resource_type}/{resource_id}"
    assert res.url == url


def test_from_string_invalid_type():
    with pytest.raises(ValueError, match="Invalid resource type"):
        TidalResource.from_string("invalid/123")


invalid_test_data = [
    ("track", "abc"),
    ("album", "xyz"),
    ("video", "id123"),
    ("artist", "user1"),
]


@pytest.mark.parametrize("resource_type, invalid_id", invalid_test_data)
def test_from_string_invalid_digit_id(
    resource_type: ResourceTypeLiteral, invalid_id: str
):
    with pytest.raises(ValueError, match="Invalid resource id"):
        TidalResource.from_string(f"{resource_type}/{invalid_id}")


urls_data = [
    ("https://tidal.com/album/321", "album", "321"),
    ("https://tidal.com/album/321/", "album", "321"),
    ("https://tidal.com/album/321/u", "album", "321"),
    ("https://listen.tidal.com/track/12345", "track", "12345"),
    ("https://listen.tidal.com/track/12345/", "track", "12345"),
    ("https://listen.tidal.com/track/12345/u", "track", "12345"),
]


@pytest.mark.parametrize("url, resource_type, resource_id", urls_data)
def test_url_fromstring(url: str, resource_type: str, resource_id: str):
    res = TidalResource.from_string(url)
    assert res.type == resource_type
    assert res.id == resource_id


def test_url_property():
    res = TidalResource(type="track", id="12345")
    assert res.url == "https://listen.tidal.com/track/12345"


def test_str_method():
    res = TidalResource(type="album", id="67890")
    assert str(res) == "album/67890"
