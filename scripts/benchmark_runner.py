"""
CLI benchmark runner script for Decision Maker Intelligence evaluation.
Allows selecting benchmark tiers (small, medium, large, edge_cases, known_failures),
executing evaluations, and outputting performance profile metrics.
"""

import argparse
import sys
from pathlib import Path

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluator import DecisionMakerEvaluator
from src.logger import get_logger

logger = get_logger("benchmark_runner")


def main():
    parser = argparse.ArgumentParser(description="Decision Maker Intelligence Benchmark Runner")
    parser.add_argument(
        "--tier",
        type=str,
        default="small",
        choices=["small", "medium", "large", "edge_cases", "known_failures"],
        help="Benchmark tier to execute"
    )
    args = parser.parse_args()

    benchmark_path = Path(f"data/benchmarks/benchmark_{args.tier}.json")
    if not benchmark_path.exists():
        # Fallback to small tier if specific tier file does not exist yet
        benchmark_path = Path("data/benchmarks/benchmark_small.json")

    logger.info(f"Executing benchmark runner on tier: {args.tier} ({benchmark_path})")

    evaluator = DecisionMakerEvaluator(benchmark_file=benchmark_path)
    res = evaluator.run_evaluation()

    m = res["metrics"]
    print("\n" + "=" * 55)
    print(f" BENCHMARK RUNNER SUMMARY ({args.tier.upper()} TIER)")
    print("=" * 55)
    print(f" Total Companies Evaluated : {m['total_companies']}")
    print(f" Decision Maker Accuracy   : {m['decision_maker_accuracy_pct']}%")
    print(f" Email Precision          : {m['email_verification_precision_pct']}%")
    print(f" False Positive Rate       : {m['false_positive_rate_pct']}%")
    print(f" False Negative Rate       : {m['false_negative_rate_pct']}%")
    print(f" Avg Processing Time       : {m['avg_processing_time_ms']} ms/lead")
    print(f" Peak Memory Usage         : {m['peak_memory_mb']} MB")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
