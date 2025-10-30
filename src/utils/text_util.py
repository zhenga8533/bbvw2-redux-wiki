import re
import itertools


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
    id_str = name.replace("é", "e")
    id_str = re.sub(r"[^a-z0-9\s-]", "", id_str.lower())
    id_str = re.sub(r"\s+", "-", id_str)
    id_str = id_str.strip("-")
    return id_str


def strip_common_prefix(string1: str, string2: str) -> str:
    """
    Removes the longest identical starting substring shared between string1 and string2
    from string2, including any common trailing punctuation like ', ' or ' '.

    Args:
        string1: The reference string (e.g., 'Surf, Normal').
        string2: The string to be stripped (e.g., 'Surf, Dark Spot').

    Returns:
        The remainder of string2 after the common prefix and any common separators
        are removed (e.g., 'Dark Spot').
    """
    common_chars = itertools.takewhile(
        lambda pair: pair[0] == pair[1], zip(string1, string2)
    )
    common_prefix = "".join(c for c, _ in common_chars)

    start_index = len(common_prefix)

    while start_index < len(string2) and string2[start_index] in (",", " "):
        start_index += 1

    return string2[start_index:]


def strip_common_suffix(string1: str, string2: str) -> str:
    """
    Removes the longest identical ending substring shared between string1 and string2
    from string2, including any common leading punctuation like ', ' or ' '.

    Args:
        string1: The reference string (e.g., 'Blue, Normal').
        string2: The string to be stripped (e.g., 'Red, Normal').

    Returns:
        The remainder of string2 after the common suffix and any common separators
        are removed (e.g., 'Red').
    """
    # 1. Find the longest common suffix
    common_chars = itertools.takewhile(
        lambda pair: pair[0] == pair[1],
        zip(reversed(string1), reversed(string2)),
    )
    common_suffix = "".join(c for c, _ in common_chars)[::-1]

    # 2. Determine the ending index for the result in string2
    end_index = len(string2) - len(common_suffix)

    # 3. Handle common leading separators (e.g., ', ' or ' ')
    # Move the index back past any trailing space or comma *in string2* # that is now at the end of the remaining string.
    # It removes multiple spaces/commas but stops at any other character.
    while end_index > 0 and string2[end_index - 1] in (",", " "):
        end_index -= 1

    # 4. Return the remainder of string2
    return string2[:end_index]


def extract_form_suffix(pokemon_name: str, base_name: str) -> str:
    """
    Extract the form suffix from a Pokemon name.

    Args:
        pokemon_name: Full Pokemon name (e.g., "giratina-altered")
        base_name: Base species name (e.g., "giratina")

    Returns:
        The form suffix, or empty string if no suffix exists.
        Examples:
            - ("giratina-altered", "giratina") -> "altered"
            - ("rotom", "rotom") -> ""
            - ("darmanitan-zen", "darmanitan") -> "zen"
    """
    if pokemon_name.startswith(base_name):
        suffix = pokemon_name[len(base_name):].lstrip('-')
        return suffix
    return ""
