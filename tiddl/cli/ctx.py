import functools
import click

from typing import Callable, TypeVar, cast

from tiddl.api import TidalApi
from tiddl.config import Config
from tiddl.utils import TidalResource

class ContextObj:
    api: TidalApi | None
    config: Config
    resources: list[TidalResource]


    def __init__(self) -> None:
        self.config = Config()
        self.resources = []
        self.api = None

        config_auth = self.config.config["auth"]

        token, user_id, country_code = (
            config_auth.get("token"),
            config_auth.get("user_id"),
            config_auth.get("country_code"),
        )

        if token and user_id and country_code:
            self.api = TidalApi(token, user_id, country_code)

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
