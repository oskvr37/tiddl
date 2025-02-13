import click
import logging

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


@AuthGroup.command("refresh")
@passContext
def refresh(ctx: Context):
    """Refresh auth token when is expired"""

    logger.debug("Invoked refresh command")

    auth = ctx.obj.config.auth

    if auth.refresh_token and time() > auth.expires:
        logger.info("Refreshing token...")
        token = refreshToken(auth.refresh_token)

        ctx.obj.config.auth.expires = token.expires_in + int(time())
        ctx.obj.config.auth.token = token.access_token

        ctx.obj.config.save()
        logger.info("Refreshed auth token!")


@AuthGroup.command("login")
@passContext
def login(ctx: Context):
    """Add token to the config"""

    logger.debug("Invoked login command")

    if ctx.obj.config.auth.token:
        logger.info("Already logged in.")
        refresh(ctx)
        return

    auth = getDeviceAuth()

    uri = f"https://{auth.verificationUriComplete}"
    click.launch(uri)

    logger.info(f"Go to {uri} and complete authentication!")

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
                logger.info("\nTime for authentication has expired.")
                break

        ctx.obj.config.auth = AuthConfig(
            token=token.access_token,
            refresh_token=token.refresh_token,
            expires=token.expires_in + int(time()),
            user_id=str(token.user.userId),
            country_code=token.user.countryCode,
        )
        ctx.obj.config.save()

        logger.info("\nAuthenticated!")

        break


@AuthGroup.command("logout")
@passContext
def logout(ctx: Context):
    """Remove token from config"""

    logger.debug("Invoked logout command")

    access_token = ctx.obj.config.auth.token

    if not access_token:
        logger.info("Not logged in.")
        return

    removeToken(access_token)

    ctx.obj.config.auth = AuthConfig()
    ctx.obj.config.save()

    logger.info("Logged out!")
