import os
import typer
import asyncio

from pathlib import Path
from logging import getLogger
from rich.live import Live

from typing_extensions import Annotated

from tiddl.core.metadata import add_track_metadata, add_video_metadata, Cover
from tiddl.core.api import ApiError
from tiddl.core.api.models import Album, Track, Video, AlbumItemsCredits
from tiddl.core.utils.format import format_template
from tiddl.core.utils.m3u import save_tracks_to_m3u
from tiddl.cli.config import (
    CONFIG,
    TRACK_QUALITY_LITERAL,
    VIDEO_QUALITY_LITERAL,
    ARTIST_SINGLES_FILTER_LITERAL,
    VALID_M3U_RESOURCE_LITERAL,
    VIDEOS_FILTER_LITERAL,
)
from tiddl.cli.utils.resource import TidalResource
from tiddl.cli.ctx import Context
from tiddl.cli.commands.auth import refresh
from tiddl.cli.commands.subcommands import register_subcommands


from .downloader import Downloader
from .output import RichOutput

download_command = typer.Typer(name="download")
register_subcommands(download_command)

log = getLogger(__name__)


@download_command.callback(no_args_is_help=True)
def download_callback(
    ctx: Context,
    TRACK_QUALITY: Annotated[
        TRACK_QUALITY_LITERAL,
        typer.Option(
            "--track-quality",
            "-q",
        ),
    ] = CONFIG.download.track_quality,
    VIDEO_QUALITY: Annotated[
        VIDEO_QUALITY_LITERAL,
        typer.Option(
            "--video-quality",
            "-vq",
        ),
    ] = CONFIG.download.video_quality,
    SKIP_EXISTING: Annotated[
        bool,
        typer.Option(
            "--no-skip",
            "-ns",
            help="Don't skip downloading existing files.",
        ),
    ] = not CONFIG.download.skip_existing,
    REWRITE_METADATA: Annotated[
        bool,
        typer.Option(
            "--rewrite-metadata",
            "-r",
            help="Rewrite metadata for already downloaded tracks.",
        ),
    ] = CONFIG.download.rewrite_metadata,
    THREADS_COUNT: Annotated[
        int,
        typer.Option(
            "--threads-count",
            "-t",
            help="Number of concurrent download threads.",
            min=1,
        ),
    ] = CONFIG.download.threads_count,
    DOWNLOAD_PATH: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Base directory path for all downloads.",
        ),
    ] = CONFIG.download.download_path,
    SCAN_PATH: Annotated[
        Path,
        typer.Option(
            "--scan-path",
            "--sp",
            help="Directory to search for your existing downloads.",
        ),
    ] = CONFIG.download.scan_path,
    TEMPLATE: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Format output file template.",
        ),
    ] = "",
    SINGLES_FILTER: Annotated[
        ARTIST_SINGLES_FILTER_LITERAL,
        typer.Option(
            "--singles",
            "-s",
            help="Filter for including artists' singles, used while downloading artist.",
        ),
    ] = CONFIG.download.singles_filter,
    VIDEOS_FILTER: Annotated[
        VIDEOS_FILTER_LITERAL,
        typer.Option(
            "--videos",
            "-vid",
            help="Videos handling: 'none' to exclude, 'allow' to include, 'only' to download videos only.",
        ),
    ] = CONFIG.download.videos_filter,
    SKIP_ERRORS: Annotated[
        bool,
        typer.Option(
            "--skip-errors",
            "-se",
            help="Skip unavailable items and continue downloading the rest.",
        ),
    ] = CONFIG.download.skip_errors,
    DISABLE_LIVE: Annotated[
        bool,
        typer.Option(
            "--disable-live",
            "-dl",
            help="Disable Rich Live display, useful for debugging with breakpoint().",
        ),
    ] = CONFIG.download.disable_live,
    SKIP_UNAVAILABLE_TRACKS: Annotated[
        bool,
        typer.Option(
            "--skip-unavailable-tracks",
            "-sut",
            help="Skip tracks that are unavailable (no ISRC) instead of attempting to download them.",
        ),
    ] = CONFIG.download.skip_unavailable_tracks,
):
    """
    Download Tidal resources.
    """

    ctx.invoke(refresh, EARLY_EXPIRE_TIME=600)

    log.debug(f"{ctx.params=}")

    def save_m3u(
        resource_type: VALID_M3U_RESOURCE_LITERAL,
        filename: str,
        tracks_with_path: list[tuple[Path, Track]],
    ):
        if not CONFIG.m3u.save:
            return

        if resource_type not in CONFIG.m3u.allowed:
            return

        tracks_with_existing_paths = [
            (path, track)
            for (path, track) in tracks_with_path
            if path and isinstance(track, Track)
        ]

        log.debug(f"{resource_type=}, {filename=}, {len(tracks_with_existing_paths)=}")

        save_tracks_to_m3u(
            tracks_with_path=tracks_with_existing_paths, path=DOWNLOAD_PATH / filename
        )

    def get_item_quality(item: Track | Video):
        def predict_item_quality() -> TRACK_QUALITY_LITERAL | VIDEO_QUALITY_LITERAL:
            if isinstance(item, Track):
                if TRACK_QUALITY in ["low", "normal"]:
                    return TRACK_QUALITY

                if (
                    TRACK_QUALITY == "max"
                    and "HIRES_LOSSLESS" not in item.mediaMetadata.tags
                ):
                    return "high"

                return TRACK_QUALITY

            elif isinstance(item, Video):
                # TODO add missing Video.quality literals so this function can work properly
                return VIDEO_QUALITY

            raise TypeError("Unsupported item type")

        return predict_item_quality().upper()

    async def download_resources():
        rich_output = RichOutput(ctx.obj.console)

        downloader = Downloader(
            tidal_api=ctx.obj.api,
            threads_count=THREADS_COUNT,
            rich_output=rich_output,
            track_quality=TRACK_QUALITY,
            video_quality=VIDEO_QUALITY,
            videos_filter=VIDEOS_FILTER,
            skip_existing=not SKIP_EXISTING,
            download_path=DOWNLOAD_PATH,
            scan_path=SCAN_PATH,
        )

        class Metadata:
            def __init__(
                self,
                date: str = "",
                artist: str = "",
                credits: list[AlbumItemsCredits.ItemWithCredits.CreditsEntry] = [],
                cover: Cover | None = None,
                album_review: str = "",
            ) -> None:
                self.date = date
                self.artist = artist
                self.credits = credits
                self.cover = cover
                self.album_review = album_review

        async def handle_resource(resource: TidalResource):
            async def handle_item(
                item: Track | Video,
                file_path: str,
                track_metadata: Metadata | None = None,
            ) -> tuple[Path | None, Track | Video]:
                log.debug(f"{item.id=}, {file_path=}")
                rich_output.total_increment()

                if not track_metadata:
                    track_metadata = Metadata()

                download_path, was_downloaded = await downloader.download(
                    item=item, file_path=Path(file_path)
                )

                log.debug(f"{download_path=}, {was_downloaded=}")

                if (
                    CONFIG.metadata.enable
                    and download_path
                    # rewrite metadata when track was skipped due to already existing
                    and (REWRITE_METADATA or was_downloaded)
                ):
                    if isinstance(item, Track):
                        lyrics_subtitles = ""

                        if CONFIG.metadata.lyrics:
                            try:
                                lyrics_subtitles = ctx.obj.api.get_track_lyrics(
                                    item.id
                                ).subtitles
                            except Exception as e:
                                log.error(e)

                        if (
                            not track_metadata.cover
                            and item.album.cover
                            and CONFIG.metadata.cover
                        ):
                            track_metadata.cover = Cover(item.album.cover)

                        if track_metadata.cover and track_metadata.cover.data is None:
                            track_metadata.cover.fetch_data()

                        add_track_metadata(
                            path=download_path,
                            track=item,
                            lyrics=lyrics_subtitles,
                            album_artist=track_metadata.artist,
                            cover_data=(
                                track_metadata.cover.data
                                if track_metadata.cover
                                else None
                            ),
                            date=track_metadata.date,
                            credits_contributors=track_metadata.credits,
                            comment=track_metadata.album_review,
                        )

                    elif isinstance(item, Video):
                        add_video_metadata(path=download_path, video=item)

                if download_path and CONFIG.download.update_mtime:
                    try:
                        os.utime(download_path, None)
                    except Exception:
                        log.warning(f"could not update mtime for {download_path}")

                return download_path, item

            async def download_album(album: Album):
                offset = 0
                futures = []

                cover: Cover | None = None
                save_cover = ("album" in CONFIG.cover.allowed) and CONFIG.cover.save

                if album.cover and (CONFIG.metadata.cover or save_cover):
                    cover = Cover(album.cover, size=CONFIG.cover.size)

                album_review = ""

                if CONFIG.metadata.album_review:
                    try:
                        album_review = ctx.obj.api.get_album_review(
                            album_id=resource.id
                        ).normalized_text()
                    except Exception as e:
                        log.error(e)

                while True:
                    album_items = ctx.obj.api.get_album_items_credits(
                        album_id=album.id, offset=offset
                    )

                    for album_item in album_items.items:
                        try:
                            template = TEMPLATE or CONFIG.templates.album
                            file_path = format_template(
                                template=template,
                                item=album_item.item,
                                album=album,
                                quality=get_item_quality(album_item.item),
                            )

                        except AttributeError as exc:
                            log.error(f"{exc=}")
                            ctx.obj.console.print(
                                f"[red]Wrong Album Template:[/] {exc} ({template=}, {album.id=}, {album_item.item.id=})"
                            )
                            continue

                        try:
                            futures.append(
                                handle_item(
                                    item=album_item.item,
                                    file_path=file_path,
                                    track_metadata=Metadata(
                                        cover=cover,
                                        date=str(album.releaseDate),
                                        artist=album.artist.name if album.artist else "",
                                        credits=album_item.credits,
                                        album_review=album_review,
                                    ),
                                )
                            )
                        except ApiError as e:
                            item = album_item.item
                            track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                            if hasattr(item, 'album') and item.album:
                                track_info += f", Album ID: {item.album.id}"
                            ctx.obj.console.print(f"[red]API Error:[/] {e} ({track_info})")
                            if not SKIP_ERRORS:
                                raise
                        except Exception as e:
                            item = album_item.item
                            track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                            ctx.obj.console.print(f"[red]Error:[/] {e} ({track_info})")
                            if not SKIP_ERRORS:
                                raise

                    offset += album_items.limit
                    if offset >= album_items.totalNumberOfItems:
                        break

                tracks_with_path = await asyncio.gather(*futures)

                save_m3u(
                    resource_type="album",
                    filename=format_template(
                        CONFIG.m3u.templates.album,
                        album=album,
                        type="album",
                    ),
                    tracks_with_path=tracks_with_path,
                )

                if save_cover and cover:
                    cover.save_to_directory(
                        path=DOWNLOAD_PATH
                        / format_template(
                            template=CONFIG.cover.templates.album, album=album
                        )
                    )

            # resources should be collected from a distinct function
            # that would yield the resources.
            # then we would be able to reuse the logic in the export command

            match resource.type:

                case "track":
                    track = ctx.obj.api.get_track(resource.id)
                    album = ctx.obj.api.get_album(track.album.id)

                    await handle_item(
                        item=track,
                        file_path=format_template(
                            template=TEMPLATE or CONFIG.templates.track,
                            item=track,
                            album=album,
                            quality=get_item_quality(track),
                        ),
                    )

                    if (
                        CONFIG.cover.save
                        and ("track" in CONFIG.cover.allowed)
                        and track.album.cover
                    ):
                        Cover(
                            track.album.cover, size=CONFIG.cover.size
                        ).save_to_directory(
                            path=DOWNLOAD_PATH
                            / format_template(
                                CONFIG.cover.templates.track, item=track, album=album
                            )
                        )

                case "video":
                    video = ctx.obj.api.get_video(resource.id)
                    template = TEMPLATE or CONFIG.templates.video

                    if "{album" in template and video.album:
                        album = ctx.obj.api.get_album(video.album.id)
                    else:
                        album = None

                    await handle_item(
                        item=video,
                        file_path=format_template(
                            template=template,
                            item=video,
                            album=album,
                            quality=get_item_quality(video),
                        ),
                    )

                case "mix":
                    offset = 0
                    futures = []

                    while True:
                        mix_items = ctx.obj.api.get_mix_items(resource.id, offset=0, skip_unavailable_tracks=SKIP_UNAVAILABLE_TRACKS)

                        for mix_item in mix_items.items:
                            template = TEMPLATE or CONFIG.templates.mix

                            try:
                                if "{album" in template:
                                    album = ctx.obj.api.get_album(
                                        mix_item.item.album.id
                                    )
                                else:
                                    album = None

                                futures.append(
                                    handle_item(
                                        item=mix_item.item,
                                        file_path=format_template(
                                            template=template,
                                            item=mix_item.item,
                                            album=album,
                                            mix_id=resource.id,
                                            quality=get_item_quality(mix_item.item),
                                        ),
                                    )
                                )
                            except ApiError as e:
                                item = mix_item.item
                                track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                                ctx.obj.console.print(f"[red]API Error:[/] {e} ({track_info})")
                                if not SKIP_ERRORS:
                                    raise
                            except Exception as e:
                                item = mix_item.item
                                track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                                ctx.obj.console.print(f"[red]Error:[/] {e} ({track_info})")
                                if not SKIP_ERRORS:
                                    raise

                        offset += mix_items.limit
                        if offset >= mix_items.totalNumberOfItems:
                            break

                    tracks_with_path = await asyncio.gather(*futures)

                    save_m3u(
                        resource_type="mix",
                        filename=format_template(
                            CONFIG.m3u.templates.mix,
                            mix_id=resource.id,
                            type="mix",
                        ),
                        tracks_with_path=tracks_with_path,
                    )

                case "album":
                    album = ctx.obj.api.get_album(album_id=resource.id)
                    await download_album(album)

                case "artist":
                    futures = []

                    async def safe_download_album(album: Album):
                        try:
                            await download_album(album)
                        except ApiError as e:
                            ctx.obj.console.print(f"[red]API Error:[/] {e} (Album: {album.title}, ID: {album.id})")
                            if not SKIP_ERRORS:
                                raise
                        except Exception as e:
                            ctx.obj.console.print(f"[red]Error:[/] {e} (Album: {album.title}, ID: {album.id})")
                            if not SKIP_ERRORS:
                                raise

                    def get_all_albums(singles: bool):
                        offset = 0

                        while True:
                            artist_albums = ctx.obj.api.get_artist_albums(
                                artist_id=resource.id,
                                offset=offset,
                                filter="EPSANDSINGLES" if singles else "ALBUMS",
                            )

                            for album in artist_albums.items:
                                futures.append(safe_download_album(album))

                            offset += artist_albums.limit
                            if offset >= artist_albums.totalNumberOfItems:
                                break

                    def get_all_videos():
                        offset = 0

                        while True:
                            artist_videos = ctx.obj.api.get_artist_videos(
                                resource.id, offset=offset
                            )

                            for video in artist_videos.items:
                                template = TEMPLATE or CONFIG.templates.video

                                try:
                                    if "{album" in template and video.album:
                                        album = ctx.obj.api.get_album(video.album.id)
                                    else:
                                        album = None

                                    futures.append(
                                        handle_item(
                                            item=video,
                                            file_path=format_template(
                                                template=template,
                                                item=video,
                                                album=album,
                                                quality=get_item_quality(video),
                                            ),
                                        )
                                    )
                                except ApiError as e:
                                    ctx.obj.console.print(f"[red]API Error:[/] {e} (Video: {video.title}, ID: {video.id})")
                                    if not SKIP_ERRORS:
                                        raise
                                except Exception as e:
                                    ctx.obj.console.print(f"[red]Error:[/] {e} (Video: {video.title}, ID: {video.id})")
                                    if not SKIP_ERRORS:
                                        raise

                            if offset > artist_videos.totalNumberOfItems:
                                break

                            offset += artist_videos.limit

                    if VIDEOS_FILTER != "none":
                        get_all_videos()

                    if VIDEOS_FILTER != "only":
                        if SINGLES_FILTER == "include":
                            get_all_albums(False)
                            get_all_albums(True)
                        else:
                            get_all_albums(SINGLES_FILTER == "only")

                    await asyncio.gather(*futures)

                case "playlist":
                    offset = 0
                    futures = []
                    playlist_index = 0
                    playlist = ctx.obj.api.get_playlist(playlist_uuid=resource.id)

                    while True:
                        playlist_items = ctx.obj.api.get_playlist_items(
                            playlist_uuid=resource.id, offset=offset, skip_unavailable_tracks=SKIP_UNAVAILABLE_TRACKS
                        )

                        for playlist_item in playlist_items.items:
                            playlist_index += 1
                            template = TEMPLATE or CONFIG.templates.playlist

                            try:
                                if "{album" in template:
                                    album = ctx.obj.api.get_album(
                                        playlist_item.item.album.id
                                    )
                                else:
                                    album = None

                                futures.append(
                                    handle_item(
                                        item=playlist_item.item,
                                        file_path=format_template(
                                            template=template,
                                            item=playlist_item.item,
                                            album=album,
                                            playlist=playlist,
                                            playlist_index=playlist_index,
                                            quality=get_item_quality(playlist_item.item),
                                        ),
                                        track_metadata=Metadata(),
                                    )
                                )
                            except ApiError as e:
                                item = playlist_item.item
                                track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                                if hasattr(item, 'album') and item.album:
                                    track_info += f", Album ID: {item.album.id}"
                                ctx.obj.console.print(f"[red]API Error:[/] {e} ({track_info})")
                                if not SKIP_ERRORS:
                                    raise
                            except Exception as e:
                                item = playlist_item.item
                                track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                                ctx.obj.console.print(f"[red]Error:[/] {e} ({track_info})")
                                if not SKIP_ERRORS:
                                    raise

                        offset += playlist_items.limit
                        if offset >= playlist_items.totalNumberOfItems:
                            break

                    tracks_with_path = await asyncio.gather(*futures)

                    save_m3u(
                        resource_type="playlist",
                        filename=format_template(
                            CONFIG.m3u.templates.playlist,
                            playlist=playlist,
                            type="playlist",
                        ),
                        tracks_with_path=tracks_with_path,
                    )

                    if (
                        CONFIG.cover.save
                        and ("playlist" in CONFIG.cover.allowed)
                        and playlist.squareImage
                    ):
                        Cover(
                            playlist.squareImage, size=max(CONFIG.cover.size, 1080)
                        ).save_to_directory(
                            path=DOWNLOAD_PATH
                            / format_template(
                                template=CONFIG.cover.templates.playlist,
                                playlist=playlist,
                            )
                        )

        with Live(
            rich_output.group,
            refresh_per_second=10,
            console=ctx.obj.console,
            transient=True,
        ):

            async def wrapper(r: TidalResource):
                try:
                    await handle_resource(r)
                except ApiError as e:
                    ctx.obj.console.print(f"[red]API Error:[/] {e} ({r})")
                    if not SKIP_ERRORS:
                        raise
                except Exception as e:
                    ctx.obj.console.print(f"[red]Error:[/] {e} ({r})")
                    if not SKIP_ERRORS:
                        raise

            await asyncio.gather(*(wrapper(r) for r in ctx.obj.resources))

        rich_output.show_stats()

    def run():
        asyncio.run(download_resources())

    ctx.call_on_close(run)
