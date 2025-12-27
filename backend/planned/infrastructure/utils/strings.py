import re
import unicodedata


def slugify(text: str) -> str:
    """
    Convert a string to a URL-friendly slug.

    Example: "Hello World! How's it going?" -> "hello-world-hows-it-going"
    """
    # Normalize unicode characters (é -> e, etc.)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)

    # Remove any characters that aren't alphanumeric or hyphens
    text = re.sub(r"[^a-z0-9-]", "", text)

    # Remove consecutive hyphens
    text = re.sub(r"-+", "-", text)

    # Strip leading/trailing hyphens
    text = text.strip("-")

    return text
