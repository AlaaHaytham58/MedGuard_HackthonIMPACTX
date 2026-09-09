import unicodedata


def normalize_name(value: str) -> str:
    """Normalize presentation only; preserve salts, doses, punctuation and ingredients."""
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())
