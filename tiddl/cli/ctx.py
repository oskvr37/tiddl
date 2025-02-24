import functools
import click

from rich.console import Console

from typing import Callable, TypeVar, cast

from tiddl.api import TidalApi
from tiddl.config import Config
from tiddl.utils import TidalResource


class ContextObj:
    api: TidalApi | None
    config: Config
    resources: list[TidalResource]
    console: Console

    def __init__(self) -> None:
        self.config = Config.fromFile()
        self.resources = []
        self.api = None
        self.console = Console()

    def initApi(self, omit_cache=False):
        auth = self.config.auth

        if auth.token and auth.user_id and auth.country_code:
            self.api = TidalApi(
                auth.token,
                auth.user_id,
                auth.country_code,
                omit_cache=omit_cache or self.config.omit_cache,
            )

    def getApi(self) -> TidalApi:
        if self.api is None:
            raise click.UsageError("You must login first")

        return self.api


class Context(click.Context):
    obj: ContextObj


F = TypeVar("F", bound=Callable[..., None])


def passContext(func: F) -> F:
    """Wrapper for @click.pass_context to use custom Context"""

    @click.pass_context
    @functools.wraps(func)
    def wrapper(ctx: click.Context, *args, **kwargs):
        custom_ctx = cast(Context, ctx)
        return func(custom_ctx, *args, **kwargs)

    return cast(F, wrapper)
