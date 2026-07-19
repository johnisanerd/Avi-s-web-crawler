from dataclasses import replace
from typing import Dict, List
from urllib.parse import urlparse

from src.models import Lead
from src.email_extractor import EmailExtractor, ExtractionResult
from src.logger import get_logger

logger = get_logger("enrichment")


class LeadEnricher:
    """
    Responsible for enriching Lead records with business email and owner details
    extracted from the leads' websites.
    """

    def __init__(self, timeout_secs: int = 10, max_pages: int = 10):
        self.extractor = EmailExtractor(timeout_secs=timeout_secs, max_pages=max_pages)
        self.domain_cache: Dict[str, ExtractionResult] = {}

    def enrich_leads(self, leads: List[Lead]) -> List[Lead]:
        """
        Processes a collection of Lead objects, fetching and appending contact
        and owner details to each record. Caches results by domain to optimize requests.
        """
        logger.info(f"Beginning contact enrichment on {len(leads)} leads...")
        enriched_leads: List[Lead] = []

        for lead in leads:
            if not lead.website:
                enriched_leads.append(lead)
                continue

            # Extract domain to perform caching checks
            parsed_url = urlparse(lead.website)
            domain = (parsed_url.netloc or parsed_url.path).lower().strip()
            if not domain:
                enriched_leads.append(lead)
                continue

            if domain not in self.domain_cache:
                logger.info(f"Extracting contact info from website: {lead.website}")
                try:
                    res = self.extractor.extract_from_website(lead.website)
                    self.domain_cache[domain] = res
                except Exception as e:
                    logger.warning(f"Error enriching site {lead.website}: {e}")
                    # Cache empty result to prevent repeating failed calls
                    self.domain_cache[domain] = ExtractionResult([], None, None, None, None)
            else:
                logger.info(f"Cache hit: Reusing contact details for domain {domain}")

            res = self.domain_cache[domain]

            # Return a copy of the Lead with enriched fields
            enriched = replace(
                lead,
                business_email=res.best_email,
                owner_name=res.owner_name,
                owner_title=res.owner_title,
                owner_email=res.owner_email
            )
            enriched_leads.append(enriched)

        logger.info("Lead contact details enrichment completed.")
        return enriched_leads
