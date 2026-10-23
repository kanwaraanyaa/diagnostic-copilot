"""
CLI Script to execute automated benchmark evaluation across 50 clinical cases.
Usage:
    python scripts/run_evaluation.py [--cases 10] [--category Respiratory]
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from evaluation.benchmark_runner import run_benchmark_suite


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Clinical Benchmark Evaluation Suite")
    parser.add_argument("--cases", type=int, default=None, help="Maximum number of cases to evaluate (default: all 50)")
    parser.add_argument("--category", type=str, default=None, help="Filter cases by category (e.g., Respiratory, Cardiovascular)")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  CLINIQ MULTI-AGENT DIAGNOSTIC COPILOT — BENCHMARK EVALUATION (PHASE 3)")
    print("=" * 70)
    print(f"Target cases: {args.cases or 'All (50)'} | Category filter: {args.category or 'All categories'}")
    print("Running evaluation suite across multi-agent architecture...\n")

    result = run_benchmark_suite(max_cases=args.cases, category_filter=args.category)

    print("\n" + "=" * 70)
    print(f"  EVALUATION COMPLETE — {result.total_cases_evaluated} CASES")
    print("=" * 70)
    print(f"  Top-1 Diagnostic Accuracy:      {result.top_1_accuracy}%")
    print(f"  Top-3 Differential Inclusion:   {result.top_3_accuracy}%")
    print(f"  Critical Rule-Out Recall:       {result.critical_rule_out_recall}%")
    print(f"  Evidence Faithfulness Score:    {result.mean_faithfulness_score}%")
    print(f"  Average Response Latency:       {result.mean_latency_seconds}s")
    print("=" * 70)
    print("Detailed results persisted to: data/evaluation/benchmark_results.json\n")


if __name__ == "__main__":
    main()
