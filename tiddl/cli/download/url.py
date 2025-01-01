import click

from ..ctx import Context, passContext

from tiddl.types import Track
from tiddl.utils import TidalResource


class TidalURL(click.ParamType):
    def convert(self, value: str, param, ctx) -> TidalResource:
        try:
            return TidalResource(value)
        except ValueError as e:
            self.fail(message=str(e), param=param, ctx=ctx)


@click.group("url")
@click.argument("url", type=TidalURL())
@passContext
def UrlGroup(ctx: Context, url: TidalResource):
    """
    Get Tidal URL.

    It can be Tidal link or `resource_type/resource_id` format.
    The resource can be a track, album, playlist or artist.
    """

    tracks: list[Track] = []

    # TODO: fetch api

    match url.resource_type:
        case "track":
            pass
        case "album":
            pass
        case "playlist":
            pass
        case "artist":
            pass

    ctx.obj.tracks.extend(tracks)
