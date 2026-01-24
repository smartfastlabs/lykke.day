import re
import unicodedata


def normalize_email(email: str) -> str:
    """
    Normalize an email address by converting to lowercase and stripping whitespace.

    Example: "  User@Example.COM  " -> "user@example.com"
    """
    return email.strip().lower()


def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize a phone number by removing formatting characters.

    Example: "(555) 123-4567" -> "5551234567"
    Example: "+1 (555) 123-4567" -> "+15551234567"
    """
    # Remove all non-digit characters except leading +
    normalized = re.sub(r"[^\d+]", "", phone_number)
    # If it doesn't start with +, remove any + characters that might be in the middle
    if not normalized.startswith("+"):
        normalized = re.sub(r"[^\d]", "", normalized)
    return normalized


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
