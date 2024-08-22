import logging

from tiddl import initLogging


# TODO: implement library synchronization #35

# let user choose what to sync (tracks, albums, playlists, artists)


def main():
    initLogging(colored_logging=True, silent=False, verbose=False)
    logging.info("syncing library...")


if __name__ == "__main__":
    main()
