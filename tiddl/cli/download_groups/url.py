import click

from ..utils import Context, passContext
from tiddl.types import Track
from urllib import parse as urlparse


class URL(click.ParamType):
    # TODO: create correct Tidal URL rules
    name = "url"

    def convert(self, value, param, ctx):
        if not isinstance(value, tuple):
            value = urlparse.urlparse(value)
            if value.scheme not in ("http", "https"):
                self.fail(
                    f"invalid URL scheme ({value.scheme}). Only HTTP URLs are allowed",
                    param,
                    ctx,
                )
        return value


@click.group("url")
@click.argument("url", type=URL())
@passContext
def UrlGroup(ctx: Context, url: URL, filename):
    """Get Tidal URLs"""

    print(url, filename)

    tracks: list[Track] = []
    ctx.obj.tracks.extend(tracks)
