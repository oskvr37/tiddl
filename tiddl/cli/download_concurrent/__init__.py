import logging
import click

from ..ctx import Context, passContext

from typing import List, Literal

from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
)

from tiddl.download import downloadTrackStream
from tiddl.utils import (
    formatTrack,
    trackExists,
    TidalResource,
    convertFileExtension,
)
from tiddl.metadata import addMetadata, Cover
from tiddl.exceptions import ApiError, AuthError
from tiddl.models.constants import TrackArg, ARG_TO_QUALITY
from tiddl.models.resource import Track, Album
from tiddl.models.api import PlaylistItems, AlbumItemsCredits

SinglesFilter = Literal["none", "only", "include"]


@click.command("download")
@click.option(
    "--quality", "-q", "QUALITY", type=click.Choice(TrackArg.__args__)
)
@click.option(
    "--output", "-o", "TEMPLATE", type=str, help="Format track file template."
)
@click.option(
    "--threads",
    "-t",
    "THREADS_COUNT",
    type=int,
    help="Number of threads to use in concurrent download; use with caution.",
    default=1,
)
@click.option(
    "--noskip",
    "-ns",
    "DO_NOT_SKIP",
    is_flag=True,
    default=False,
    help="Do not skip already downloaded tracks.",
)
@click.option(
    "--singles",
    "-s",
    "SINGLES_FILTER",
    type=click.Choice(SinglesFilter.__args__),
    default="none",
    help="Defines how to treat artist EPs and singles.",
)
@passContext
def DownloadCommand(
    ctx: Context,
    QUALITY: TrackArg | None,
    TEMPLATE: str | None,
    THREADS_COUNT: int,
    DO_NOT_SKIP: bool,
    SINGLES_FILTER: SinglesFilter,
):
    """Download resources"""

    logging.debug(
        (QUALITY, TEMPLATE, THREADS_COUNT, DO_NOT_SKIP, SINGLES_FILTER)
    )

    api = ctx.obj.getApi()

    def handleResource(resource: TidalResource) -> None:
        pass

    failed_resources: list[TidalResource] = []

    for resource in ctx.obj.resources:
        try:
            handleResource(resource)

        except ApiError as e:
            # TODO: handle rate limit
            logging.error(e)
            failed_resources.append(resource)

        except AuthError as e:
            logging.error(e)
            return

    # TODO: do something with `failed_resources`
