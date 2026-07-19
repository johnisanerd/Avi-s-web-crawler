from typing import Any, Dict, Set
from src.models import RawLead, Lead, ClayLead


def dict_to_raw_lead(data: Dict[str, Any]) -> RawLead:
    """
    Maps a raw JSON dictionary from Apify to a RawLead dataclass.
    Preserves data exactly during translation, converting missing fields to None.
    
    Args:
        data: Raw dictionary of scraped place data.

    Returns:
        A RawLead dataclass instance.
    """
    return RawLead(
        title=data.get("title"),
        categoryName=data.get("categoryName"),
        categories=data.get("categories"),
        subTitle=data.get("subTitle"),
        address=data.get("address"),
        city=data.get("city"),
        state=data.get("state"),
        postalCode=data.get("postalCode"),
        phone=data.get("phone"),
        website=data.get("website"),
        url=data.get("url"),
        totalScore=data.get("totalScore"),
        reviewsCount=data.get("reviewsCount"),
        socialProfiles=data.get("socialProfiles"),
        placeId=data.get("placeId"),
        location=data.get("location"),
        searchString=data.get("searchString")
    )


def raw_lead_to_lead(raw: RawLead) -> Lead:
    """
    Maps a RawLead dataclass directly to a standardized Lead dataclass.
    Performs field-to-field translation without normalizing or modifying data.
    
    Args:
        raw: RawLead instance.

    Returns:
        A Lead dataclass instance.
    """
    # Extract coordinates from raw location dictionary
    lat = None
    lng = None
    if isinstance(raw.location, dict):
        lat = raw.location.get("lat")
        lng = raw.location.get("lng")

    # Map search query set
    queries: Set[str] = set()
    if raw.searchString:
        queries.add(raw.searchString)

    return Lead(
        business_name=raw.title or "",
        category=raw.categoryName or "",
        website=raw.website or "",
        phone=raw.phone or "",
        street=raw.address or "",
        city=raw.city or "",
        state=raw.state or "",
        zip_code=raw.postalCode or "",
        country="",  # Left empty as country is not present in raw payload (no value invented)
        rating=raw.totalScore if raw.totalScore is not None else 0.0,
        review_count=raw.reviewsCount if raw.reviewsCount is not None else 0,
        latitude=lat,
        longitude=lng,
        google_maps_url=raw.url or "",
        google_place_id=raw.placeId,
        source_queries=queries,
        social_profiles=raw.socialProfiles
    )


def lead_to_clay_lead(lead: Lead) -> ClayLead:
    """
    Maps a standardized Lead dataclass to a ClayLead dataclass.
    
    Args:
        lead: Lead instance.

    Returns:
        A ClayLead dataclass instance.
    """
    return ClayLead(
        brokerage=lead.business_name,
        website=lead.website,
        city=lead.city,
        state=lead.state,
        phone=lead.phone,
        google_maps_url=lead.google_maps_url,
        lead_score=lead.lead_score,
        lead_tier=lead.lead_tier,
        score_breakdown=lead.score_breakdown,
        estimated_agent_count=lead.estimated_agent_count,
        office_count=lead.office_count,
        years_in_business=lead.years_in_business,
        social_profiles=lead.social_profiles,
        linkedin_url=lead.linkedin_url,
        facebook_url=lead.facebook_url,
        instagram_url=lead.instagram_url,
        youtube_url=lead.youtube_url,
        x_url=lead.x_url,
        tiktok_url=lead.tiktok_url,
        has_blog=lead.has_blog,
        has_contact_form=lead.has_contact_form,
        has_property_search=lead.has_property_search,
        has_mortgage_services=lead.has_mortgage_services,
        has_property_management=lead.has_property_management,
        has_commercial_services=lead.has_commercial_services,
        has_luxury_division=lead.has_luxury_division,
        has_careers_page=lead.has_careers_page,
        has_multiple_offices=lead.has_multiple_offices,
        business_intelligence_confidence=lead.business_intelligence_confidence,
        estimated_transactions=lead.estimated_transactions,
        estimated_gci=lead.estimated_gci,
        estimated_revenue_low=lead.estimated_revenue_low,
        estimated_revenue_high=lead.estimated_revenue_high,
        revenue_confidence=lead.revenue_confidence,
        revenue_reasoning=lead.revenue_reasoning,
        revenue_model_version=lead.revenue_model_version,
        website_platform=lead.website_platform,
        cms=lead.cms,
        idx_provider=lead.idx_provider,
        crm_platform=lead.crm_platform,
        analytics_tools=lead.analytics_tools,
        marketing_tools=lead.marketing_tools,
        chat_provider=lead.chat_provider,
        form_provider=lead.form_provider,
        consent_manager=lead.consent_manager,
        cdn_provider=lead.cdn_provider,
        technology_confidence=lead.technology_confidence,
        technology_reasoning=lead.technology_reasoning,
        technology_model_version=lead.technology_model_version
    )


def lead_to_standard_dict(lead: Lead) -> Dict[str, Any]:
    """
    Converts a Lead dataclass instance to a dictionary using the exact column keys
    defined in the system specification's Standardized Data Model.
    
    Args:
        lead: Lead instance.

    Returns:
        Dictionary mapping specification keys to values.
    """
    return {
        "Business Name": lead.business_name,
        "Category": lead.category,
        "Website": lead.website,
        "Phone": lead.phone,
        "Street": lead.street,
        "City": lead.city,
        "State": lead.state,
        "Zip Code": lead.zip_code,
        "Country": lead.country,
        "Rating": lead.rating,
        "Review Count": lead.review_count,
        "Latitude": lead.latitude,
        "Longitude": lead.longitude,
        "Google Maps URL": lead.google_maps_url,
        "Google Place ID": lead.google_place_id,
        "Business Email": lead.business_email,
        "Owner Name": lead.owner_name,
        "Owner Title": lead.owner_title,
        "Owner Email": lead.owner_email,
        "Lead Score": lead.lead_score,
        "Lead Tier": lead.lead_tier,
        "Score Breakdown": ", ".join(lead.score_breakdown),
        "Estimated Agent Count": lead.estimated_agent_count,
        "Office Count": lead.office_count,
        "Years in Business": lead.years_in_business,
        "LinkedIn URL": lead.linkedin_url,
        "Facebook URL": lead.facebook_url,
        "Instagram URL": lead.instagram_url,
        "YouTube URL": lead.youtube_url,
        "X URL": lead.x_url,
        "TikTok URL": lead.tiktok_url,
        "Has Blog": lead.has_blog,
        "Has Contact Form": lead.has_contact_form,
        "Has Property Search": lead.has_property_search,
        "Has Mortgage Services": lead.has_mortgage_services,
        "Has Property Management": lead.has_property_management,
        "Has Commercial Services": lead.has_commercial_services,
        "Has Luxury Division": lead.has_luxury_division,
        "Has Careers Page": lead.has_careers_page,
        "Has Multiple Offices": lead.has_multiple_offices,
        "Business Intelligence Confidence": lead.business_intelligence_confidence,
        "Estimated Transactions": lead.estimated_transactions,
        "Estimated GCI": lead.estimated_gci,
        "Estimated Revenue Low": lead.estimated_revenue_low,
        "Estimated Revenue High": lead.estimated_revenue_high,
        "Revenue Confidence": lead.revenue_confidence,
        "Revenue Reasoning": ", ".join(lead.revenue_reasoning),
        "Revenue Model Version": lead.revenue_model_version,
        "Website Platform": lead.website_platform,
        "CMS": lead.cms,
        "IDX Provider": lead.idx_provider,
        "CRM Platform": lead.crm_platform,
        "Analytics Tools": lead.analytics_tools,
        "Marketing Tools": lead.marketing_tools,
        "Chat Provider": lead.chat_provider,
        "Form Provider": lead.form_provider,
        "Consent Manager": lead.consent_manager,
        "CDN Provider": lead.cdn_provider,
        "Technology Confidence": lead.technology_confidence,
        "Technology Reasoning": ", ".join(lead.technology_reasoning),
        "Technology Model Version": lead.technology_model_version
    }


def clay_lead_to_dict(clay: ClayLead) -> Dict[str, str]:
    """
    Converts a ClayLead dataclass instance to a dictionary using the exact column keys
    defined in the system specification's Clay Export model.
    
    Args:
        clay: ClayLead instance.

    Returns:
        Dictionary mapping Clay export keys to values.
    """
    return {
        "Brokerage": clay.brokerage,
        "Website": clay.website,
        "City": clay.city,
        "State": clay.state,
        "Phone": clay.phone,
        "Google Maps URL": clay.google_maps_url,
        "Lead Score": clay.lead_score,
        "Lead Tier": clay.lead_tier,
        "Score Breakdown": ", ".join(clay.score_breakdown),
        "Estimated Agent Count": clay.estimated_agent_count,
        "Office Count": clay.office_count,
        "Years in Business": clay.years_in_business,
        "LinkedIn URL": clay.linkedin_url,
        "Facebook URL": clay.facebook_url,
        "Instagram URL": clay.instagram_url,
        "YouTube URL": clay.youtube_url,
        "X URL": clay.x_url,
        "TikTok URL": clay.tiktok_url,
        "Has Blog": clay.has_blog,
        "Has Contact Form": clay.has_contact_form,
        "Has Property Search": clay.has_property_search,
        "Has Mortgage Services": clay.has_mortgage_services,
        "Has Property Management": clay.has_property_management,
        "Has Commercial Services": clay.has_commercial_services,
        "Has Luxury Division": clay.has_luxury_division,
        "Has Careers Page": clay.has_careers_page,
        "Has Multiple Offices": clay.has_multiple_offices,
        "Business Intelligence Confidence": clay.business_intelligence_confidence,
        "Estimated Transactions": clay.estimated_transactions,
        "Estimated GCI": clay.estimated_gci,
        "Estimated Revenue Low": clay.estimated_revenue_low,
        "Estimated Revenue High": clay.estimated_revenue_high,
        "Revenue Confidence": clay.revenue_confidence,
        "Revenue Reasoning": ", ".join(clay.revenue_reasoning),
        "Revenue Model Version": clay.revenue_model_version,
        "Website Platform": clay.website_platform,
        "CMS": clay.cms,
        "IDX Provider": clay.idx_provider,
        "CRM Platform": clay.crm_platform,
        "Analytics Tools": clay.analytics_tools,
        "Marketing Tools": clay.marketing_tools,
        "Chat Provider": clay.chat_provider,
        "Form Provider": clay.form_provider,
        "Consent Manager": clay.consent_manager,
        "CDN Provider": clay.cdn_provider,
        "Technology Confidence": clay.technology_confidence,
        "Technology Reasoning": ", ".join(clay.technology_reasoning),
        "Technology Model Version": clay.technology_model_version
    }
