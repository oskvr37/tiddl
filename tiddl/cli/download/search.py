import click

from ..ctx import Context, passContext


@click.group("search")
@click.argument("query")
@passContext
def SearchGroup(ctx: Context, query: str):
    """Search on Tidal"""

    # TODO: search on Tidal
