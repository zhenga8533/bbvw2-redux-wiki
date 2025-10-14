import re


def name_to_id(name: str) -> str:
    """
    Convert a name to a standardized ID format.

    Converts to lowercase, replaces spaces with hyphens, and removes
    non-alphanumeric characters (except hyphens). This is used for
    file names and string values in the JSON data.

    Note: JSON field names use snake_case, but this function produces
    kebab-case for file names and data values.

    Args:
        name: The name to convert.

    Returns:
        A standardized ID string (lowercase, kebab-case, alphanumeric only).

    Examples:
        >>> name_to_id("Mr. Mime")
        'mr-mime'
        >>> name_to_id("Farfetch'd")
        'farfetchd'
        >>> name_to_id("Ho-Oh")
        'ho-oh'
        >>> name_to_id("Nidoran♀")
        'nidoran'
        >>> name_to_id("Type: Null")
        'type-null'
    """
    # Convert to lowercase, replace spaces with hyphens, and remove non-alphanumeric characters
    id_str = re.sub(r"[^a-z0-9\s-]", "", name.lower())
    id_str = re.sub(r"\s+", "-", id_str)
    id_str = id_str.strip("-")
    return id_str
