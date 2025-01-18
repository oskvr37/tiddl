import click
import logging

from click import style
from time import sleep, time

from tiddl.auth import getDeviceAuth, getToken, refreshToken, removeToken, AuthError
from .ctx import passContext, Context


logger = logging.getLogger(__name__)


@click.group("auth")
def AuthGroup():
    """Manage Tidal token"""


@AuthGroup.command("login")
@passContext
def login(ctx: Context):
    """Add token to the config"""

    access_token, refresh_token, expires = (
        ctx.obj.config.config["auth"].get("token"),
        ctx.obj.config.config["auth"].get("refresh_token"),
        ctx.obj.config.config["auth"].get("expires", 0),
    )

    if access_token:
        if refresh_token and time() > expires:
            click.echo(style("Refreshing token...", fg="yellow"))
            token = refreshToken(refresh_token)

            ctx.obj.config.update(
                {
                    "auth": {
                        "expires": token.expires_in + int(time()),
                        "token": token.access_token,
                    }
                }
            )

        click.echo(style("Authenticated!", fg="green"))
        return

    auth = getDeviceAuth()

    uri = f"https://{auth.verificationUriComplete}"
    click.launch(uri)
    click.echo(f"Go to {style(uri, fg='cyan')} and complete authentication!")

    time_left = time() + auth.expiresIn

    while True:
        sleep(auth.interval)

        try:
            token = getToken(auth.deviceCode)
        except AuthError as e:
            if e.error == "authorization_pending":
                # FIX: `Time left: 0 secondsss` 🐍

                click.echo(f"\rTime left: {time_left - time():.0f} seconds", nl=False)
                continue

            if e.error == "expired_token":
                click.echo(
                    f"\nTime for authentication {style('has expired', fg='red')}."
                )
                break

        ctx.obj.config.update(
            {
                "auth": {
                    "token": token.access_token,
                    "refresh_token": token.refresh_token,
                    "expires": token.expires_in + int(time()),
                    "user_id": str(token.user.userId),
                    "country_code": token.user.countryCode,
                }
            }
        )

        click.echo(style("\nAuthenticated!", fg="green"))

        break


@AuthGroup.command("logout")
@passContext
def logout(ctx: Context):
    """Remove token from config"""

    access_token = ctx.obj.config.config["auth"].get("token")

    if not access_token:
        click.echo(style("Not logged in", fg="yellow"))
        return

    removeToken(access_token)

    ctx.obj.config.update(
        {
            "auth": {
                "country_code": "",
                "expires": 0,
                "refresh_token": "",
                "token": "",
                "user_id": "",
            }
        }
    )

    click.echo(style("Logged out!", fg="green"))
