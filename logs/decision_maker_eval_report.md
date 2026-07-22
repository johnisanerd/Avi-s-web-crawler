# Decision Maker Intelligence Evaluation Report

**Benchmark Dataset:** `data\benchmarks\benchmark_small.json` (v1.0.0)
**Timestamp:** `2026-07-22 11:43:47` | **Config Version:** `1.0.0`

## Executive Quality Summary

| Metric | Current Value | Delta vs Prev Run | Target |
| :--- | :---: | :---: | :---: |
| **Decision Maker Accuracy** | **100.0%** | `+0.0%` | `>= 95.0%` |
| **Email Verification Precision** | **100.0%** | `+0.0%` | `>= 98.0%` |
| **False Positive Rate** | **0.0%** | `+0.0%` | `<= 1.0%` |
| **False Negative Rate** | **0.0%** | `+0.0%` | `<= 5.0%` |
| **Average Latency per Lead** | **16.29 ms** | `-128.58 ms` | `<= 10.0 ms` |
| **Peak Memory Usage** | **0.1 MB** | - | - |

## Failure Taxonomy

| Failure Category | Count | Percentage |
| :--- | :---: | :---: |
| Wrong Decision Maker | 0 | 0.0% |
| Wrong Title | 0 | 0.0% |
| Wrong Email | 0 | 0.0% |
| Generic Email Accepted | 0 | 0.0% |
| Confidence Too High | 0 | 0.0% |
| Confidence Too Low | 0 | 0.0% |
| Candidate Conflict | 0 | 0.0% |
| No Decision Maker Found | 0 | 0.0% |
| Parser Failure | 0 | 0.0% |
| Email Matcher Failure | 0 | 0.0% |

## Confidence Calibration

| Confidence Bucket | Total Evaluated | Correct | Accuracy |
| :--- | :---: | :---: | :---: |
| 90-100 | 3 | 3 | 100.0% |
| 80-89 | 0 | 0 | 0.0% |
| 70-79 | 0 | 0 | 0.0% |
| <70 | 2 | 2 | 100.0% |
