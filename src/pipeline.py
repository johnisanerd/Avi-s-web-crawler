import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from src.config import Config
from src.logger import get_logger
from src.scraper import LeadScraper, ApifyGoogleMapsScraper
from src.processor import process_leads
from src.exporter import LeadExporter
from src.enrichment import LeadEnricher
from src.lead_scorer import LeadScorer
from src.business_intelligence import BusinessIntelligence
from src.revenue_intelligence import RevenueIntelligence
from src.technology_intelligence import TechnologyIntelligence

logger = get_logger("pipeline")


@dataclass(slots=True)
class PipelineResult:
    """
    Holds structured execution summary details returned by the pipeline orchestrator.
    """
    success: bool
    start_time: str
    end_time: str
    duration_secs: float
    downloaded_count: int
    processed_count: int
    filtered_count: int
    duplicates_removed: int
    exported_count: int
    output_dir: Path
    warnings: List[str]


class LeadGenerationPipeline:
    """
    Coordinates and executes the end-to-end lead discovery pipeline.
    Ensures directories are initialized, scraper is run, raw JSON is preserved,
    leads are processed, and outputs are exported.
    """

    def __init__(self, config: Config, scraper: Optional[LeadScraper] = None):
        """
        Initializes the pipeline with configurations and optional scraper injector.
        """
        self.config = config
        self.scraper = scraper or ApifyGoogleMapsScraper()
        self.exporter = LeadExporter(config)

    def run(self) -> PipelineResult:
        """
        Executes the modular lead generation stages sequentially.

        Returns:
            A PipelineResult object summarizing the run statistics.

        Raises:
            Exception: If an unrecoverable failure occurs in any stage.
        """
        start_dt = datetime.now()
        start_time_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Starting lead generation pipeline at {start_time_str}...")

        warnings: List[str] = []
        downloaded_count = 0
        processed_count = 0
        filtered_count = 0
        duplicates_removed = 0
        exported_count = 0
        success = False

        try:
            # 1. Initialize data folders
            self.config.raw_data_dir.mkdir(parents=True, exist_ok=True)
            self.config.output_data_dir.mkdir(parents=True, exist_ok=True)
            self.config.logs_dir.mkdir(parents=True, exist_ok=True)

            # 2. Run the lead scraper
            logger.info("Stage 1/4: Scraping raw lead records...")
            raw_leads = self.scraper.scrape_leads(self.config)
            downloaded_count = len(raw_leads)

            # 3. Save raw leads copy to raw data folder
            logger.info("Stage 2/4: Saving immutable raw JSON dataset...")
            timestamp_str = start_dt.strftime("%Y%m%d_%H%M%S")
            raw_file_name = f"raw_leads_{timestamp_str}.json"
            raw_file_path = self.config.raw_data_dir / raw_file_name
            
            # Serialize RawLead dataclasses back to JSON dictionaries
            raw_leads_dict = [asdict(lead) for lead in raw_leads]
            with open(raw_file_path, "w", encoding="utf-8") as f:
                json.dump(raw_leads_dict, f, ensure_ascii=False, indent=2)
            logger.info(f"Raw leads saved to: {raw_file_path}")

            # 4. Invoke processing logic (translate, validate, normalize, filter, deduplicate)
            logger.info("Stage 3/4: Processing and deduplicating leads...")
            processing_res = process_leads(
                raw_leads=raw_leads,
                min_similarity_score=self.config.min_similarity_score,
                allowed_states=self.config.allowed_states,
                allowed_countries=self.config.allowed_countries
            )
            processed_leads = processing_res.leads
            processed_count = len(processed_leads)
            filtered_count = processing_res.filtered_count
            duplicates_removed = processing_res.duplicate_count

            if processing_res.validation_failures_count > 0:
                warn_msg = f"Skipped {processing_res.validation_failures_count} invalid raw records."
                logger.warning(warn_msg)
                warnings.append(warn_msg)

            # 4.5. Enrich leads with contact email and owner details
            logger.info("Enriching processed leads with website contact info...")
            enricher = LeadEnricher(timeout_secs=10)
            enriched_leads = enricher.enrich_leads(processed_leads)

            # 4.6. Profile leads with Business Intelligence engine
            logger.info("Profiling leads with business intelligence engine...")
            bi_engine = BusinessIntelligence()
            bi_leads = bi_engine.analyze_leads(enriched_leads, enricher.domain_cache)

            # 4.7. Compute opportunity scores and tiers
            logger.info("Computing opportunity scores and tiers for enriched leads...")
            scorer = LeadScorer()
            scored_leads = scorer.score_leads(bi_leads)

            # 4.8. Compute revenue intelligence metrics
            logger.info("Computing revenue intelligence metrics...")
            rev_engine = RevenueIntelligence()
            revenue_leads = rev_engine.estimate_leads(scored_leads)

            # 4.9. Compute technology intelligence metrics
            logger.info("Computing technology intelligence metrics...")
            tech_engine = TechnologyIntelligence()
            tech_leads = tech_engine.detect_leads(revenue_leads, enricher.domain_cache)

            # 5. Export results
            logger.info("Stage 4/4: Formatting and exporting spreadsheet outputs...")
            self.exporter.export_all(tech_leads)
            exported_count = len(tech_leads)
            success = True

        except Exception as e:
            logger.error(f"Pipeline run encountered an unrecoverable failure: {e}", exc_info=True)
            raise
        finally:
            end_dt = datetime.now()
            end_time_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            duration_secs = (end_dt - start_dt).total_seconds()
            logger.info(f"Pipeline finished execution at {end_time_str} (duration: {duration_secs:.2f}s).")

        return PipelineResult(
            success=success,
            start_time=start_time_str,
            end_time=end_time_str,
            duration_secs=duration_secs,
            downloaded_count=downloaded_count,
            processed_count=processed_count,
            filtered_count=filtered_count,
            duplicates_removed=duplicates_removed,
            exported_count=exported_count,
            output_dir=self.config.output_data_dir,
            warnings=warnings
        )
