"""
Benchmark Evaluation Runner — Phase 3.
Evaluates Diagnostic Copilot on the 50-case benchmark dataset.
Computes Top-1 Accuracy, Top-3 Diagnostic Recall, Rule-Out Detection Rate,
Faithfulness, and Latency metrics.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field

from config import get_settings
from evaluation.benchmark_dataset import BenchmarkCase, load_benchmark_cases
from evaluation.hallucination_detector import audit_report_hallucinations
from graph.workflow import run_diagnostic_workflow
from logger import get_logger

log = get_logger(__name__)


class CaseEvaluationDetail(BaseModel):
    """Detailed score for an individual benchmark case."""
    case_id: str
    category: str
    gold_standard_primary: str
    top_1_differential: str
    top_1_match: bool
    top_3_match: bool
    rule_outs_identified: list[str] = Field(default_factory=list)
    rule_out_recall: float = 0.0
    faithfulness_score: float = 100.0
    latency_seconds: float = 0.0
    status: str = "passed"


class BenchmarkRunResult(BaseModel):
    """Summary of benchmark evaluation run."""
    run_timestamp: str
    total_cases_evaluated: int
    top_1_accuracy: float = 0.0      # % (0 to 100)
    top_3_accuracy: float = 0.0      # % (0 to 100)
    critical_rule_out_recall: float = 0.0  # % (0 to 100)
    mean_faithfulness_score: float = 0.0   # % (0 to 100)
    mean_latency_seconds: float = 0.0
    system_version: str = "0.3.0 (Phase 3 Multi-Agent)"
    case_details: list[CaseEvaluationDetail] = Field(default_factory=list)
    summary_markdown: str = ""


def _evaluate_differentials(
    generated_differentials: list[dict[str, Any]],
    gold_primary: str,
    critical_rule_outs: list[str],
) -> tuple[bool, bool, list[str], float, str]:
    """Scores generated differentials against gold-standard targets."""
    if not generated_differentials:
        return False, False, [], 0.0, "None"

    gold_primary_clean = gold_primary.lower()
    top_1_cond = generated_differentials[0].get("condition", "None")

    def _matches(cond_name: str, target: str) -> bool:
        c_words = set(cond_name.lower().replace("-", " ").split())
        t_words = set(target.lower().replace("-", " ").split())
        overlap = c_words.intersection(t_words)
        return len(overlap) >= 1 and any(len(w) > 3 for w in overlap)

    top_1_match = _matches(top_1_cond, gold_primary_clean)

    top_3_conds = [d.get("condition", "") for d in generated_differentials[:3]]
    top_3_match = any(_matches(c, gold_primary_clean) for c in top_3_conds)

    # Check rule-out detection
    all_conds = [d.get("condition", "") for d in generated_differentials]
    identified_rule_outs = []
    for ro in critical_rule_outs:
        if any(_matches(c, ro.lower()) for c in all_conds):
            identified_rule_outs.append(ro)

    rule_out_recall = (
        round(len(identified_rule_outs) / len(critical_rule_outs) * 100.0, 1)
        if critical_rule_outs
        else 100.0
    )

    return top_1_match, top_3_match, identified_rule_outs, rule_out_recall, top_1_cond


def run_benchmark_suite(
    max_cases: Optional[int] = None,
    category_filter: Optional[str] = None,
) -> BenchmarkRunResult:
    """
    Executes automated benchmark evaluation across benchmark cases.
    """
    all_cases = load_benchmark_cases()
    if category_filter:
        all_cases = [c for c in all_cases if c.category.lower() == category_filter.lower()]
    if max_cases:
        all_cases = all_cases[:max_cases]

    log.info("starting_benchmark_suite", count=len(all_cases))
    case_details: list[CaseEvaluationDetail] = []
    total_time = 0.0

    for bcase in all_cases:
        t0 = time.time()
        patient_dict = {
            "case_id": bcase.case_id,
            "patient": bcase.patient,
            "symptoms": bcase.symptoms,
            "history": bcase.history,
            "labs": bcase.labs,
            "clinical_notes": bcase.clinical_notes,
        }

        # Run multi-agent diagnostic workflow
        try:
            workflow_state = run_diagnostic_workflow(patient_case=patient_dict)
            report = workflow_state.get("final_report", {})
            diffs = report.get("differential_considerations", [])
            citations = report.get("evidence_citations", [])

            top_1_m, top_3_m, id_ros, ro_rec, top_1_c = _evaluate_differentials(
                generated_differentials=diffs,
                gold_primary=bcase.gold_standard_primary,
                critical_rule_outs=bcase.critical_rule_outs,
            )

            # Audit faithfulness
            audit = audit_report_hallucinations(
                patient_case=patient_dict,
                report=report,
                citations=citations,
            )
            latency = round(time.time() - t0, 2)
            total_time += latency

            case_details.append(
                CaseEvaluationDetail(
                    case_id=bcase.case_id,
                    category=bcase.category,
                    gold_standard_primary=bcase.gold_standard_primary,
                    top_1_differential=top_1_c,
                    top_1_match=top_1_m,
                    top_3_match=top_3_m,
                    rule_outs_identified=id_ros,
                    rule_out_recall=ro_rec,
                    faithfulness_score=audit.faithfulness_score,
                    latency_seconds=latency,
                    status="passed",
                )
            )
        except Exception as e:
            log.error("benchmark_case_failed", case_id=bcase.case_id, error=str(e))
            latency = round(time.time() - t0, 2)
            case_details.append(
                CaseEvaluationDetail(
                    case_id=bcase.case_id,
                    category=bcase.category,
                    gold_standard_primary=bcase.gold_standard_primary,
                    top_1_differential="Evaluation Error",
                    top_1_match=False,
                    top_3_match=False,
                    rule_outs_identified=[],
                    rule_out_recall=0.0,
                    faithfulness_score=0.0,
                    latency_seconds=latency,
                    status=f"error: {e}",
                )
            )

    # Compute aggregate metrics
    n = len(case_details)
    if n == 0:
        return BenchmarkRunResult(
            run_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_cases_evaluated=0,
        )

    top_1_acc = round(sum(1 for c in case_details if c.top_1_match) / n * 100.0, 1)
    top_3_acc = round(sum(1 for c in case_details if c.top_3_match) / n * 100.0, 1)
    mean_ro_rec = round(sum(c.rule_out_recall for c in case_details) / n, 1)
    mean_faith = round(sum(c.faithfulness_score for c in case_details) / n, 1)
    mean_lat = round(total_time / n, 2)

    summary_md = (
        f"### Benchmark Evaluation Summary ({n} Cases Evaluated)\n\n"
        f"- **Top-1 Diagnostic Accuracy**: **{top_1_acc}%**\n"
        f"- **Top-3 Differential Inclusion**: **{top_3_acc}%**\n"
        f"- **Critical Rule-Out Recall**: **{mean_ro_rec}%**\n"
        f"- **Mean Evidence Faithfulness**: **{mean_faith}%**\n"
        f"- **Average Case Latency**: **{mean_lat}s**\n"
    )

    result = BenchmarkRunResult(
        run_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        total_cases_evaluated=n,
        top_1_accuracy=top_1_acc,
        top_3_accuracy=top_3_acc,
        critical_rule_out_recall=mean_ro_rec,
        mean_faithfulness_score=mean_faith,
        mean_latency_seconds=mean_lat,
        case_details=case_details,
        summary_markdown=summary_md,
    )

    # Save results to data/evaluation
    try:
        eval_dir = Path("data/evaluation")
        eval_dir.mkdir(parents=True, exist_ok=True)
        with open(eval_dir / "benchmark_results.json", "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
    except Exception as e:
        log.warning("failed_saving_benchmark_results", error=str(e))

    return result
