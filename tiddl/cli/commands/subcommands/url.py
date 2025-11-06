import typer
from typing_extensions import Annotated

from tiddl.cli.ctx import Context
from tiddl.cli.utils.resource import TidalResource


url_subcommand = typer.Typer()


@url_subcommand.command(
    no_args_is_help=True,
)
def url(
    ctx: Context,
    urls: Annotated[
        list[TidalResource], typer.Argument(parser=TidalResource.from_string)
    ],
):
    """
    Get Tidal URLs.

    It can be Tidal link or `resource_type/resource_id` format
    e.g. track/12345, album/67890.

    Available resource types: track, video, album, playlist, artist, mix.
    """

    ctx.obj.resources.extend(urls)
