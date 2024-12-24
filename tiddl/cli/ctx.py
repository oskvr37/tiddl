import functools
import click

from typing import Callable, TypeVar, cast
from tiddl import Config
from tiddl.types import Track


class ContextObj:
    def __init__(self, verbose: bool) -> None:
        self.config = Config()
        self.tracks: list[Track] = []

        self.verbose = verbose


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
