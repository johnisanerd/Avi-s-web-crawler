import argparse
import sys
from src.config import Config
from src.pipeline import LeadGenerationPipeline
from src.logger import get_logger

logger = get_logger("main")


def main() -> None:
    """
    Application entry point. Parses CLI overrides, instantiates Config,
    runs the execution pipeline, and reports a summary with exit codes.
    """
    parser = argparse.ArgumentParser(
        description="Production-grade real estate lead generator utilizing Apify Google Maps Scraper."
    )
    parser.add_argument(
        "--queries",
        type=str,
        help="Comma-separated search queries (e.g. 'realty, real estate agent')"
    )
    parser.add_argument(
        "--locations",
        type=str,
        help="Comma-separated locations (e.g. 'Miami FL, Tampa FL')"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        help="Maximum results to crawl per search query"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="Apify API Token override"
    )
    parser.add_argument(
        "--min-similarity",
        type=int,
        help="Fuzzy matching similarity threshold override (0-100)"
    )

    args = parser.parse_args()

    # Build overrides dictionary mapping CLI input to configuration properties
    overrides = {}
    if args.queries:
        overrides["queries"] = args.queries
    if args.locations:
        overrides["locations"] = args.locations
    if args.max_results:
        overrides["max_results"] = args.max_results
    if args.token:
        overrides["token"] = args.token
    if args.min_similarity is not None:
        overrides["min_similarity"] = args.min_similarity

    # 1. Load and validate Config
    try:
        config = Config.load(overrides)
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    # 2. Run the pipeline stages
    try:
        pipeline = LeadGenerationPipeline(config)
        result = pipeline.run()
    except TimeoutError as e:
        logger.critical(f"Scraper execution timed out: {e}")
        sys.exit(2)
    except RuntimeError as e:
        err_msg = str(e).lower()
        if "scraper" in err_msg or "apify" in err_msg:
            logger.critical(f"Scraper operation failed: {e}")
            sys.exit(2)
        elif "process" in err_msg or "dedup" in err_msg:
            logger.critical(f"Data processing operation failed: {e}")
            sys.exit(3)
        elif "export" in err_msg or "csv" in err_msg or "xlsx" in err_msg:
            logger.critical(f"File export operation failed: {e}")
            sys.exit(4)
        else:
            logger.critical(f"Unexpected operational pipeline failure: {e}")
            sys.exit(5)
    except Exception as e:
        logger.critical(f"Unexpected pipeline exception: {e}", exc_info=True)
        sys.exit(5)

    # 3. Print the execution summary report
    if result.success:
        print("\n" + "=" * 45)
        print("         LEAD GENERATION RUN SUMMARY")
        print("=" * 45)
        print(f"Downloaded Records : {result.downloaded_count}")
        print(f"Processed Records  : {result.processed_count}")
        print(f"Filtered Records   : {result.filtered_count}")
        print(f"Duplicates Removed : {result.duplicates_removed}")
        print(f"Exported Records   : {result.exported_count}")
        print(f"Output Directory   : {result.output_dir.resolve()}")
        print(f"Total Runtime      : {result.duration_secs:.2f} seconds")
        print("=" * 45)
        sys.exit(0)
    else:
        logger.error("Pipeline run completed but reported a non-success status.")
        sys.exit(5)


if __name__ == "__main__":
    main()
