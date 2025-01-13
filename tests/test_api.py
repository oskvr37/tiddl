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

        self.assertEqual(session.userId, int(self.api.user_id))
        self.assertEqual(session.countryCode, self.api.country_code)

    def test_track(self):
        track = self.api.getTrack(103805726)
        self.assertEqual(track.title, "Stronger")

    def test_artist_albums(self):
        self.api.getArtistAlbums(25022)

    def test_album(self):
        album = self.api.getAlbum(103805723)
        self.assertEqual(album.title, "Graduation")

    def test_album_items(self):
        album_items = self.api.getAlbumItems(103805723, limit=10)
        self.assertEqual(len(album_items.items), 10)

        album_items = self.api.getAlbumItems(103805723, limit=10, offset=10)
        self.assertEqual(len(album_items.items), 4)

    def test_playlist(self):
        playlist = self.api.getPlaylist("84974059-76af-406a-aede-ece2b78fa372")
        self.assertEqual(playlist.title, "Kanye West Essentials")

    def test_playlist_items(self):
        playlist_items = self.api.getPlaylistItems(
            "84974059-76af-406a-aede-ece2b78fa372"
        )
        self.assertEqual(len(playlist_items.items), 25)

    def test_favorites(self):
        favorites = self.api.getFavorites()
        self.assertGreaterEqual(len(favorites.PLAYLIST), 0)
        self.assertGreaterEqual(len(favorites.ALBUM), 0)
        self.assertGreaterEqual(len(favorites.VIDEO), 0)
        self.assertGreaterEqual(len(favorites.TRACK), 0)
        self.assertGreaterEqual(len(favorites.ARTIST), 0)

    def test_search(self):
        self.api.search("Kanye West")


if __name__ == "__main__":
    unittest.main()
