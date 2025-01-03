import click

from ..ctx import Context


def getReadyApi(ctx: Context):
    if ctx.obj.api is None:
        raise click.ClickException(
            "API is not initialized, please use: tiddl auth login."
        )

    return ctx.obj.api
