import typer
from typing import cast
from typing_extensions import Annotated

from tiddl.cli.config import CONFIG
from tiddl.cli.ctx import Context
from tiddl.cli.utils.resource import ResourceTypeLiteral, TidalResource


fav_subcommand = typer.Typer()


@fav_subcommand.command()
def fav(
    ctx: Context,
    TYPES: Annotated[
        list[str],
        typer.Option(
            "-t",
            "--types",
            metavar="<resource>",
            help="Narrow resource types, usage: -t track -t album etc. Available resources: track, video, album, playlist, artist.",
        ),
    ] = ["track", "video", "album", "playlist", "artist"],
):
    """
    Get your Tidal favorites. You can narrow them to any type of your choice.
    """

    favorites = ctx.obj.api.get_favorites()
    favorites_dict = favorites.model_dump()

    stats: dict[ResourceTypeLiteral, int] = dict()

    for resource_type in cast(list[ResourceTypeLiteral], TYPES):
        if CONFIG.download.fav_mtime and resource_type in ("track", "video", "album"):
            offset = 0
            count = 0
            while True:
                if resource_type == "track":
                    page = ctx.obj.api.get_favorite_tracks(offset=offset)
                elif resource_type == "video":
                    page = ctx.obj.api.get_favorite_videos(offset=offset)
                else:
                    page = ctx.obj.api.get_favorite_albums(offset=offset)
                for entry in page.items:
                    ctx.obj.resources.append(
                        TidalResource(
                            id=str(entry.item.id),
                            type=resource_type,
                            fav_date_added=entry.created,
                        )
                    )
                    count += 1
                offset += page.limit
                if offset >= page.totalNumberOfItems:
                    break
            stats[resource_type] = count
        else:
            resources = favorites_dict[resource_type.upper()]
            stats[resource_type] = len(resources)
            for resource_id in resources:
                ctx.obj.resources.append(TidalResource(id=resource_id, type=resource_type))

    ctx.obj.console.print(f"[green]Loaded {len(ctx.obj.resources)} resources")

    for resource_type, count in stats.items():
        ctx.obj.console.print(f"{resource_type.title()}s: {count}")
