import click
import logging

from click import style
from time import sleep, time

from tiddl.config import AuthConfig
from tiddl.auth import (
    getDeviceAuth,
    getToken,
    refreshToken,
    removeToken,
    AuthError,
)

from .ctx import passContext, Context


logger = logging.getLogger(__name__)


@click.group("auth")
def AuthGroup():
    """Manage Tidal token."""


def refresh(ctx: Context):
    """Refresh auth token when is expired"""

    auth = ctx.obj.config.auth

    if auth.refresh_token and time() > auth.expires:
        click.echo(style("Refreshing token...", fg="yellow"))
        token = refreshToken(auth.refresh_token)

        ctx.obj.config.auth.expires = token.expires_in + int(time())
        ctx.obj.config.auth.token = token.access_token

        ctx.obj.config.save()

        click.echo(style("Refreshed auth token!", fg="green"))


@AuthGroup.command("login")
@passContext
def login(ctx: Context):
    """Add token to the config"""

    if ctx.obj.config.auth.token:
        click.echo(style("Already logged in.", fg="green"))
        refresh(ctx)
        return

    auth = getDeviceAuth()

    uri = f"https://{auth.verificationUriComplete}"
    click.launch(uri)
    click.echo(f"Go to {style(uri, fg='cyan')} and complete authentication!")

    auth_end_at = time() + auth.expiresIn

    while True:
        sleep(auth.interval)

        try:
            token = getToken(auth.deviceCode)
        except AuthError as e:
            if e.error == "authorization_pending":
                time_left = auth_end_at - time()
                minutes, seconds = time_left // 60, int(time_left % 60)

                click.echo(
                    f"\rTime left: {minutes:.0f}:{seconds:02d}", nl=False
                )
                continue

            if e.error == "expired_token":
                click.echo(
                    f"\nTime for authentication {style('has expired', fg='red')}."
                )
                break

        ctx.obj.config.auth = AuthConfig(
            token=token.access_token,
            refresh_token=token.refresh_token,
            expires=token.expires_in + int(time()),
            user_id=str(token.user.userId),
            country_code=token.user.countryCode,
        )
        ctx.obj.config.save()

        click.echo(style("\nAuthenticated!", fg="green"))

        break


@AuthGroup.command("logout")
@passContext
def logout(ctx: Context):
    """Remove token from config"""

    access_token = ctx.obj.config.auth.token

    if not access_token:
        click.echo(style("Not logged in", fg="yellow"))
        return

    removeToken(access_token)

    ctx.obj.config.auth = AuthConfig()
    ctx.obj.config.save()

    click.echo(style("Logged out!", fg="green"))
