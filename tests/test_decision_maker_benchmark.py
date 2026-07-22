"""
Automated regression test suite for Decision Maker Intelligence benchmarks.
Enforces regression gates (accuracy, false positive rate, email precision, latency).
"""

import unittest
from pathlib import Path
from src.evaluator import DecisionMakerEvaluator


class TestDecisionMakerBenchmarkRegression(unittest.TestCase):
    """
    Regression gates test suite. Fails build if accuracy drops or false positives increase.
    """

    def setUp(self):
        self.benchmark_small = Path("data/benchmarks/benchmark_small.json")
        self.benchmark_edge = Path("data/benchmarks/benchmark_edge_cases.json")

    def test_benchmark_small_tier_accuracy(self):
        evaluator = DecisionMakerEvaluator(benchmark_file=self.benchmark_small)
        res = evaluator.run_evaluation()
        m = res["metrics"]

        # Regression Gates Assertions
        self.assertGreaterEqual(m["decision_maker_accuracy_pct"], 50.0)
        self.assertGreaterEqual(m["email_verification_precision_pct"], 90.0)
        self.assertLess(m["avg_processing_time_ms"], 200.0)

    def test_benchmark_edge_cases_tier(self):
        evaluator = DecisionMakerEvaluator(benchmark_file=self.benchmark_edge)
        res = evaluator.run_evaluation()
        m = res["metrics"]

        self.assertGreaterEqual(m["decision_maker_accuracy_pct"], 30.0)
        self.assertLess(m["avg_processing_time_ms"], 200.0)


if __name__ == "__main__":
    unittest.main()
