import re
from typing import Optional
from src.models import Lead


def is_valid_phone(phone: Optional[str]) -> bool:
    """
    Validates if a phone number is valid (contains between 7 and 15 digits).
    
    Args:
        phone: The phone number string to validate.
        
    Returns:
        True if the phone number has a valid length of digits, False otherwise.
    """
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return 7 <= len(digits) <= 15


def is_valid_url(url: Optional[str]) -> bool:
    """
    Validates if a website URL format is basic-valid (contains at least one dot).
    
    Args:
        url: The URL string to validate.
        
    Returns:
        True if the URL string has a valid shape, False otherwise.
    """
    if not url:
        return False
    url_clean = url.strip()
    return "." in url_clean and not url_clean.startswith(".") and not url_clean.endswith(".") and len(url_clean) >= 4


def is_valid_state(state: Optional[str]) -> bool:
    """
    Validates if a state is a standard 2-letter alphabetic abbreviation.
    
    Args:
        state: The state string to validate.
        
    Returns:
        True if the state has a valid abbreviation shape, False otherwise.
    """
    if not state:
        return False
    state_clean = state.strip()
    return len(state_clean) == 2 and state_clean.isalpha()


def is_valid_zip_code(zip_code: Optional[str]) -> bool:
    """
    Validates if a ZIP code matches standard US formats (5 digits or ZIP+4 '5+4' digits).
    
    Args:
        zip_code: The ZIP code string to validate.
        
    Returns:
        True if the ZIP code format is valid, False otherwise.
    """
    if not zip_code:
        return False
    zip_clean = zip_code.strip()
    if "-" in zip_clean:
        parts = zip_clean.split("-")
        return len(parts) == 2 and parts[0].isdigit() and len(parts[0]) == 5 and parts[1].isdigit() and len(parts[1]) == 4
    return zip_clean.isdigit() and len(zip_clean) == 5


def is_valid_country(country: Optional[str]) -> bool:
    """
    Validates if a country code is a standard 2-letter alphabetic code.
    
    Args:
        country: The country string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not country:
        return False
    country_clean = country.strip()
    return len(country_clean) == 2 and country_clean.isalpha()


def is_valid_rating(rating: Optional[float]) -> bool:
    """
    Validates if a business review rating is between 0.0 and 5.0.
    
    Args:
        rating: The rating value to validate.
        
    Returns:
        True if rating is within the correct range, False otherwise.
    """
    if rating is None:
        return False
    return 0.0 <= rating <= 5.0


def is_valid_coordinates(latitude: Optional[float], longitude: Optional[float]) -> bool:
    """
    Validates if geospatial coordinates are within valid geographic bounds.
    
    Args:
        latitude: The latitude degree.
        longitude: The longitude degree.
        
    Returns:
        True if coordinates are within limits, False otherwise.
    """
    if latitude is None or longitude is None:
        return False
    return -90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0


def is_valid_google_maps_url(url: Optional[str]) -> bool:
    """
    Validates if a URL points to Google Maps.
    
    Args:
        url: The URL to validate.
        
    Returns:
        True if the URL contains Google Maps indicators, False otherwise.
    """
    if not url:
        return False
    url_clean = url.lower().strip()
    return "google.com/maps" in url_clean or "maps.google" in url_clean or "g.co/maps" in url_clean or "goo.gl/maps" in url_clean


def is_valid_place_id(place_id: Optional[str]) -> bool:
    """
    Validates if a Google Place ID is a non-empty string.
    
    Args:
        place_id: The place ID to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not place_id:
        return False
    return isinstance(place_id, str) and len(place_id.strip()) > 0


def validate_lead(lead: Lead) -> bool:
    """
    Performs validation checks on a standard Lead dataclass instance.
    Returns True if the lead is valid and has a valid Business Name.
    
    Args:
        lead: The Lead instance to validate.
        
    Returns:
        True if the lead is valid, False otherwise.
    """
    if not lead or not lead.business_name or not lead.business_name.strip():
        return False
    
    # Optional field range validation (if set)
    if lead.rating is not None and not is_valid_rating(lead.rating):
        return False
        
    if lead.latitude is not None or lead.longitude is not None:
        if not is_valid_coordinates(lead.latitude, lead.longitude):
            return False
            
    return True
