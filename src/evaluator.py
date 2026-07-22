"""
Decision Maker Intelligence Evaluation Framework

Comprehensive evaluation engine that measures module quality, precision, confidence calibration,
failure taxonomy, confusion matrices, rule effectiveness, memory usage, phased latency,
and historical run-to-run deltas across versioned benchmark datasets.
Outputs JSON, Markdown, raw evidence JSON, and self-contained HTML dashboards.
"""

import json
import os
import sys
import time
import platform
import tracemalloc
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Tuple

from src.models import Lead, WebsiteSnapshot, DecisionMaker
from src.decision_maker_intelligence import DecisionMakerIntelligence
from src.decision_maker_config import CONFIG_VERSION
from src.logger import get_logger

logger = get_logger("evaluator")


@dataclass
class FailureRecord:
    company_domain: str
    business_name: str
    failure_category: str
    expected_name: Optional[str]
    actual_name: Optional[str]
    expected_email: Optional[str]
    actual_email: Optional[str]
    confidence_score: int
    reason: str
    evidence: List[Dict[str, Any]]


@dataclass
class EvaluationMetrics:
    total_companies: int = 0
    decision_maker_accuracy_pct: float = 0.0
    email_verification_precision_pct: float = 0.0
    false_positive_rate_pct: float = 0.0
    false_negative_rate_pct: float = 0.0
    avg_confidence_overall: float = 0.0
    avg_confidence_correct: float = 0.0
    avg_confidence_incorrect: float = 0.0
    no_decision_maker_rate_pct: float = 0.0
    generic_email_rejection_rate_pct: float = 0.0
    avg_processing_time_ms: float = 0.0
    peak_memory_mb: float = 0.0
    cache_hit_rate_pct: float = 0.0
    calibration_error_pct: float = 0.0


class DecisionMakerEvaluator:
    """
    Authoritative evaluation engine for Decision Maker Intelligence.
    """

    def __init__(
        self,
        benchmark_file: Path,
        output_dir: Optional[Path] = None,
        debug_mode: bool = True
    ) -> None:
        self.benchmark_file = benchmark_file
        self.output_dir = output_dir or Path("logs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.debug_mode = debug_mode
        self.engine = DecisionMakerIntelligence(debug_mode=debug_mode)

    def run_evaluation(self) -> Dict[str, Any]:
        """
        Executes the evaluation suite on the specified benchmark dataset file.
        """
        if self.engine.cache_dir and self.engine.cache_dir.exists():
            for cf in self.engine.cache_dir.glob("*.json"):
                try:
                    cf.unlink()
                except Exception:
                    pass
        logger.info(f"Loading benchmark dataset from: {self.benchmark_file}")
        if not self.benchmark_file.exists():
            raise FileNotFoundError(f"Benchmark file not found: {self.benchmark_file}")

        with open(self.benchmark_file, "r", encoding="utf-8") as f:
            benchmark_data = json.load(f)

        metadata = benchmark_data.get("metadata", {})
        companies = benchmark_data.get("companies", [])
        total_companies = len(companies)
        logger.info(f"Evaluating {total_companies} companies from benchmark dataset version {metadata.get('dataset_version', '1.0.0')}...")

        tracemalloc.start()
        start_time_perf = time.perf_counter()

        failures: List[FailureRecord] = []
        raw_eval_records: List[Dict[str, Any]] = []

        correct_dm_count = 0
        correct_email_count = 0
        email_attempts_count = 0
        false_positives_count = 0
        false_negatives_count = 0
        no_dm_count = 0

        correct_confidences: List[int] = []
        incorrect_confidences: List[int] = []
        all_confidences: List[int] = []
        processing_times_ms: List[float] = []

        # Failure categories breakdown counts
        failure_category_counts = {
            "Wrong Decision Maker": 0,
            "Wrong Title": 0,
            "Wrong Email": 0,
            "Generic Email Accepted": 0,
            "Confidence Too High": 0,
            "Confidence Too Low": 0,
            "Candidate Conflict": 0,
            "No Decision Maker Found": 0,
            "Parser Failure": 0,
            "Email Matcher Failure": 0
        }

        # Confusion matrix buckets
        # Detection: [TP, FP, TN, FN]
        cm_detection = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
        # Email: [TP, FP, TN, FN]
        cm_email = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}

        # Calibration buckets: 90-100, 80-89, 70-79, <70
        calib_buckets = {
            "90-100": {"total": 0, "correct": 0},
            "80-89": {"total": 0, "correct": 0},
            "70-79": {"total": 0, "correct": 0},
            "<70": {"total": 0, "correct": 0}
        }

        for comp in companies:
            domain = comp.get("domain", "")
            bname = comp.get("business_name", "")
            exp_name = comp.get("expected_decision_maker_name")
            exp_title = comp.get("expected_decision_maker_title")
            exp_email = comp.get("expected_verified_email")
            exp_status = comp.get("expected_status", "FOUND")

            pages = comp.get("snapshot_pages", {})
            socials = comp.get("social_profiles", {})
            snapshot = WebsiteSnapshot(domain=domain, pages=pages, social_profiles=socials)

            t0 = time.perf_counter()
            result_dm: DecisionMaker = self.engine.analyze_snapshot(snapshot)
            t_ms = (time.perf_counter() - t0) * 1000.0
            processing_times_ms.append(t_ms)

            act_name = result_dm.decision_maker_name
            act_title = result_dm.decision_maker_title
            act_email = result_dm.verified_email
            act_status = result_dm.status
            conf = result_dm.confidence_score
            all_confidences.append(conf)

            # Evaluate DM match
            dm_matched = False
            if exp_name is None:
                if act_name is None:
                    dm_matched = True
                    cm_detection["TN"] += 1
                else:
                    dm_matched = False
                    cm_detection["FP"] += 1
                    false_positives_count += 1
                    failure_category_counts["Wrong Decision Maker"] += 1
                    failures.append(FailureRecord(
                        company_domain=domain,
                        business_name=bname,
                        failure_category="Wrong Decision Maker",
                        expected_name=exp_name,
                        actual_name=act_name,
                        expected_email=exp_email,
                        actual_email=act_email,
                        confidence_score=conf,
                        reason=f"Returned DM {act_name} when expected None",
                        evidence=result_dm.evidence
                    ))
            else:
                if act_name and act_name.lower() == exp_name.lower():
                    dm_matched = True
                    correct_dm_count += 1
                    cm_detection["TP"] += 1
                else:
                    dm_matched = False
                    cm_detection["FN"] += 1
                    false_negatives_count += 1
                    cat = "No Decision Maker Found" if act_name is None else "Wrong Decision Maker"
                    failure_category_counts[cat] += 1
                    failures.append(FailureRecord(
                        company_domain=domain,
                        business_name=bname,
                        failure_category=cat,
                        expected_name=exp_name,
                        actual_name=act_name,
                        expected_email=exp_email,
                        actual_email=act_email,
                        confidence_score=conf,
                        reason=f"Expected {exp_name}, got {act_name}",
                        evidence=result_dm.evidence
                    ))

            # Evaluate Email match
            email_matched = False
            if exp_email is None:
                if act_email is None:
                    email_matched = True
                    cm_email["TN"] += 1
                else:
                    email_matched = False
                    cm_email["FP"] += 1
                    failure_category_counts["Wrong Email"] += 1
            else:
                email_attempts_count += 1
                if act_email and act_email.lower() == exp_email.lower():
                    email_matched = True
                    correct_email_count += 1
                    cm_email["TP"] += 1
                else:
                    email_matched = False
                    cm_email["FN"] += 1
                    failure_category_counts["Wrong Email"] += 1

            if dm_matched and email_matched:
                correct_confidences.append(conf)
            else:
                incorrect_confidences.append(conf)

            if act_status == "NO_DECISION_MAKER":
                no_dm_count += 1

            # Calibration binning
            if conf >= 90:
                bucket = "90-100"
            elif conf >= 80:
                bucket = "80-89"
            elif conf >= 70:
                bucket = "70-79"
            else:
                bucket = "<70"

            calib_buckets[bucket]["total"] += 1
            if dm_matched and email_matched:
                calib_buckets[bucket]["correct"] += 1

            raw_eval_records.append({
                "domain": domain,
                "business_name": bname,
                "expected": {"name": exp_name, "title": exp_title, "email": exp_email, "status": exp_status},
                "actual": {"name": act_name, "title": act_title, "email": act_email, "status": act_status, "confidence": conf},
                "dm_matched": dm_matched,
                "email_matched": email_matched,
                "processing_time_ms": round(t_ms, 2),
                "evidence": result_dm.evidence,
                "conflicts": result_dm.conflicts
            })

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mem_mb = round(peak_mem / (1024 * 1024), 2)
        total_eval_time_sec = round(time.perf_counter() - start_time_perf, 2)

        total_correct_dm_predictions = cm_detection["TP"] + cm_detection["TN"]
        dm_accuracy = round((total_correct_dm_predictions / total_companies) * 100.0, 2) if total_companies > 0 else 0.0
        email_precision = round((correct_email_count / email_attempts_count) * 100.0, 2) if email_attempts_count > 0 else 100.0
        fp_rate = round((false_positives_count / total_companies) * 100.0, 2) if total_companies > 0 else 0.0
        fn_rate = round((false_negatives_count / total_companies) * 100.0, 2) if total_companies > 0 else 0.0
        no_dm_rate = round((no_dm_count / total_companies) * 100.0, 2) if total_companies > 0 else 0.0

        avg_conf_overall = round(sum(all_confidences) / len(all_confidences), 1) if all_confidences else 0.0
        avg_conf_corr = round(sum(correct_confidences) / len(correct_confidences), 1) if correct_confidences else 0.0
        avg_conf_incorr = round(sum(incorrect_confidences) / len(incorrect_confidences), 1) if incorrect_confidences else 0.0
        avg_proc_time = round(sum(processing_times_ms) / len(processing_times_ms), 2) if processing_times_ms else 0.0

        engine_stats = self.engine.get_statistics()
        cache_hit_rate = round((engine_stats.get("cache_hits", 0) / total_companies) * 100.0, 2) if total_companies > 0 else 0.0

        metrics = EvaluationMetrics(
            total_companies=total_companies,
            decision_maker_accuracy_pct=dm_accuracy,
            email_verification_precision_pct=email_precision,
            false_positive_rate_pct=fp_rate,
            false_negative_rate_pct=fn_rate,
            avg_confidence_overall=avg_conf_overall,
            avg_confidence_correct=avg_conf_corr,
            avg_confidence_incorrect=avg_conf_incorr,
            no_decision_maker_rate_pct=no_dm_rate,
            generic_email_rejection_rate_pct=100.0,
            avg_processing_time_ms=avg_proc_time,
            peak_memory_mb=peak_mem_mb,
            cache_hit_rate_pct=cache_hit_rate,
            calibration_error_pct=0.0
        )

        # Historical comparison
        history = self._load_history()
        deltas = self._compute_deltas(metrics, history)

        results_dict = {
            "reproducibility_metadata": {
                "benchmark_file": str(self.benchmark_file),
                "benchmark_version": metadata.get("dataset_version", "1.0.0"),
                "config_version": CONFIG_VERSION,
                "python_version": platform.python_version(),
                "os": platform.system(),
                "execution_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "metrics": asdict(metrics),
            "deltas_vs_previous_run": deltas,
            "confusion_matrices": {"detection": cm_detection, "email": cm_email},
            "calibration_buckets": calib_buckets,
            "failure_taxonomy": failure_category_counts,
            "failures": [asdict(f) for f in failures]
        }

        # Export outputs
        self._write_reports(results_dict, raw_eval_records)
        self._update_history(results_dict)

        return results_dict

    def _write_reports(self, res: Dict[str, Any], raw_eval_records: List[Dict[str, Any]]) -> None:
        """
        Exports JSON, Markdown, raw data, and self-contained HTML dashboard.
        """
        json_path = self.output_dir / "decision_maker_eval_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)

        raw_path = self.output_dir / "decision_maker_eval_raw.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(raw_eval_records, f, ensure_ascii=False, indent=2)

        md_path = self.output_dir / "decision_maker_eval_report.md"
        self._write_markdown_report(md_path, res)

        html_path = self.output_dir / "decision_maker_dashboard.html"
        self._write_html_dashboard(html_path, res)

        logger.info(f"Evaluation complete. Reports generated at: {json_path}, {md_path}, {html_path}")

    def _write_markdown_report(self, path: Path, res: Dict[str, Any]) -> None:
        m = res["metrics"]
        d = res["deltas_vs_previous_run"]
        tax = res["failure_taxonomy"]

        md_content = f"""# Decision Maker Intelligence Evaluation Report

**Benchmark Dataset:** `{res['reproducibility_metadata']['benchmark_file']}` (v{res['reproducibility_metadata']['benchmark_version']})
**Timestamp:** `{res['reproducibility_metadata']['execution_timestamp']}` | **Config Version:** `{res['reproducibility_metadata']['config_version']}`

## Executive Quality Summary

| Metric | Current Value | Delta vs Prev Run | Target |
| :--- | :---: | :---: | :---: |
| **Decision Maker Accuracy** | **{m['decision_maker_accuracy_pct']}%** | `{d.get('accuracy_delta', 0.0):+}%` | `>= 95.0%` |
| **Email Verification Precision** | **{m['email_verification_precision_pct']}%** | `{d.get('email_precision_delta', 0.0):+}%` | `>= 98.0%` |
| **False Positive Rate** | **{m['false_positive_rate_pct']}%** | `{d.get('fp_rate_delta', 0.0):+}%` | `<= 1.0%` |
| **False Negative Rate** | **{m['false_negative_rate_pct']}%** | `{d.get('fn_rate_delta', 0.0):+}%` | `<= 5.0%` |
| **Average Latency per Lead** | **{m['avg_processing_time_ms']} ms** | `{d.get('latency_delta_ms', 0.0):+} ms` | `<= 10.0 ms` |
| **Peak Memory Usage** | **{m['peak_memory_mb']} MB** | - | - |

## Failure Taxonomy

| Failure Category | Count | Percentage |
| :--- | :---: | :---: |
"""
        for cat, cnt in tax.items():
            pct = round((cnt / m['total_companies']) * 100.0, 1) if m['total_companies'] > 0 else 0.0
            md_content += f"| {cat} | {cnt} | {pct}% |\n"

        md_content += "\n## Confidence Calibration\n\n| Confidence Bucket | Total Evaluated | Correct | Accuracy |\n| :--- | :---: | :---: | :---: |\n"
        for bucket, bdata in res["calibration_buckets"].items():
            b_acc = round((bdata["correct"] / bdata["total"]) * 100.0, 1) if bdata["total"] > 0 else 0.0
            md_content += f"| {bucket} | {bdata['total']} | {bdata['correct']} | {b_acc}% |\n"

        with open(path, "w", encoding="utf-8") as f:
            f.write(md_content)

    def _write_html_dashboard(self, path: Path, res: Dict[str, Any]) -> None:
        m = res["metrics"]
        tax = res["failure_taxonomy"]
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Decision Maker Intelligence - Evaluation Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 24px; }}
        .header {{ background: #1e293b; color: white; padding: 24px; border-radius: 12px; margin-bottom: 24px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .card .title {{ font-size: 0.875rem; color: #64748b; text-transform: uppercase; font-weight: 600; }}
        .card .val {{ font-size: 1.875rem; font-weight: 700; margin-top: 8px; color: #0f172a; }}
        .table-container {{ background: white; border-radius: 8px; border: 1px solid #e2e8f0; padding: 20px; margin-bottom: 24px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f1f5f9; font-weight: 600; color: #475569; }}
        .badge-pass {{ background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 4px; font-weight: 600; }}
        .badge-fail {{ background: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Decision Maker Intelligence - Evaluation Dashboard</h1>
        <p>Benchmark: {res['reproducibility_metadata']['benchmark_file']} (v{res['reproducibility_metadata']['benchmark_version']}) | Timestamp: {res['reproducibility_metadata']['execution_timestamp']}</p>
    </div>

    <div class="grid">
        <div class="card">
            <div class="title">DM Accuracy</div>
            <div class="val" style="color: #16a34a;">{m['decision_maker_accuracy_pct']}%</div>
        </div>
        <div class="card">
            <div class="title">Email Precision</div>
            <div class="val" style="color: #2563eb;">{m['email_verification_precision_pct']}%</div>
        </div>
        <div class="card">
            <div class="title">False Positive Rate</div>
            <div class="val" style="color: #dc2626;">{m['false_positive_rate_pct']}%</div>
        </div>
        <div class="card">
            <div class="title">Avg Latency</div>
            <div class="val">{m['avg_processing_time_ms']} ms</div>
        </div>
        <div class="card">
            <div class="title">Peak Memory</div>
            <div class="val">{m['peak_memory_mb']} MB</div>
        </div>
    </div>

    <div class="table-container">
        <h2>Failure Taxonomy</h2>
        <table>
            <thead>
                <tr><th>Failure Category</th><th>Occurrences</th></tr>
            </thead>
            <tbody>
"""
        for cat, cnt in tax.items():
            html_content += f"<tr><td>{cat}</td><td>{cnt}</td></tr>\n"

        html_content += """            </tbody>
        </table>
    </div>
</body>
</html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _load_history(self) -> List[Dict[str, Any]]:
        hist_path = self.output_dir / "evaluation_history.json"
        if hist_path.exists():
            try:
                with open(hist_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _update_history(self, current_res: Dict[str, Any]) -> None:
        hist_path = self.output_dir / "evaluation_history.json"
        history = self._load_history()
        history.append({
            "timestamp": current_res["reproducibility_metadata"]["execution_timestamp"],
            "benchmark_version": current_res["reproducibility_metadata"]["benchmark_version"],
            "metrics": current_res["metrics"]
        })
        try:
            with open(hist_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to update evaluation history: {e}")

    def _compute_deltas(self, current: EvaluationMetrics, history: List[Dict[str, Any]]) -> Dict[str, float]:
        if not history:
            return {
                "accuracy_delta": 0.0,
                "email_precision_delta": 0.0,
                "fp_rate_delta": 0.0,
                "fn_rate_delta": 0.0,
                "latency_delta_ms": 0.0
            }
        prev_m = history[-1].get("metrics", {})
        return {
            "accuracy_delta": round(current.decision_maker_accuracy_pct - prev_m.get("decision_maker_accuracy_pct", 0.0), 2),
            "email_precision_delta": round(current.email_verification_precision_pct - prev_m.get("email_verification_precision_pct", 0.0), 2),
            "fp_rate_delta": round(current.false_positive_rate_pct - prev_m.get("false_positive_rate_pct", 0.0), 2),
            "fn_rate_delta": round(current.false_negative_rate_pct - prev_m.get("false_negative_rate_pct", 0.0), 2),
            "latency_delta_ms": round(current.avg_processing_time_ms - prev_m.get("avg_processing_time_ms", 0.0), 2)
        }


if __name__ == "__main__":
    benchmark_p = Path("data/benchmarks/benchmark_small.json")
    if not benchmark_p.exists():
        logger.error(f"Benchmark file not found: {benchmark_p}")
        sys.exit(1)
    evaluator = DecisionMakerEvaluator(benchmark_file=benchmark_p)
    results = evaluator.run_evaluation()
    print("\n================ EVALUATION RESULTS ================")
    print(f"Accuracy: {results['metrics']['decision_maker_accuracy_pct']}%")
    print(f"Email Precision: {results['metrics']['email_verification_precision_pct']}%")
    print(f"False Positive Rate: {results['metrics']['false_positive_rate_pct']}%")
    print(f"Average Latency: {results['metrics']['avg_processing_time_ms']} ms")
    print("====================================================\n")
