import re
from typing import Optional, Tuple
from urllib.parse import urlparse
from src.models import Lead


def normalize_whitespace(text: Optional[str]) -> Optional[str]:
    """
    Strips leading/trailing whitespace and collapses multiple internal spaces
    into a single space.
    
    Args:
        text: The string to normalize.

    Returns:
        The normalized string, or None if the input was None.
    """
    if text is None:
        return None
    return " ".join(text.strip().split())


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalizes phone numbers to digits only, removing all formatting.
    
    Args:
        phone: The phone string.

    Returns:
        Digits-only phone string, or None if the input was None.
    """
    if phone is None:
        return None
    return re.sub(r"\D", "", phone)


def normalize_website(website: Optional[str]) -> Optional[str]:
    """
    Extracts a clean, normalized domain name from a URL (e.g. "domain.com").
    
    Args:
        website: The website URL.

    Returns:
        Normalized domain name, or None if the input was None.
    """
    if website is None:
        return None
    cleaned = website.strip().lower()
    if not cleaned:
        return ""
    if not cleaned.startswith(("http://", "https://")):
        cleaned = "https://" + cleaned
    try:
        parsed = urlparse(cleaned)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def normalize_url(url: Optional[str]) -> Optional[str]:
    """
    Standardizes a URL string by stripping leading and trailing whitespace.
    
    Args:
        url: The URL to normalize.

    Returns:
        The cleaned URL, or None if the input was None.
    """
    if url is None:
        return None
    return url.strip()


def normalize_city(city: Optional[str]) -> Optional[str]:
    """
    Normalizes a city name by collapsing whitespace and title-casing it.
    
    Args:
        city: The city name.

    Returns:
        The normalized city name, or None if the input was None.
    """
    if city is None:
        return None
    cleaned = normalize_whitespace(city)
    return cleaned.title() if cleaned else ""


def normalize_state(state: Optional[str]) -> Optional[str]:
    """
    Normalizes a state designation to uppercase and strips whitespace.
    
    Args:
        state: The state name or abbreviation.

    Returns:
        The normalized state name, or None if the input was None.
    """
    if state is None:
        return None
    return state.strip().upper()


def normalize_zip_code(zip_code: Optional[str]) -> Optional[str]:
    """
    Cleans postal/zip code strings by stripping leading and trailing whitespace.
    
    Args:
        zip_code: The ZIP code string.

    Returns:
        The normalized ZIP code, or None if the input was None.
    """
    if zip_code is None:
        return None
    return zip_code.strip()


def normalize_country(country: Optional[str]) -> Optional[str]:
    """
    Normalizes country designation to uppercase and strips whitespace.
    
    Args:
        country: The country name.

    Returns:
        The normalized country name, or None if the input was None.
    """
    if country is None:
        return None
    return country.strip().upper()


def normalize_rating(rating: Optional[float]) -> Optional[float]:
    """
    Normalizes a float rating score.
    
    Args:
        rating: The rating score.

    Returns:
        The float rating, or None if the input was None or invalid.
    """
    if rating is None:
        return None
    try:
        return float(rating)
    except (ValueError, TypeError):
        return None


def normalize_review_count(reviews: Optional[int]) -> Optional[int]:
    """
    Normalizes an integer review count.
    
    Args:
        reviews: The count of reviews.

    Returns:
        The integer review count, or None if the input was None or invalid.
    """
    if reviews is None:
        return None
    try:
        return int(reviews)
    except (ValueError, TypeError):
        return None


def normalize_coordinates(
    lat: Optional[float], 
    lng: Optional[float]
) -> Tuple[Optional[float], Optional[float]]:
    """
    Normalizes latitude and longitude coordinates.
    
    Args:
        lat: Latitude value.
        lng: Longitude value.

    Returns:
        A tuple of (normalized_latitude, normalized_longitude).
    """
    new_lat = None
    new_lng = None
    if lat is not None:
        try:
            new_lat = float(lat)
        except (ValueError, TypeError):
            pass
    if lng is not None:
        try:
            new_lng = float(lng)
        except (ValueError, TypeError):
            pass
    return new_lat, new_lng


def normalize_lead(lead: Lead) -> Lead:
    """
    Coordinates the individual normalization functions to return a new, normalized
    Lead object. Preserves the original input lead instance unmodified.
    Never alters the Lead business_name property.
    
    Args:
        lead: The Lead instance to normalize.

    Returns:
        A new normalized Lead instance.
    """
    norm_lat, norm_lng = normalize_coordinates(lead.latitude, lead.longitude)
    
    return Lead(
        business_name=lead.business_name,  # Left unaltered as per spec
        category=(normalize_whitespace(lead.category) or ""),
        website=(normalize_website(lead.website) or ""),
        phone=(normalize_phone(lead.phone) or ""),
        street=(normalize_whitespace(lead.street) or ""),
        city=(normalize_city(lead.city) or ""),
        state=(normalize_state(lead.state) or ""),
        zip_code=(normalize_zip_code(lead.zip_code) or ""),
        country=(normalize_country(lead.country) or ""),
        rating=(normalize_rating(lead.rating) if lead.rating is not None else 0.0),
        review_count=(normalize_review_count(lead.review_count) if lead.review_count is not None else 0),
        latitude=norm_lat,
        longitude=norm_lng,
        google_maps_url=(normalize_url(lead.google_maps_url) or ""),
        google_place_id=lead.google_place_id,
        source_queries=lead.source_queries
    )
