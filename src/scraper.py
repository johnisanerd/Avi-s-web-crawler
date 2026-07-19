import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List
import requests

from src.models import RawLead
from src.config import Config
from src.constants import DEFAULT_POLL_INTERVAL_SECS
from src.logger import get_logger
from src.mappers import dict_to_raw_lead

logger = get_logger("scraper")


class LeadScraper(ABC):
    """
    Abstract base class representing a generic lead scraper interface.
    Allows the pipeline to remain provider-agnostic.
    """

    @abstractmethod
    def scrape_leads(self, config: Config) -> List[RawLead]:
        """
        Triggers the scraper run, polls for completion, and downloads
        the raw leads dataset.

        Args:
            config: A validated Config instance.

        Returns:
            A list of RawLead objects representing the unnormalized data.
        """
        pass


class ApifyGoogleMapsScraper(LeadScraper):
    """
    Apify implementation of the LeadScraper interface.
    Communicates with the Apify REST API to run the Google Maps Scraper Actor.
    """

    def __init__(self, request_timeout_secs: int = 30):
        self.request_timeout_secs = request_timeout_secs

    def _send_request(
        self,
        method: str,
        url: str,
        retry_count: int,
        **kwargs: Any
    ) -> requests.Response:
        """
        Sends an HTTP request with exponential backoff retries for transient failures.
        """
        last_error = None
        for attempt in range(retry_count + 1):
            try:
                response = requests.request(
                    method,
                    url,
                    timeout=self.request_timeout_secs,
                    **kwargs
                )
                # Retry for rate limits (429) or server errors (5xx)
                if response.status_code in [429, 500, 502, 503, 504]:
                    logger.warning(
                        f"HTTP status {response.status_code} received. "
                        f"Retrying request (attempt {attempt + 1}/{retry_count})..."
                    )
                    time.sleep(2 ** attempt)
                    continue
                
                response.raise_for_status()
                return response
            except (requests.RequestException, Exception) as e:
                last_error = e
                logger.warning(
                    f"HTTP request failed: {e}. "
                    f"Retrying request (attempt {attempt + 1}/{retry_count})..."
                )
                time.sleep(2 ** attempt)

        raise RuntimeError(
            f"HTTP request failed after {retry_count} retries. "
            f"Last error: {last_error}"
        )

    def scrape_leads(self, config: Config) -> List[RawLead]:
        """
        Orchestrates running the Google Maps Scraper actor on the Apify platform.
        Combines queries and locations, starts a run, polls until finished,
        and retrieves the final dataset.
        """
        actor_path = config.apify_actor_id.replace("/", "~")
        run_url = f"https://api.apify.com/v2/acts/{actor_path}/runs?token={config.apify_token}"
        
        # Combine search queries and locations
        search_strings = []
        for query in config.search_queries:
            for location in config.locations:
                search_strings.append(f"{query} in {location}")

        logger.info(
            f"Initializing scraper run with {len(search_strings)} search strings "
            f"for actor '{config.apify_actor_id}'."
        )

        payload = {
            "searchStringsArray": search_strings,
            "maxCrawledPlacesPerSearch": config.max_results_per_query,
            "language": "en",
            "scrapeResponseHeaders": False,
        }

        # 1. Trigger the run
        logger.info("Triggering actor run on Apify...")
        response = self._send_request(
            "POST",
            run_url,
            retry_count=config.retry_count,
            json=payload
        )
        
        run_data = response.json().get("data", {})
        run_id = run_data.get("id")
        dataset_id = run_data.get("defaultDatasetId")
        status = run_data.get("status")

        if not run_id or not dataset_id:
            raise RuntimeError("Failed to retrieve Run ID or Dataset ID from Apify response.")

        logger.info(f"Apify run triggered. Run ID: {run_id} | Dataset ID: {dataset_id}")

        # 2. Poll for status
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={config.apify_token}"
        abort_url = f"https://api.apify.com/v2/actor-runs/{run_id}/abort?token={config.apify_token}"
        
        start_time = time.time()
        max_wait_secs = config.timeout_mins * 60

        try:
            while status not in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                elapsed = time.time() - start_time
                if elapsed > max_wait_secs:
                    logger.error(f"Apify run timed out after {config.timeout_mins} minutes.")
                    self._abort_run(abort_url, config.retry_count)
                    raise TimeoutError(f"Scraper run {run_id} timed out.")

                logger.info(
                    f"Polling run status (elapsed: {int(elapsed)}s)... "
                    f"Current status: {status}"
                )
                time.sleep(DEFAULT_POLL_INTERVAL_SECS)

                status_response = self._send_request(
                    "GET",
                    status_url,
                    retry_count=config.retry_count
                )
                status = status_response.json().get("data", {}).get("status")

        except KeyboardInterrupt:
            logger.warning(
                f"KeyboardInterrupt received. Attempting to abort Apify run: {run_id}..."
            )
            self._abort_run(abort_url, config.retry_count)
            raise

        logger.info(f"Scraper run finished with final status: {status}")

        if status != "SUCCEEDED":
            raise RuntimeError(f"Apify scraper run did not succeed. Final status: {status}")

        # 3. Retrieve dataset
        dataset_url = (
            f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            f"?token={config.apify_token}&clean=true"
        )
        logger.info("Downloading raw dataset items...")
        dataset_response = self._send_request(
            "GET",
            dataset_url,
            retry_count=config.retry_count
        )
        
        raw_items: List[Dict[str, Any]] = dataset_response.json()
        logger.info(f"Successfully downloaded {len(raw_items)} raw lead records.")

        # 4. Map to RawLead data contracts
        raw_leads = [dict_to_raw_lead(item) for item in raw_items]
        return raw_leads

    def _abort_run(self, abort_url: str, retry_count: int) -> None:
        """
        Sends an abort request to stop a running actor instance on Apify.
        """
        try:
            self._send_request("POST", abort_url, retry_count=retry_count)
            logger.info("Successfully sent abort signal to Apify.")
        except Exception as e:
            logger.warning(f"Could not abort actor run: {e}")
