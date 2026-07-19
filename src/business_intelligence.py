import re
from dataclasses import replace
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from src.models import Lead
from src.email_extractor import ExtractionResult
from src.logger import get_logger

logger = get_logger("business_intelligence")


class BusinessIntelligence:
    """
    Evaluates enriched Lead records and extracts observable company intelligence
    exclusively from public information already downloaded from the company's website.
    """

    def __init__(self) -> None:
        pass

    def analyze_leads(self, leads: List[Lead], domain_cache: Dict[str, ExtractionResult]) -> List[Lead]:
        """
        Orchestrates profiling for a collection of Lead objects, utilizing downloaded HTML
        stored in the domain cache to avoid duplicate HTTP requests.
        """
        logger.info(f"Extracting company intelligence for {len(leads)} leads...")
        profiled_leads: List[Lead] = []

        for lead in leads:
            try:
                # Find matching extraction results from enrichment stage
                if lead.website:
                    parsed_url = urlparse(lead.website)
                    domain = (parsed_url.netloc or parsed_url.path).lower().strip()
                else:
                    domain = ""

                extraction_res = domain_cache.get(domain) if domain else None
                html_pages = extraction_res.html_pages if extraction_res else []

                profiled = self.analyze_lead(lead, html_pages)
                profiled_leads.append(profiled)
            except Exception as e:
                logger.error(f"Failed to analyze lead {lead.business_name}: {e}")
                profiled_leads.append(lead)

        logger.info("Company intelligence extraction complete.")
        return profiled_leads

    def analyze_lead(self, lead: Lead, html_pages: List[str]) -> Lead:
        """
        Extracts business intelligence from a list of HTML pages for a single Lead record.
        """
        if not html_pages:
            # Low confidence default if no HTML was downloaded
            return replace(
                lead,
                estimated_agent_count=None,
                office_count=None,
                years_in_business=None,
                social_profiles={},
                linkedin_url=None,
                facebook_url=None,
                instagram_url=None,
                youtube_url=None,
                x_url=None,
                tiktok_url=None,
                has_blog=False,
                has_contact_form=False,
                has_property_search=False,
                has_mortgage_services=False,
                has_property_management=False,
                has_commercial_services=False,
                has_luxury_division=False,
                has_careers_page=False,
                has_multiple_offices=False,
                business_intelligence_confidence="Low"
            )

        # 1. Estimate Agent Count
        agent_count = self._estimate_agent_count(html_pages)

        # 2. Office Count & Multiple Offices check
        office_count, has_multiple_offices = self._estimate_office_count(html_pages)

        # 3. Years in Business
        years_in_business = self._estimate_years_in_business(html_pages)

        # 4. Social Links
        socials = self._extract_social_links(html_pages)

        # 5. Feature Detection
        features = self._detect_features(html_pages)

        # 6. Calculate Confidence
        confidence = self._compute_confidence(
            agent_count=agent_count,
            office_count=office_count,
            years_in_business=years_in_business,
            socials=socials,
            features=features
        )

        return replace(
            lead,
            estimated_agent_count=agent_count,
            office_count=office_count,
            years_in_business=years_in_business,
            social_profiles=socials,
            linkedin_url=socials.get("linkedin"),
            facebook_url=socials.get("facebook"),
            instagram_url=socials.get("instagram"),
            youtube_url=socials.get("youtube"),
            x_url=socials.get("x"),
            tiktok_url=socials.get("tiktok"),
            has_blog=features.get("has_blog", False),
            has_contact_form=features.get("has_contact_form", False),
            has_property_search=features.get("has_property_search", False),
            has_mortgage_services=features.get("has_mortgage_services", False),
            has_property_management=features.get("has_property_management", False),
            has_commercial_services=features.get("has_commercial_services", False),
            has_luxury_division=features.get("has_luxury_division", False),
            has_careers_page=features.get("has_careers_page", False),
            has_multiple_offices=has_multiple_offices,
            business_intelligence_confidence=confidence
        )

    def _estimate_agent_count(self, html_pages: List[str]) -> Optional[int]:
        """
        Estimates the count of agents listed on roster and team pages without guessing.
        """
        counts = []
        for html in html_pages:
            # 1. Look for mailto links to capture distinct agent listings
            mailtos = set()
            for email in re.findall(r'href=["\']mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']', html, re.IGNORECASE):
                email_lower = email.lower()
                if not any(prefix in email_lower for prefix in ["info@", "office@", "contact@", "support@", "sales@", "admin@", "careers@", "jobs@"]):
                    mailtos.add(email_lower)
            
            # 2. Look for links to dedicated agent biographies
            agent_profile_regex = re.compile(r'href=["\']([^"\']*(?:/agent/|/agents/|/team/|/our-team/|/staff/)[a-zA-Z0-9-]+)["\']', re.IGNORECASE)
            agent_links = set(agent_profile_regex.findall(html))

            # 3. Look for standard CSS card wrappers
            card_regex = re.compile(r'class=["\'][^"\']*(?:agent-card|team-member|agent-info|staff-card|agent-profile|our-agent)["\']', re.IGNORECASE)
            cards = len(card_regex.findall(html))

            signals = []
            if len(mailtos) > 1:
                signals.append(len(mailtos))
            if len(agent_links) > 1:
                signals.append(len(agent_links))
            if cards > 1:
                signals.append(cards)

            if signals:
                counts.append(max(signals))

        return max(counts) if counts else None

    def _estimate_office_count(self, html_pages: List[str]) -> Tuple[Optional[int], bool]:
        """
        Estimates the count of distinct offices based on unique geographical zip codes.
        """
        all_zips = set()
        states_regex = r'\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)'
        zip_pattern = re.compile(r'\b(?:' + states_regex + r')\s+(\d{5})\b', re.IGNORECASE)
        
        for html in html_pages:
            # Extract standard state-zip format
            zips = zip_pattern.findall(html)
            for z in zips:
                all_zips.add(z)

        if len(all_zips) > 1:
            return len(all_zips), True
        elif len(all_zips) == 1:
            return 1, False
        return None, False

    def _estimate_years_in_business(self, html_pages: List[str]) -> Optional[int]:
        """
        Estimates years in business from common established/founding phrases.
        """
        years = []
        pattern = re.compile(r'\b(?:founded\s+in|serving\s+since|established(?:\s+in)?|since)\s+(18\d{2}|19\d{2}|20[0-2]\d)\b', re.IGNORECASE)
        
        for html in html_pages:
            matches = pattern.findall(html)
            for yr in matches:
                years.append(int(yr))

        if years:
            founding_year = min(years)
            current_year = 2026  # Anchored to system current local time context
            return max(0, current_year - founding_year)
        return None

    def _extract_social_links(self, html_pages: List[str]) -> Dict[str, str]:
        """
        Extracts verified links to common social media profiles.
        """
        socials = {}
        patterns = {
            "linkedin": r'href=["\'](https?://(?:www\.)?linkedin\.com/(?:company|in)/[^"\']+)["\']',
            "facebook": r'href=["\'](https?://(?:www\.)?facebook\.com/[^"\']+)["\']',
            "instagram": r'href=["\'](https?://(?:www\.)?instagram\.com/[^"\']+)["\']',
            "youtube": r'href=["\'](https?://(?:www\.)?youtube\.com/[^"\']+)["\']',
            "x": r'href=["\'](https?://(?:www\.)?(?:twitter|x)\.com/[^"\']+)["\']',
            "tiktok": r'href=["\'](https?://(?:www\.)?tiktok\.com/[^"\']+)["\']'
        }

        for platform, regex in patterns.items():
            for html in html_pages:
                matches = re.findall(regex, html, re.IGNORECASE)
                valid_matches = []
                for m in matches:
                    if not any(kw in m.lower() for kw in ["share", "intent", "login", "signup", "pages"]):
                        valid_matches.append(m.strip())
                if valid_matches:
                    socials[platform] = valid_matches[0]
                    break
        return socials

    def _detect_features(self, html_pages: List[str]) -> Dict[str, bool]:
        """
        Evaluates presence of key real estate features and digital offerings.
        """
        features = {
            "has_property_search": False,
            "has_mortgage_services": False,
            "has_property_management": False,
            "has_commercial_services": False,
            "has_luxury_division": False,
            "has_blog": False,
            "has_careers_page": False,
            "has_contact_form": False
        }

        combined_html = "\n".join(html_pages).lower()

        if any(kw in combined_html for kw in ["property search", "search properties", "search homes", "idx search", "mls search"]):
            features["has_property_search"] = True
        if any(kw in combined_html for kw in ["mortgage", "home loan", "financing", "mortgage calculator"]):
            features["has_mortgage_services"] = True
        if any(kw in combined_html for kw in ["property management", "manage property", "rental management"]):
            features["has_property_management"] = True
        if any(kw in combined_html for kw in ["commercial", "commercial real estate", "retail space", "office space"]):
            features["has_commercial_services"] = True
        if any(kw in combined_html for kw in ["luxury", "luxury division", "luxury homes", "fine estates"]):
            features["has_luxury_division"] = True
        if any(kw in combined_html for kw in ["/blog", "latest news", "our blog", "news & articles"]):
            features["has_blog"] = True
        if any(kw in combined_html for kw in ["careers", "join our team", "hiring", "join us", "jobs"]):
            features["has_careers_page"] = True
        if "<form" in combined_html and any(kw in combined_html for kw in ["name", "email", "message", "submit"]):
            features["has_contact_form"] = True

        return features

    def _compute_confidence(
        self,
        agent_count: Optional[int],
        office_count: Optional[int],
        years_in_business: Optional[int],
        socials: Dict[str, str],
        features: Dict[str, bool]
    ) -> str:
        """
        Determines the confidence rating (High, Medium, Low) based on active signals.
        """
        points = 0
        if agent_count is not None:
            points += 2
        if office_count is not None:
            points += 2
        if years_in_business is not None:
            points += 2
        
        # Social links weight
        if len(socials) > 1:
            points += 2
        elif len(socials) == 1:
            points += 1

        # Feature count weight
        detected_features_count = sum(1 for v in features.values() if v)
        if detected_features_count > 3:
            points += 2
        elif detected_features_count > 1:
            points += 1

        if points >= 6:
            return "High"
        elif points >= 3:
            return "Medium"
        return "Low"
