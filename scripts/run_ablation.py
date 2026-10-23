"""
CLI Script to execute clinical ablation experiments across 5 system variants.
Usage:
    python scripts/run_ablation.py [--cases 10]
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from evaluation.ablation import run_ablation_study


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Clinical System Ablation Study")
    parser.add_argument("--cases", type=int, default=10, help="Number of benchmark cases to test per variant (default: 10)")
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("  CLINIQ MULTI-AGENT DIAGNOSTIC COPILOT — ABLATION EXPERIMENTS (PHASE 3)")
    print("=" * 80)
    print(f"Testing {args.cases} benchmark cases across 5 architectural configurations:\n")
    print("  1. Proposed ClinIQ Multi-Agent (LangGraph + Debate + Multi-Hop + Vision)")
    print("  2. Multi-Agent (No Critic Debate / Single-Pass)")
    print("  3. Baseline Single-Agent RAG (Phase 1 Baseline)")
    print("  4. Multi-Agent (Single-Hop RAG / No Query Planning)")
    print("  5. Dense-Only Retrieval (No BM25 Hybrid)\n")

    result = run_ablation_study(max_cases=args.cases)

    print("\n" + "=" * 95)
    print(f"{'Variant':<35} | {'Top-1':<7} | {'Top-3':<7} | {'Rule-Out':<9} | {'Faithful':<9} | {'Latency':<8}")
    print("-" * 95)
    for v in result.variants:
        print(f"{v.variant_name:<35} | {v.top_1_accuracy:>5.1f}% | {v.top_3_accuracy:>5.1f}% | {v.critical_rule_out_recall:>7.1f}% | {v.faithfulness_score:>7.1f}% | {v.mean_latency_seconds:>6.2f}s")
    print("=" * 95)
    print(f"\n{result.comparative_summary}\n")
    print("Detailed results saved to: data/evaluation/ablation_results.json\n")


if __name__ == "__main__":
    main()
