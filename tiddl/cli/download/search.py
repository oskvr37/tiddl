import click

from tiddl.utils import TidalResource
from tiddl.models.resource import Artist, Album, Playlist, Track, Video

from ..ctx import Context, passContext


@click.group("search")
@click.argument("query")
@passContext
def SearchGroup(ctx: Context, query: str):
    """Search on Tidal."""

    # TODO: give user interactive choice what to select

    api = ctx.obj.getApi()

    search = api.getSearch(query)

    # issue is that we get resource data in search api call,
    # in download we refetch that data.
    # it's not that big deal as we refetch one resource at most,
    # but it should be redesigned

    if not search.topHit:
        click.echo(f"No search results for '{query}'")
        return

    value = search.topHit.value
    icon = click.style("\u2bcc", "magenta")

    if isinstance(value, Album):
        resource = TidalResource(type="album", id=str(value.id))
        click.echo(f"{icon} Album {value.title}")
    elif isinstance(value, Artist):
        resource = TidalResource(type="artist", id=str(value.id))
        click.echo(f"{icon} Artist {value.name}")
    elif isinstance(value, Track):
        resource = TidalResource(type="track", id=str(value.id))
        click.echo(f"{icon} Track {value.title}")
    elif isinstance(value, Playlist):
        resource = TidalResource(type="playlist", id=str(value.uuid))
        click.echo(f"{icon} Playlist {value.title}")
    elif isinstance(value, Video):
        resource = TidalResource(type="video", id=str(value.id))
        click.echo(f"{icon} Video {value.title}")

    ctx.obj.resources.append(resource)
