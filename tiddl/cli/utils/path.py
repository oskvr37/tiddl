from pathlib import Path


def resolve_existing_path_case(base_path: Path, relative_path: Path) -> Path:
    """
    Return base_path / relative_path, reusing existing path component casing.
    """

    if relative_path.is_absolute():
        raise ValueError("relative_path must not be absolute")

    resolved_path = base_path

    for part in relative_path.parts:
        if part in ("", "."):
            continue

        existing_part = find_existing_child_case(resolved_path, part)
        resolved_path = resolved_path / (existing_part or part)

    return resolved_path


def find_existing_child_case(parent: Path, name: str) -> str | None:
    if not parent.is_dir():
        return None

    casefolded_name = name.casefold()
    fallback: str | None = None

    for child in parent.iterdir():
        if child.name == name:
            return child.name

        if fallback is None and child.name.casefold() == casefolded_name:
            fallback = child.name

    return fallback
