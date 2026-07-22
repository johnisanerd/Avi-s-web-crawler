"""
Unit tests for Decision Maker Intelligence final production refinements.
Covers integer confidence, content-hashed caching, candidate merging, scoring breakdown,
HTML pre-normalization, precompiled regex, strict name validation, processing timers,
cache stats, email match trace, and fail-safe exception handling.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src.models import (
    Lead,
    RawLead,
    PageBlock,
    DecisionMakerCandidate,
    DecisionMaker,
    WebsiteSnapshot
)
from src.email_utils import (
    normalize_email,
    is_generic_email,
    is_personal_email,
    match_email_to_name
)
from src.html_parser import parse_html_to_blocks, classify_page_type, normalize_html_text
from src.decision_maker_intelligence import DecisionMakerIntelligence
from src.config import Config
from src.pipeline import LeadGenerationPipeline


class TestEmailUtils(unittest.TestCase):
    """
    Tests for email normalization, generic detection, and multi-strategy matching trace.
    """

    def test_normalize_email(self):
        self.assertEqual(normalize_email("  JOHN@Company.COM  "), "john@company.com")
        self.assertEqual(normalize_email("mailto:John.Smith@Company.com"), "john.smith@company.com")
        self.assertEqual(normalize_email(""), "")

    def test_is_generic_email(self):
        self.assertTrue(is_generic_email("info@company.com"))
        self.assertTrue(is_generic_email("office@company.com"))
        self.assertTrue(is_generic_email("hello@company.com"))
        self.assertTrue(is_generic_email("contact@company.com"))
        self.assertTrue(is_generic_email("support@company.com"))
        self.assertTrue(is_generic_email("admin@company.com"))

        self.assertFalse(is_generic_email("john@company.com"))
        self.assertFalse(is_generic_email("john.smith@company.com"))
        self.assertFalse(is_generic_email("jsmith@company.com"))

    def test_is_personal_email(self):
        self.assertTrue(is_personal_email("john.smith@company.com"))
        self.assertFalse(is_personal_email("info@company.com"))
        self.assertFalse(is_personal_email("invalid-email"))

    def test_multi_strategy_matching(self):
        name = "John Smith"
        
        matched, strat, weight = match_email_to_name("john.smith@company.com", name)
        self.assertTrue(matched)
        self.assertEqual(strat, "FIRST_DOT_LAST")

        matched, strat, weight = match_email_to_name("johnsmith@company.com", name)
        self.assertTrue(matched)
        self.assertEqual(strat, "EXACT_FULL_NAME")

        matched, strat, weight = match_email_to_name("jsmith@company.com", name)
        self.assertTrue(matched)
        self.assertEqual(strat, "FIRST_INITIAL_LAST")

        matched, strat, weight = match_email_to_name("john@company.com", name)
        self.assertTrue(matched)
        self.assertEqual(strat, "FIRST_NAME")


class TestHTMLParserAndNormalization(unittest.TestCase):
    """
    Tests for HTML pre-normalization and PageBlock parsing.
    """

    def test_normalize_html_text(self):
        raw = "Hello&nbsp;World!&amp;&ldquo;Quotes&rdquo;\r\nNew Line"
        normalized = normalize_html_text(raw)
        self.assertIn("Hello World!&\"Quotes\"", normalized)
        self.assertNotIn("&nbsp;", normalized)
        self.assertNotIn("\r", normalized)

    def test_parse_html_to_blocks(self):
        html = """
        <html>
            <body>
                <h1>About Our Leadership</h1>
                <div class="team-member">
                    <h2>Jane Doe</h2>
                    <p>Founder & Principal Broker</p>
                    <a href="mailto:jane@example.com">Email Jane</a>
                </div>
                <footer>
                    <p>Contact info@example.com</p>
                </footer>
            </body>
        </html>
        """
        blocks = parse_html_to_blocks("http://example.com/about", html)
        self.assertGreater(len(blocks), 0)


class TestDecisionMakerIntelligenceProduction(unittest.TestCase):
    """
    Tests for Decision Maker Intelligence production features.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"
        self.engine = DecisionMakerIntelligence(cache_dir=self.cache_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_integer_confidence_and_scoring_breakdown(self):
        html = """
        <html>
            <body>
                <div class="team-member">
                    <h2>Jane Doe</h2>
                    <p>Owner & Founder</p>
                    <a href="mailto:jane.doe@example.com">Email Jane</a>
                </div>
            </body>
        </html>
        """
        snapshot = WebsiteSnapshot(
            domain="example.com",
            pages={"http://example.com/about": html},
            social_profiles={"linkedin": "https://linkedin.com/in/janedoe"}
        )

        dm = self.engine.analyze_snapshot(snapshot)
        self.assertEqual(dm.status, "FOUND")
        self.assertIsInstance(dm.confidence_score, int)
        self.assertGreater(dm.confidence_score, 50)
        self.assertGreater(len(dm.evidence), 0)

    def test_strict_name_validation(self):
        # Reject candidates containing MLS, Privacy, Terms, Address terms
        html = """
        <div>
            <h2>MLS Terms Privacy</h2>
            <p>Founder</p>
        </div>
        <div>
            <h2>Jane Doe</h2>
            <p>Managing Broker</p>
        </div>
        """
        blocks = parse_html_to_blocks("http://example.com/about", html)
        candidates = self.engine.extract_candidates(blocks)
        validated = self.engine.validate_candidates(candidates)

        names = [c.name for c in validated]
        self.assertIn("Jane Doe", names)
        self.assertNotIn("MLS Terms Privacy", names)

    def test_candidate_merging_across_pages(self):
        html1 = "<p>Jane Doe - Owner</p>"
        html2 = "<p>Jane Doe - Owner</p>"
        blocks1 = parse_html_to_blocks("http://example.com/about", html1)
        blocks2 = parse_html_to_blocks("http://example.com/team", html2)

        candidates = self.engine.extract_candidates(blocks1 + blocks2)
        validated = self.engine.validate_candidates(candidates)
        merged = self.engine.merge_candidates(validated)

        # 2 extracted sightings should merge into 1 group
        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged[0][1]), 2)

    def test_content_hashed_caching_and_stats(self):
        html = "<p>Jane Doe - Owner</p><a href='mailto:jane@example.com'>Email</a>"
        snapshot = WebsiteSnapshot(
            domain="cachetest.com",
            pages={"http://cachetest.com/about": html},
            social_profiles={}
        )

        # First run -> cache miss
        dm1 = self.engine.analyze_snapshot(snapshot)
        self.assertEqual(self.engine.stats["cache_misses"], 1)

        # Second run -> content-hashed cache hit
        dm2 = self.engine.analyze_snapshot(snapshot)
        self.assertEqual(self.engine.stats["cache_hits"], 1)
        self.assertEqual(dm1.decision_maker_name, dm2.decision_maker_name)

        stats = self.engine.get_statistics()
        self.assertIn("avg_processing_time_ms", stats)
        self.assertIn("cache_hits", stats)

    def test_fail_safe_execution(self):
        # Malformed lead / invalid snapshot structure should not crash pipeline
        broken_lead = Lead(
            business_name="Broken Business",
            category="Broker",
            website="http://broken.com",
            phone="", street="", city="", state="", zip_code="", country="",
            rating=0.0, review_count=0, latitude=None, longitude=None,
            google_maps_url="", google_place_id=None, source_queries=set()
        )

        # Simulate exception during domain cache lookup
        broken_cache = {"broken.com": None}
        leads = self.engine.analyze_leads([broken_lead], broken_cache)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0].decision_maker.status, "NO_DECISION_MAKER")


class MockScraper:
    def scrape_leads(self, config):
        return [
            RawLead(
                title="Apex Realty Group",
                website="http://apexrealty.com",
                city="Austin",
                state="TX",
                phone="512-555-0100"
            )
        ]


class TestPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config(
            apify_token="mock_token",
            apify_actor_id="mock_actor",
            search_queries=["real estate austin"],
            locations=["Austin, TX"],
            max_results_per_query=10,
            timeout_mins=10,
            retry_count=3,
            log_level="INFO",
            data_dir=Path(self.temp_dir),
            raw_data_dir=Path(self.temp_dir) / "raw",
            processed_data_dir=Path(self.temp_dir) / "processed",
            output_data_dir=Path(self.temp_dir) / "output",
            logs_dir=Path(self.temp_dir) / "logs",
            cleaned_csv_name="clean.csv",
            cleaned_xlsx_name="clean.xlsx",
            clay_csv_name="clay.csv",
            min_similarity_score=85,
            excel_theme_color="1F4E79"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_pipeline_run_with_decision_maker_intelligence(self):
        pipeline = LeadGenerationPipeline(config=self.config, scraper=MockScraper())
        result = pipeline.run()
        self.assertTrue(result.success)
        self.assertEqual(result.exported_count, 1)

        csv_file = self.config.output_data_dir / "clean.csv"
        self.assertTrue(csv_file.exists())
        with open(csv_file, "r", encoding="utf-8") as f:
            header = f.readline()
            self.assertIn("Decision Maker Name", header)
            self.assertIn("Decision Maker Confidence", header)


if __name__ == "__main__":
    unittest.main()
