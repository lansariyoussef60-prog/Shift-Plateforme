import re


def normalize_company_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace. This is the single
    function both partner creation and target-list search go through — if it
    ever needs to get smarter (stripping 'Inc.', 'Ltd', legal suffixes, etc.),
    it only needs to change here, and every dedup check benefits.

    Reused as-is for speaker name normalization since the same
    duplicate-detection problem applies to both.
    """
    if not name:
        return ""
    cleaned = name.strip().lower()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned
