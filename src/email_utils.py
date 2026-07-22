"""
Reusable email utility functions for normalization, generic detection,
and 8-stage deterministic email-to-person matching strategies.
"""

import re
from typing import List, Optional, Tuple
from src.decision_maker_config import GENERIC_EMAIL_PREFIXES


def normalize_email(email: str) -> str:
    """
    Cleans, strips whitespace, and lowercases an email address.
    """
    if not email:
        return ""
    clean = email.strip().lower()
    if clean.startswith("mailto:"):
        clean = clean[7:].strip()
    return clean


def is_generic_email(email: str) -> bool:
    """
    Returns True if the email belongs to a generic inbox (e.g. info@, office@, hello@, etc.).
    Generic emails MUST NEVER be assigned to an individual decision maker.
    """
    clean = normalize_email(email)
    if not clean or "@" not in clean:
        return True

    username = clean.split("@")[0]
    username_clean = re.sub(r'[^a-z0-9]', '', username)
    
    for prefix in GENERIC_EMAIL_PREFIXES:
        if username == prefix or username_clean == prefix:
            return True
        if username.startswith(f"{prefix}.") or username.startswith(f"{prefix}_") or username.startswith(f"{prefix}-"):
            return True

    return False


def is_personal_email(email: str) -> bool:
    """
    Returns True if an email is valid and NOT generic.
    """
    clean = normalize_email(email)
    if not clean:
        return False
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', clean):
        return False
    return not is_generic_email(clean)


def match_email_to_name(email: str, name: str) -> Tuple[bool, Optional[str], float]:
    """
    Attempts multi-strategy deterministic email-to-person username matching.

    Strategies evaluated in priority order:
    1. FIRST_DOT_LAST (e.g. john.smith@domain.com) -> weight 30.0
    2. EXACT_FULL_NAME (e.g. johnsmith@domain.com) -> weight 28.0
    3. FIRST_INITIAL_LAST (e.g. jsmith@domain.com) -> weight 25.0
    4. FIRST_NAME (e.g. john@domain.com) -> weight 22.0
    5. LAST_NAME (e.g. smith@domain.com) -> weight 18.0

    Returns:
        Tuple of (matched: bool, strategy_name: Optional[str], score_weight: float)
    """
    clean_email = normalize_email(email)
    if not is_personal_email(clean_email):
        return False, None, 0.0

    if not name:
        return False, None, 0.0

    tokens = [t.lower() for t in re.findall(r'[a-zA-Z]+', name)]
    if not tokens:
        return False, None, 0.0

    first = tokens[0]
    last = tokens[-1] if len(tokens) > 1 else ""
    full_name_clean = "".join(tokens)

    username = clean_email.split("@")[0].lower()
    username_alpha = re.sub(r'[^a-z]', '', username)

    # Strategy 1: FIRST_DOT_LAST
    if first and last:
        dotted_name = f"{first}.{last}"
        underscore_name = f"{first}_{last}"
        hyphen_name = f"{first}-{last}"
        if username in (dotted_name, underscore_name, hyphen_name):
            return True, "FIRST_DOT_LAST", 30.0

    # Strategy 2: EXACT_FULL_NAME
    if full_name_clean and (username == full_name_clean or (username_alpha == full_name_clean and '.' not in username)):
        return True, "EXACT_FULL_NAME", 28.0

    # Strategy 3: FIRST_INITIAL_LAST
    if first and last:
        initial_last = f"{first[0]}{last}"
        if username_alpha == initial_last or username == initial_last:
            return True, "FIRST_INITIAL_LAST", 25.0

    # Strategy 4: FIRST_NAME
    if first and len(first) >= 3:
        if username == first or username_alpha == first:
            return True, "FIRST_NAME", 22.0

    # Strategy 5: LAST_NAME
    if last and len(last) >= 3:
        if username == last or username_alpha == last:
            return True, "LAST_NAME", 18.0

    return False, None, 0.0
