import re


def name_to_id(name: str) -> str:
    """
    Convert a name to a standardized ID format.

    Args:
        name: The name to convert.

    Returns:
        A standardized ID string.
    """
    # Convert to lowercase, replace spaces with hyphens, and remove non-alphanumeric characters
    id_str = re.sub(r"[^a-z0-9\s-]", "", name.lower())
    id_str = re.sub(r"\s+", "-", id_str)
    id_str = id_str.strip("-")
    return id_str
