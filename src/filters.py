from dataclasses import dataclass
from typing import Optional, Set
from src.models import Lead
from src.constants import POSITIVE_KEYWORDS, EXCLUDED_KEYWORDS

# Additional negative keywords to fully satisfy the specifications not fully covered in constants
ADDITIONAL_EXCLUDED_KEYWORDS = {
    "property management",
    "apartment leasing",
    "apartment",
    "apartments",
    "vacation rental",
    "vacation rentals",
    "leasing agency",
    "property manager"
}


def passes_geographic_filter(
    lead: Lead,
    allowed_states: Optional[Set[str]] = None,
    allowed_countries: Optional[Set[str]] = None
) -> bool:
    """
    Checks if a lead is geographically relevant based on dynamic configuration parameters.
    Does not mutate the lead, does not log, does not normalize, is deterministic,
    and returns only True or False.
    
    Args:
        lead: A Lead dataclass instance.
        allowed_states: Optional set of allowed US states (abbreviations or names).
        allowed_countries: Optional set of allowed countries.

    Returns:
        True if the lead passes geographic relevance rules, False otherwise.
    """
    if allowed_countries:
        country_clean = lead.country.strip().upper()
        allowed_countries_upper = {c.strip().upper() for c in allowed_countries}
        if country_clean and country_clean not in allowed_countries_upper:
            return False

    if allowed_states:
        state_clean = lead.state.strip().upper()
        allowed_states_upper = {s.strip().upper() for s in allowed_states}
        if state_clean and state_clean not in allowed_states_upper:
            return False

    return True


@dataclass(slots=True)
class FilterResult:
    """
    Represents the output of the filtering operation for a single lead.
    """
    accepted: bool
    reason: str


def check_residential_lead(
    lead: Lead,
    allowed_states: Optional[Set[str]] = None,
    allowed_countries: Optional[Set[str]] = None
) -> FilterResult:
    """
    Determines whether a normalized Lead should remain in the pipeline based on
    case-insensitive keyword matching and dynamic geographic validation.

    Matches categories and business names against positive (residential brokerage)
    and negative (commercial, leasing, mortgage, etc.) keyword groups.

    Args:
        lead: A normalized Lead dataclass instance.
        allowed_states: Optional set of allowed US states.
        allowed_countries: Optional set of allowed countries.

    Returns:
        A FilterResult object containing validation decision and rationale.
    """
    # 0. Check geographic relevance filter using configurations passed in
    if not passes_geographic_filter(lead, allowed_states=allowed_states, allowed_countries=allowed_countries):
        return FilterResult(
            accepted=False,
            reason="Geographic validation failed: lead falls outside the allowed region."
        )

    business_name_lower = lead.business_name.lower()
    category_lower = lead.category.lower()
    text_corpus = f"{business_name_lower} {category_lower}"

    # 1. Check for negative matches in category and business name
    for kw in EXCLUDED_KEYWORDS:
        kw_lower = kw.lower()
        if kw_lower in category_lower:
            return FilterResult(
                accepted=False,
                reason=f"Excluded category keyword match: '{kw}'"
            )
        if kw_lower in business_name_lower:
            return FilterResult(
                accepted=False,
                reason=f"Excluded business name keyword match: '{kw}'"
            )

    for kw in ADDITIONAL_EXCLUDED_KEYWORDS:
        if kw in category_lower:
            return FilterResult(
                accepted=False,
                reason=f"Excluded category keyword match (additional): '{kw}'"
            )
        if kw in business_name_lower:
            return FilterResult(
                accepted=False,
                reason=f"Excluded business name keyword match (additional): '{kw}'"
            )

    # 2. Commercial filter check (commercial is rejected unless residential is explicitly present)
    if "commercial" in text_corpus and "residential" not in text_corpus:
        return FilterResult(
            accepted=False,
            reason="Commercial real estate matches without residential qualification."
        )

    # 3. Check for positive matches
    # Standard brokerage types matching standard category phrases
    is_standard_brokerage = any(
        kw in category_lower for kw in ["real estate agency", "real estate agent", "realtor", "brokerage"]
    )
    if is_standard_brokerage:
        return FilterResult(
            accepted=True,
            reason="Category matches standard residential brokerage terms."
        )

    # Check for other positive keywords
    for kw in POSITIVE_KEYWORDS:
        kw_lower = kw.lower()
        if kw_lower in text_corpus:
            return FilterResult(
                accepted=True,
                reason=f"Positive keyword match found: '{kw}'"
            )

    # 4. Default rejection if no positive criteria met
    return FilterResult(
        accepted=False,
        reason="No positive residential real estate indicators found."
    )
