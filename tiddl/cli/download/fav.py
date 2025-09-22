import click

from tiddl.utils import TidalResource, ResourceTypeLiteral
from tiddl.cli.ctx import Context, passContext

ResourceTypeList: list[ResourceTypeLiteral] = [
    "track",
    "video",
    "album",
    "artist",
    "playlist",
]


@click.group("fav")
@click.option(
    "--resource",
    "-r",
    "resource_types",
    multiple=True,
    type=click.Choice(ResourceTypeList),
)
@passContext
def FavGroup(ctx: Context, resource_types: list[ResourceTypeLiteral]):
    """Get your Tidal favorites."""

    api = ctx.obj.getApi()

    favorites = api.getFavorites()
    favorites_dict = favorites.model_dump()

    click.echo(type(resource_types))

    if not resource_types:
        resource_types = ResourceTypeList

    stats: dict[ResourceTypeLiteral, int] = dict()

    for resource_type in resource_types:
        resources = favorites_dict[resource_type.upper()]

        stats[resource_type] = len(resources)

        for resource_id in resources:
            ctx.obj.resources.append(TidalResource(id=resource_id, type=resource_type))

    # TODO: show pretty message

    click.echo(click.style(f"Loaded {len(ctx.obj.resources)} resources", "green"))

    for resource_type, count in stats.items():
        click.echo(f"{resource_type} - {count}")
