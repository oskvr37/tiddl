import logging

from tiddl import initLogging


# TODO: implement library synchronization #35


def main():
    initLogging(colored_logging=True, directory="tiddl", silent=False, verbose=False)
    logging.info("syncing library...")


if __name__ == "__main__":
    main()
