import os
import time
import logging
from random import randint

from .api import TidalApi, ApiError
from .auth import getDeviceAuth, getToken, refreshToken
from .config import Config
from .download import downloadTrackStream, Cover
from .parser import QUALITY_ARGS, parser
from .types import TRACK_QUALITY, TrackQuality, Track
from .types.api import _PlaylistItem
from .utils import (
    RESOURCE,
    parseURL,
    formatFilename,
    loadingSymbol,
    setMetadata,
    convertFileExtension,
    initLogging,
    parseFileInput,
)

SAVE_COVER = True


def main():
    args = parser.parse_args()
    initLogging(
        silent=args.silent, verbose=args.verbose, colored_logging=not args.no_color
    )

    logger = logging.getLogger("TIDDL")
    logger.debug(args)

    config = Config()

    include_singles = args.include_singles
    download_path = args.download_path or config["settings"]["download_path"]
    track_template = args.file_template or config["settings"]["track_template"]
    track_quality = (
        QUALITY_ARGS[args.quality]
        if args.quality
        else config["settings"]["track_quality"]
    )
    file_extension = args.file_extension or config["settings"]["file_extension"]

    if args.save_options:
        logger.info("saving new settings...")
        settings = config.update(
            {
                "settings": {
                    "download_path": download_path,
                    "track_quality": track_quality,
                    "track_template": track_template,
                    "file_extension": file_extension,
                }
            }
        ).get("settings")

        if settings:
            print("Current Settings:")
            for k, v in settings.items():
                print(f'> {k.upper()} "{v}"')

        logger.info(f"saved settings to {config.config_path}")

    if not config["token"]:
        auth = getDeviceAuth()
        text = f"> go to https://{auth['verificationUriComplete']} and add device!"
        expires_at = time.time() + auth["expiresIn"]
        i = 0
        while time.time() < expires_at:
            for _ in range(50):
                loadingSymbol(i, text)
                i += 1
                time.sleep(0.1)
            token = getToken(auth["deviceCode"])

            if token.get("error"):
                continue

            print()

            config.update(
                {
                    "token": token["access_token"],
                    "refresh_token": token["refresh_token"],
                    "token_expires_at": int(time.time()) + token["expires_in"],
                    "user": {
                        "user_id": str(token["user"]["userId"]),
                        "country_code": token["user"]["countryCode"],
                    },
                }
            )
            logger.info(f"authenticated!")
            break
        else:
            logger.info("time for authentication has expired")
            return

    t_now = int(time.time())
    token_expired = t_now > config["token_expires_at"]

    if token_expired:
        token = refreshToken(config["refresh_token"])
        config.update(
            {
                "token": token["access_token"],
                "token_expires_at": int(time.time()) + token["expires_in"],
            }
        )
        logger.info(f"refreshed token!")

    time_to_expire = config["token_expires_at"] - t_now
    days, hours = time_to_expire // (24 * 3600), time_to_expire % (24 * 3600) // 3600
    days_text = f" {days} {'day' if days == 1 else 'days'}" if days else ""
    hours_text = f" {hours} {'hour' if hours == 1 else 'hours'}" if hours else ""
    logger.debug(f"token expires in{days_text}{hours_text}")

    user_inputs: list[str] = args.input

    if args.input_file:
        file_inputs = parseFileInput(args.input_file)
        user_inputs.extend(file_inputs)

    if len(user_inputs) == 0:
        logger.warning("no ID nor URL provided")
        return

    api = TidalApi(
        config["token"], config["user"]["user_id"], config["user"]["country_code"]
    )

    def downloadTrack(
        track: Track,
        file_template: str,
        skip_existing=True,
        sleep=False,
        playlist="",
        cover_data=b"",
    ) -> tuple[str, str]:
        if track.get("status") == 404:
            raise ValueError(track)

        file_dir, file_name = formatFilename(file_template, track, playlist)

        file_path = f"{download_path}/{file_dir}/{file_name}"
        if skip_existing and (
            os.path.isfile(file_path + ".m4a") or os.path.isfile(file_path + ".flac")
        ):
            logger.info(f"already exists: {file_path}")
            return file_dir, file_name

        if sleep:
            sleep_time = randint(5, 15) / 10 + 1
            logger.info(f"sleeping for {sleep_time}s")
            try:
                time.sleep(sleep_time)
            except KeyboardInterrupt:
                logger.info("stopping...")
                exit()

        stream = api.getTrackStream(track["id"], track_quality)
        logger.debug({"stream": stream})

        quality = TRACK_QUALITY[stream["audioQuality"]]

        MASTER_QUALITIES: list[TrackQuality] = ["HI_RES_LOSSLESS", "LOSSLESS"]
        if stream["audioQuality"] in MASTER_QUALITIES:
            bit_depth, sample_rate = stream.get("bitDepth"), stream.get("sampleRate")
            if bit_depth is None or sample_rate is None:
                raise ValueError(
                    "bitDepth and sampleRate must be provided for master qualities"
                )
            details = f"{bit_depth} bit {sample_rate/1000:.1f} kHz"
        else:
            details = quality["details"]

        logger.info(f"{file_name} :: {quality['name']} Quality - {details}")

        track_data, extension = downloadTrackStream(
            stream["manifest"],
            stream["manifestMimeType"],
        )

        os.makedirs(f"{download_path}/{file_dir}", exist_ok=True)

        file_path = f"{download_path}/{file_dir}/{file_name}.{extension}"

        with open(file_path, "wb+") as f:
            f.write(track_data)

        if not cover_data:
            cover = Cover(track["album"]["cover"])
            cover_data = cover.content

        setMetadata(file_path, extension, track, cover_data)

        if file_extension:
            file_path = convertFileExtension(
                source_path=file_path, file_extension=file_extension
            )

        logger.info(f"track saved as {file_path}")

        return file_dir, file_name

    def downloadAlbum(album_id: str | int, skip_existing: bool):
        album = api.getAlbum(album_id)
        logger.info(f"album: {album['title']}")

        # i dont know if limit 100 is suspicious
        # but i will leave it here
        album_items = api.getAlbumItems(album_id, limit=100)
        album_cover = Cover(album["cover"])

        for item in album_items["items"]:
            track = item["item"]

            if item["type"] != "track":
                logger.warning(f"item is not a track: {track["title"]} ({track["id"]})")
                continue

            try:
                file_dir, file_name = downloadTrack(
                    track,
                    file_template=args.file_template
                    or config["settings"]["album_template"],
                    skip_existing=skip_existing,
                    sleep=True,
                    cover_data=album_cover.content,
                )

                if SAVE_COVER:
                    album_cover.save(f"{download_path}/{file_dir}")

            except ValueError:
                logger.warning(f"track unavailable")

    skip_existing = not args.no_skip
    failed_input = []

    for user_input in user_inputs:
        input_type: RESOURCE
        input_id: str

        if user_input.isdigit():
            input_type = "track"
            input_id = user_input
        else:
            try:
                input_type, input_id = parseURL(user_input)
            except ValueError as e:
                logger.error(e)
                failed_input.append(user_input)
                continue

        match input_type:
            case "track":
                try:
                    track = api.getTrack(input_id)
                except ApiError as e:
                    logger.warning(f"{e.error['userMessage']} ({e.error['status']})")
                    continue

                downloadTrack(
                    track,
                    file_template=track_template,
                    skip_existing=skip_existing,
                )

                continue

            case "album":
                downloadAlbum(input_id, skip_existing)
                continue

            case "artist":
                all_albums = []
                artist_albums = api.getArtistAlbums(input_id)
                all_albums.extend(artist_albums["items"])

                if include_singles:
                    artist_singles = api.getArtistAlbums(input_id, onlyNonAlbum=True)
                    all_albums.extend(artist_singles["items"])

                for album in all_albums:
                    downloadAlbum(album["id"], skip_existing)

                continue

            case "playlist":
                # TODO: add option to limit and set offset of playlist ✨
                # or just make a feature in GUI that lets user choose
                # which tracks from playlist to download

                playlist = api.getPlaylist(input_id)
                logger.info(f"playlist: {playlist['title']} ({playlist['url']})")

                playlist_cover = Cover(
                    playlist["squareImage"], 1080
                )  # playlists have 1080x1080 size

                items: list[_PlaylistItem] = []
                offset = 0

                while True:
                    playlist_items = api.getPlaylistItems(input_id, offset=offset)
                    items.extend(playlist_items["items"])

                    if (
                        playlist_items["limit"] + playlist_items["offset"]
                        > playlist_items["totalNumberOfItems"]
                    ):
                        break

                    offset += playlist_items["limit"]

                for index, item in enumerate(items, 1):
                    track = item["item"]

                    track["playlistNumber"] = index
                    try:
                        file_dir, file_name = downloadTrack(
                            track,
                            file_template=args.file_template
                            or config["settings"]["playlist_template"],
                            skip_existing=skip_existing,
                            sleep=True,
                            playlist=playlist["title"],
                        )

                        if SAVE_COVER:
                            playlist_cover.save(f"{download_path}/{file_dir}")

                    except ValueError as e:
                        logger.warning(f"track unavailable")

                continue

            case _:
                logger.warning(f"invalid input: `{input_type}`")

        failed_input.append(input_id)

    if len(failed_input) > 0:
        logger.info(f"failed: {failed_input}")


if __name__ == "__main__":
    main()
