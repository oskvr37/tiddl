import re


def sanitize_string(string: str) -> str:
    """
    Function used to sanitize file paths.
    Sometimes resources from Tidal contain
    forbidden characters that we need to remove.
    """

    pattern = r'[\\/:"*?<>|]+'
    return re.sub(pattern, "", string)
