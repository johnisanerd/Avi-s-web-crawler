from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass(slots=True)
class RawLead:
    """
    Represents a raw lead record directly from the Apify Google Maps Scraper payload.
    This class is a data contract for the scraped, unnormalized data.
    """
    title: Optional[str] = None
    categoryName: Optional[str] = None
    categories: Optional[List[str]] = None
    subTitle: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    url: Optional[str] = None
    totalScore: Optional[float] = None
    reviewsCount: Optional[int] = None
    socialProfiles: Optional[Dict[str, Any]] = None
    placeId: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    searchString: Optional[str] = None


@dataclass(slots=True)
class Lead:
    """
    Represents a standardized, normalized, and validated internal real estate lead.
    Complies with the fields defined in the project specification's Standardized Data Model.
    """
    business_name: str
    category: str
    website: str
    phone: str
    street: str
    city: str
    state: str
    zip_code: str
    country: str
    rating: float
    review_count: int
    latitude: Optional[float]
    longitude: Optional[float]
    google_maps_url: str
    google_place_id: Optional[str]
    source_queries: Set[str]
    social_profiles: Dict[str, str] = field(default_factory=dict)
    business_email: Optional[str] = None
    owner_name: Optional[str] = None
    owner_title: Optional[str] = None
    owner_email: Optional[str] = None
    lead_score: int = 0
    lead_tier: str = "Low Priority"
    score_breakdown: List[str] = field(default_factory=list)
    estimated_agent_count: Optional[int] = None
    office_count: Optional[int] = None
    years_in_business: Optional[int] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    youtube_url: Optional[str] = None
    x_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    has_blog: bool = False
    has_contact_form: bool = False
    has_property_search: bool = False
    has_mortgage_services: bool = False
    has_property_management: bool = False
    has_commercial_services: bool = False
    has_luxury_division: bool = False
    has_careers_page: bool = False
    has_multiple_offices: bool = False
    business_intelligence_confidence: str = "Low"
    estimated_transactions: Optional[int] = None
    estimated_gci: Optional[float] = None
    estimated_revenue_low: Optional[float] = None
    estimated_revenue_high: Optional[float] = None
    revenue_confidence: str = "Low"
    revenue_reasoning: List[str] = field(default_factory=list)
    revenue_model_version: str = ""
    website_platform: Optional[str] = None
    cms: Optional[str] = None
    idx_provider: Optional[str] = None
    crm_platform: Optional[str] = None
    analytics_tools: Optional[str] = None
    marketing_tools: Optional[str] = None
    chat_provider: Optional[str] = None
    form_provider: Optional[str] = None
    consent_manager: Optional[str] = None
    cdn_provider: Optional[str] = None
    technology_confidence: str = "Low"
    technology_reasoning: List[str] = field(default_factory=list)
    technology_model_version: str = ""
    decision_maker: Optional[Any] = None


@dataclass(slots=True)
class ClayLead:
    """
    Represents the reduced data model formatted specifically for Clay export.
    """
    brokerage: str
    website: str
    city: str
    state: str
    phone: str
    google_maps_url: str
    lead_score: int = 0
    lead_tier: str = "Low Priority"
    score_breakdown: List[str] = field(default_factory=list)
    estimated_agent_count: Optional[int] = None
    office_count: Optional[int] = None
    years_in_business: Optional[int] = None
    social_profiles: Dict[str, str] = field(default_factory=dict)
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    youtube_url: Optional[str] = None
    x_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    has_blog: bool = False
    has_contact_form: bool = False
    has_property_search: bool = False
    has_mortgage_services: bool = False
    has_property_management: bool = False
    has_commercial_services: bool = False
    has_luxury_division: bool = False
    has_careers_page: bool = False
    has_multiple_offices: bool = False
    business_intelligence_confidence: str = "Low"
    estimated_transactions: Optional[int] = None
    estimated_gci: Optional[float] = None
    estimated_revenue_low: Optional[float] = None
    estimated_revenue_high: Optional[float] = None
    revenue_confidence: str = "Low"
    revenue_reasoning: List[str] = field(default_factory=list)
    revenue_model_version: str = ""
    website_platform: Optional[str] = None
    cms: Optional[str] = None
    idx_provider: Optional[str] = None
    crm_platform: Optional[str] = None
    analytics_tools: Optional[str] = None
    marketing_tools: Optional[str] = None
    chat_provider: Optional[str] = None
    form_provider: Optional[str] = None
    consent_manager: Optional[str] = None
    cdn_provider: Optional[str] = None
    technology_confidence: str = "Low"
    technology_reasoning: List[str] = field(default_factory=list)
    technology_model_version: str = ""
    decision_maker: Optional[Any] = None


@dataclass(slots=True)
class PageBlock:
    """
    Represents a structured section/block extracted from an HTML page.
    Decouples HTML parsing from candidate extraction logic.
    """
    page_url: str
    page_type: str
    heading: Optional[str] = None
    subheading: Optional[str] = None
    text: str = ""
    emails: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    container_type: str = "general"


@dataclass(slots=True)
class DecisionMakerEvidence:
    """
    Tracks detailed evidence and confidence delta adjustments for a decision maker score decision.
    """
    page_url: str
    page_type: str
    title_found: str
    matched_name: str
    matched_email: Optional[str] = None
    confidence_delta: float = 0.0
    reason: str = ""


@dataclass(slots=True)
class DecisionMakerCandidate:
    """
    Intermediate candidate object representing a potential decision maker during pipeline execution.
    """
    name: str
    title: str
    page_url: str
    page_type: str
    snippet: str
    matched_email: Optional[str] = None
    email_matching_strategy: Optional[str] = None
    title_weight: float = 0.0
    page_weight: float = 0.0
    email_weight: float = 0.0
    social_weight: float = 0.0
    score: float = 0.0
    is_primary: bool = False
    evidence: List[DecisionMakerEvidence] = field(default_factory=list)
    scoring_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class DecisionMaker:
    """
    Final structured output of the Decision Maker Intelligence module.
    """
    decision_maker_name: Optional[str] = None
    decision_maker_title: Optional[str] = None
    decision_maker_source: Optional[str] = None
    confidence_score: int = 0
    verified_email: Optional[str] = None
    email_source: Optional[str] = None
    email_verified: bool = False
    status: str = "NO_DECISION_MAKER"
    processing_time_ms: float = 0.0
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    decision_makers: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class WebsiteSnapshot:
    """
    Generic website snapshot abstraction passed into intelligence modules.
    Decouples modules from EmailExtractor/scraper internals.
    """
    domain: str
    pages: Dict[str, str] = field(default_factory=dict)  # url -> html_content
    social_profiles: Dict[str, str] = field(default_factory=dict)  # platform -> url

