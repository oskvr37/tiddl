from tiddl.core.utils.format import format_template

# we reuse Tidal API from another example
from .fetch_api import api

ALBUM_ID = 465173294


if __name__ == "__main__":
    album = api.get_album(ALBUM_ID)
    album_items = api.get_album_items(ALBUM_ID)

    TEMPLATE = "{album.artists}/{album.title}, {album.date:%Y}/{item.number:02d}. {item.artists} - {item.title} ({custom_field})"

    for album_item in album_items.items:
        track = album_item.item

        print(
            format_template(
                template=TEMPLATE,
                item=track,
                album=album,
                with_asterisk_ext=False,
                custom_field="custom_field",
            )
        )
