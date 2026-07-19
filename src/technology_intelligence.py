from dataclasses import replace
from typing import Dict, List, Optional
from urllib.parse import urlparse

from src.models import Lead
from src.email_extractor import ExtractionResult
from src import constants
from src.logger import get_logger

logger = get_logger("technology_intelligence")


class TechnologyIntelligence:
    """
    Identifies software platforms, plugins, and third-party tools used by a
    brokerage's public website using only pre-downloaded cached HTML.
    """

    def __init__(self) -> None:
        self.model_version = constants.TECHNOLOGY_MODEL_VERSION
        self.signatures = constants.TECH_SIGNATURES
        self.confidence_thresholds = constants.TECHNOLOGY_CONFIDENCE_THRESHOLDS

    def detect_leads(self, leads: List[Lead], domain_cache: Dict[str, ExtractionResult]) -> List[Lead]:
        """
        Orchestrates technology detection for a collection of Lead objects, utilizing
        downloaded HTML stored in the domain cache to avoid duplicate HTTP requests.
        """
        logger.info(f"Detecting website technologies for {len(leads)} leads...")
        detected_leads: List[Lead] = []

        for lead in leads:
            try:
                # Retrieve cached page content from enrichment domain cache
                if lead.website:
                    parsed_url = urlparse(lead.website)
                    domain = (parsed_url.netloc or parsed_url.path).lower().strip()
                else:
                    domain = ""

                extraction_res = domain_cache.get(domain) if domain else None
                html_pages = extraction_res.html_pages if extraction_res else []

                detected = self.detect_lead(lead, html_pages)
                detected_leads.append(detected)
            except Exception as e:
                logger.error(f"Failed to detect technologies for lead {lead.business_name}: {e}")
                detected_leads.append(lead)

        logger.info("Technology intelligence detection complete.")
        return detected_leads

    def detect_lead(self, lead: Lead, html_pages: List[str]) -> Lead:
        """
        Scans pre-downloaded HTML pages for configured technology signatures.
        """
        if not html_pages:
            return replace(
                lead,
                website_platform=None,
                cms=None,
                idx_provider=None,
                crm_platform=None,
                analytics_tools=None,
                marketing_tools=None,
                chat_provider=None,
                form_provider=None,
                consent_manager=None,
                cdn_provider=None,
                technology_confidence="Low",
                technology_reasoning=["No website content available for analysis"],
                technology_model_version=self.model_version
            )

        # 1. Match all signatures against downloaded HTML pages
        matched_sigs_per_tech: Dict[str, set[str]] = {}

        for html in html_pages:
            for tech_name, info in self.signatures.items():
                sigs = info.get("signatures", [])
                for sig in sigs:
                    if sig in html:
                        if tech_name not in matched_sigs_per_tech:
                            matched_sigs_per_tech[tech_name] = set()
                        matched_sigs_per_tech[tech_name].add(sig)

        # 2. Group matches by categories
        category_matches: Dict[str, Dict[str, int]] = {
            "cms": {},
            "idx_provider": {},
            "crm_platform": {},
            "analytics_tools": {},
            "marketing_tools": {},
            "chat_provider": {},
            "form_provider": {},
            "consent_manager": {},
            "cdn_provider": {}
        }

        for tech_name, sigs in matched_sigs_per_tech.items():
            category = self.signatures[tech_name]["category"]
            if category in category_matches:
                category_matches[category][tech_name] = len(sigs)

        # 3. Determine values for each category field
        # Single-valued categories select the technology with the highest match count
        def get_best_match(category_dict: Dict[str, int]) -> Optional[str]:
            if not category_dict:
                return None
            return max(category_dict, key=category_dict.get)

        # Multi-valued categories join all matched technologies with commas
        def get_all_matches(category_dict: Dict[str, int]) -> Optional[str]:
            if not category_dict:
                return None
            return ", ".join(sorted(category_dict.keys()))

        cms_tech = get_best_match(category_matches["cms"])
        idx_tech = get_best_match(category_matches["idx_provider"])
        crm_tech = get_best_match(category_matches["crm_platform"])
        chat_tech = get_best_match(category_matches["chat_provider"])
        consent_tech = get_best_match(category_matches["consent_manager"])
        cdn_tech = get_best_match(category_matches["cdn_provider"])

        analytics_techs = get_all_matches(category_matches["analytics_tools"])
        marketing_techs = get_all_matches(category_matches["marketing_tools"])
        form_techs = get_all_matches(category_matches["form_provider"])

        # 4. Generate explainable reasoning and compute overall confidence
        reasoning: List[str] = []
        highest_match_count = 0

        for tech_name in sorted(matched_sigs_per_tech.keys()):
            sigs = matched_sigs_per_tech[tech_name]
            match_count = len(sigs)
            if match_count > highest_match_count:
                highest_match_count = match_count
            for sig in sorted(sigs):
                reasoning.append(f"Detected {tech_name} via signature: '{sig}'")

        if not reasoning:
            reasoning.append("No technology signatures detected")
            confidence = "Low"
        else:
            high_threshold = self.confidence_thresholds.get("High", 2)
            med_threshold = self.confidence_thresholds.get("Medium", 1)
            
            if highest_match_count >= high_threshold:
                confidence = "High"
            elif highest_match_count >= med_threshold:
                confidence = "Medium"
            else:
                confidence = "Low"

        return replace(
            lead,
            website_platform=cms_tech,
            cms=cms_tech,
            idx_provider=idx_tech,
            crm_platform=crm_tech,
            analytics_tools=analytics_techs,
            marketing_tools=marketing_techs,
            chat_provider=chat_tech,
            form_provider=form_techs,
            consent_manager=consent_tech,
            cdn_provider=cdn_tech,
            technology_confidence=confidence,
            technology_reasoning=reasoning,
            technology_model_version=self.model_version
        )
